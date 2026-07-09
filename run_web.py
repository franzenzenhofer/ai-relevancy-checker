#!/usr/bin/env python3
"""Launch the AI Relevancy Checker web app."""
import sys
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn


def main():
    host = "0.0.0.0"
    port = 8080

    for i, arg in enumerate(sys.argv[1:], 1):
        if arg in ("--port", "-p") and i < len(sys.argv) - 1:
            port = int(sys.argv[i + 1])
        elif arg in ("--host",) and i < len(sys.argv) - 1:
            host = sys.argv[i + 1]

    print("=" * 50)
    print("  AI Relevancy Checker - Web App")
    print(f"  http://localhost:{port}")
    print("=" * 50)

    uvicorn.run(
        "web.server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
