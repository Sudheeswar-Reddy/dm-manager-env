"""
server/app.py — Entry point for openenv multi-mode deployment.
Wraps the root app.py for openenv serve / uv run compatibility.
"""
import os
import sys
import uvicorn

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402


def main():
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
