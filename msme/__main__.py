"""Launcher — `python -m msme` (same behaviour as `python run.py`)."""
import uvicorn

from msme import config
from msme.receive import scheduler


def main() -> None:
    # Auto-poll scheduler (off unless ENABLE_AUTO=true). Must be single worker.
    scheduler.start()
    server = uvicorn.Server(
        uvicorn.Config(
            "msme.combined:app",
            host=config.API_HOST,
            port=config.DASH_PORT,
            log_level="info",
        )
    )
    server.run()


if __name__ == "__main__":
    main()
