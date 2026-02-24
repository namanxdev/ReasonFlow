"""API tests for email endpoints."""

from __future__ import annotations

import uuid

import pytest

from app.models.email import Email, EmailStatus, EmailClassification


@pytest.mark.asyncio
class TestEmailEndpoints:
    """Test email API endpoints."""

    async def test_list_emails_empty(self, auth_client, test_user, db_session):
        """Test listing emails when none exist."""
        response = await auth_client.get("/api/v1/emails")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_emails_with_data(self, auth_client, test_user, db_session):
        """Test listing emails with data."""
        # Create test emails
        emails = [
            Email(
                id=uuid.uuid4(),
                user_id=test_user.id,
                gmail_id=f"gmail_{i}",
                subject=f"Test Subject {i}",
                body="Test body",
                sender="sender@example.com",
                status=EmailStatus.PENDING,
            )
            for i in range(3)
        ]
        for email in emails:
            db_session.add(email)
        await db_session.commit()

        response = await auth_client.get("/api/v1/emails")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3

    async def test_get_email_by_id(self, auth_client, test_user, db_session):
        """Test getting a single email by ID."""
        email = Email(
            id=uuid.uuid4(),
            user_id=test_user.id,
            gmail_id="test_gmail_id",
            subject="Test Subject",
            body="Test body",
            sender="sender@example.com",
            status=EmailStatus.PENDING,
            classification=EmailClassification.INQUIRY,
            confidence=0.95,
        )
        db_session.add(email)
        await db_session.commit()

        response = await auth_client.get(f"/api/v1/emails/{email.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(email.id)
        assert data["subject"] == "Test Subject"
        assert data["classification"] == "inquiry"

    async def test_get_email_not_found(self, auth_client):
        """Test getting non-existent email."""
        fake_id = uuid.uuid4()
        response = await auth_client.get(f"/api/v1/emails/{fake_id}")
        assert response.status_code == 404

    async def test_get_email_wrong_user(self, auth_client, db_session):
        """Test getting email belonging to another user."""
        from app.models.user import User
        from app.core.security import hash_password
        
        # Create another user
        other_user = User(
            email="other@example.com",
            hashed_password=hash_password("password123"),
        )
        db_session.add(other_user)
        await db_session.flush()
        
        # Create email for other user
        email = Email(
            id=uuid.uuid4(),
            user_id=other_user.id,
            gmail_id="other_gmail_id",
            subject="Other User Email",
            body="Test body",
            sender="sender@example.com",
            status=EmailStatus.PENDING,
        )
        db_session.add(email)
        await db_session.commit()

        # Try to access as authenticated user
        response = await auth_client.get(f"/api/v1/emails/{email.id}")
        assert response.status_code == 404  # Should not reveal existence

    async def test_email_pagination(self, auth_client, test_user, db_session):
        """Test email pagination."""
        # Create 5 emails
        for i in range(5):
            email = Email(
                id=uuid.uuid4(),
                user_id=test_user.id,
                gmail_id=f"gmail_{i}",
                subject=f"Email {i}",
                body="Test body",
                sender="sender@example.com",
                status=EmailStatus.PENDING,
            )
            db_session.add(email)
        await db_session.commit()

        # Get page 1 with size 2
        response = await auth_client.get("/api/v1/emails?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["per_page"] == 2

        # Get page 2 with size 2
        response = await auth_client.get("/api/v1/emails?page=2&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 2

    async def test_email_status_filter(self, auth_client, test_user, db_session):
        """Test filtering emails by status."""
        # Create emails with different statuses
        email1 = Email(
            id=uuid.uuid4(),
            user_id=test_user.id,
            gmail_id="gmail_1",
            subject="Pending Email",
            body="Test body",
            sender="sender@example.com",
            status=EmailStatus.PENDING,
        )
        email2 = Email(
            id=uuid.uuid4(),
            user_id=test_user.id,
            gmail_id="gmail_2",
            subject="Sent Email",
            body="Test body",
            sender="sender@example.com",
            status=EmailStatus.SENT,
        )
        db_session.add(email1)
        db_session.add(email2)
        await db_session.commit()

        # Filter by pending status
        response = await auth_client.get("/api/v1/emails?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["subject"] == "Pending Email"

    async def test_email_search(self, auth_client, test_user, db_session):
        """Test searching emails."""
        # Create emails
        email1 = Email(
            id=uuid.uuid4(),
            user_id=test_user.id,
            gmail_id="gmail_1",
            subject="Important Meeting",
            body="Test body",
            sender="boss@example.com",
            status=EmailStatus.PENDING,
        )
        email2 = Email(
            id=uuid.uuid4(),
            user_id=test_user.id,
            gmail_id="gmail_2",
            subject="Lunch plans",
            body="Test body",
            sender="friend@example.com",
            status=EmailStatus.PENDING,
        )
        db_session.add(email1)
        db_session.add(email2)
        await db_session.commit()

        # Search for "meeting"
        response = await auth_client.get("/api/v1/emails?q=meeting")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "meeting" in data["items"][0]["subject"].lower()
