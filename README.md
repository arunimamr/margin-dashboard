# Margin Dashboard

Margin Dashboard

## Basic Backend Setup

### macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python run.py
```

### Windows

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
python run.py
```

The API runs on:

http://127.0.0.1:8000

Health check:

http://127.0.0.1:8000/api/health
