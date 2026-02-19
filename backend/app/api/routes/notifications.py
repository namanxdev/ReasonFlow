"""WebSocket notifications endpoint."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from app.core.config import settings
from app.core.events import subscribe_events

logger = logging.getLogger(__name__)

router = APIRouter()

# WebSocket close codes
WS_CLOSE_NORMAL = 1000
WS_CLOSE_INVALID_TOKEN = 4002
WS_CLOSE_MISSING_TOKEN = 4001
WS_CLOSE_SERVER_ERROR = 4000


@router.websocket("/ws")
async def notifications_websocket(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time notifications.

    Protocol:
        1. Client connects to ws://host/api/v1/notifications/ws
        2. Client must send auth message as first message: {"token": "<jwt_token>"}
        3. Server responds with: {"type": "connected", "user_id": "..."}
        4. Server streams events as JSON with type, user_id, data, timestamp
        5. Connection remains open until client disconnects or token expires

    Authentication:
        - First message must contain valid JWT token
        - Invalid or missing token results in immediate connection close
        - Token is verified using JWT_SECRET_KEY and JWT_ALGORITHM from config

    Events:
        - EMAIL_RECEIVED: New email arrived
        - EMAIL_CLASSIFIED: Email classification completed
        - DRAFT_READY: Draft response generated
        - DRAFT_APPROVED: Draft approved by user
        - DRAFT_REJECTED: Draft rejected by user
        - EMAIL_SENT: Email sent successfully
        - BATCH_PROGRESS: Batch operation progress update
        - BATCH_COMPLETE: Batch operation completed
    """
    await websocket.accept()
    user_id: UUID | None = None

    try:
        # First message must be authentication
        auth_msg = await websocket.receive_json()
        token = auth_msg.get("token")

        if not token:
            logger.warning("WebSocket connection rejected: missing token")
            await websocket.close(
                code=WS_CLOSE_MISSING_TOKEN, reason="Missing authentication token"
            )
            return

        # Verify JWT token
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            user_id_str = payload.get("sub")
            if not user_id_str:
                raise ValueError("Missing subject claim")
            user_id = UUID(user_id_str)
        except (JWTError, ValueError) as exc:
            logger.warning("WebSocket connection rejected: invalid token - %s", exc)
            await websocket.close(
                code=WS_CLOSE_INVALID_TOKEN, reason="Invalid authentication token"
            )
            return

        # Send connected confirmation
        await websocket.send_json({"type": "connected", "user_id": str(user_id)})
        logger.info("WebSocket connected for user: %s", user_id)

        # Subscribe to events and forward to client
        async for event in subscribe_events(user_id):
            try:
                await websocket.send_json(event)
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected for user: %s", user_id)
                break
            except RuntimeError as exc:
                # Connection might be closed
                logger.debug("WebSocket send error for user %s: %s", user_id, exc)
                break

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for user: %s", user_id)
    except Exception as exc:
        logger.exception("WebSocket error for user %s: %s", user_id, exc)
        if user_id:
            try:
                await websocket.close(code=WS_CLOSE_SERVER_ERROR, reason="Internal server error")
            except RuntimeError:
                # Connection already closed
                pass
