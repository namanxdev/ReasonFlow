.PHONY: dev backend frontend install clean

# Paths
VENV_PYTHON := backend/venv/Scripts/python
BACKEND_DIR := backend
FRONTEND_DIR := frontend

# ─── Main target: start both services concurrently ────────────────────────────
dev:
	@echo "Starting backend and frontend..."
	@(cd $(BACKEND_DIR) && ../$(VENV_PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &)
	@(cd $(FRONTEND_DIR) && npm run dev)

# ─── Individual service targets ───────────────────────────────────────────────
backend:
	@echo "Starting backend..."
	cd $(BACKEND_DIR) && ../$(VENV_PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	@echo "Starting frontend..."
	cd $(FRONTEND_DIR) && npm run dev

# ─── Install all dependencies ─────────────────────────────────────────────────
install:
	@echo "Installing backend dependencies..."
	$(VENV_PYTHON) -m pip install -r $(BACKEND_DIR)/requirements.txt
	@echo "Installing frontend dependencies..."
	cd $(FRONTEND_DIR) && npm install

# ─── Kill running dev processes ───────────────────────────────────────────────
clean:
	@echo "Stopping dev processes..."
	-taskkill //F //IM uvicorn.exe 2>/dev/null || true
	-taskkill //F //IM node.exe 2>/dev/null || true
	@echo "Done."
