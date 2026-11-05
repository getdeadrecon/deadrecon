#!/usr/bin/env python3
"""
DeadRecon — Production launch script

Author:  the-clipper
AI:      Claude (Anthropic)
License: MIT — see LICENSE
"""
import os

if __name__ == "__main__":
    from deadrecon.core.config import config
    from deadrecon.core.database import init_db
    from deadrecon.web.app import create_app, socketio

    init_db()
    app = create_app()

    host = os.getenv("DEADRECON_HOST", config.get("server", "host", default="127.0.0.1"))
    port = int(os.getenv("DEADRECON_PORT", config.get("server", "port", default=5000)))
    debug = os.getenv("DEADRECON_DEBUG", str(config.get("server", "debug", default=False))).lower() == "true"

    print(f"\n>> DeadRecon // OSINT Framework — v{__import__('deadrecon').__version__}")
    print(f"   Grid online: http://{host}:{port}\n")

    socketio.run(app, host=host, port=port, debug=debug, use_reloader=False, allow_unsafe_werkzeug=True)
