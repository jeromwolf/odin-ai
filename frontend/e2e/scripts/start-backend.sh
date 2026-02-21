#!/bin/bash
cd /Users/blockmeta/Desktop/workspace/odin-ai
export DATABASE_URL="postgresql://blockmeta@localhost:5432/odin_db"
export SECRET_KEY="${SECRET_KEY:-odin-ai-e2e-test-secret-key-2025}"

if [ -f "venv/bin/python3" ]; then
  cd backend && ../venv/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 9000
elif [ -f "venv_test/bin/python3" ]; then
  cd backend && ../venv_test/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 9000
else
  cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port 9000
fi
