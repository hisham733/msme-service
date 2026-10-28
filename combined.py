# =============================================================================
# FILE HEADER
# file    : combined.py
# role    : Entrypoint — one external port for receive + filter
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : route one ASGI app on :8899 to the receive dashboard or the filter service;
#           preserve legacy receive API paths and serve a combined /health.
# pages   : all static pages from dashboard.py and filter_service.py
# calls   : dashboard.app, filter_service.app, db.init_db, receive_queue.start
# called  : run.py (uvicorn `combined:app`)
# amend   : path table is the contract; add a new filter path here. Filter pages keep root-relative
#           URLs, so `/` stays receive and `/filter.html` is the filter home.
#           Test: curl -s localhost:8899/health; curl -s localhost:8899/filter.html
# =============================================================================
"""One ASGI entrypoint: receive at the root, filter at its existing root paths.

The filter pages use root-relative API paths (`/config.json`, `/verdicts`, ...),
so dispatching by path avoids rewriting every filter page. Both FastAPI apps
run in the same process and port.
"""
import db
import dashboard
import filter_service
import receive_queue

# Filter paths that must not fall through to the receive dashboard.
_FILTER_EXACT = {
    "/filter", "/filter.html", "/filter-upload", "/filters.json",
    "/verdicts", "/verdicts.html", "/workflow.html", "/workflow.json",
    "/logs.html", "/logs.json", "/config.json", "/clear",
    "/lab.html", "/testfilter.html", "/reportmanager.html", "/archived",
}
_FILTER_PREFIXES = ("/lab/", "/testfilter/", "/report/", "/archived/")

# Legacy :8898 receive API paths, rewritten onto the dashboard's /api aliases.
_LEGACY = {
    "/run": "/api/run",
    "/run-all": "/api/run-all",
    "/emails": "/api/emails",
    "/logs": "/api/logs",
    "/config": "/api/config",
}


def _target(path):
    if path == "/health":
        return dashboard.app, "/api/health"
    if path in _LEGACY:
        return dashboard.app, _LEGACY[path]
    if path in _FILTER_EXACT or path.startswith(_FILTER_PREFIXES):
        return filter_service.app, path
    return dashboard.app, path


class CombinedApp:
    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    try:
                        db.init_db()
                        receive_queue.start()
                        await send({"type": "lifespan.startup.complete"})
                    except Exception as e:
                        await send({"type": "lifespan.startup.failed", "message": str(e)})
                elif message["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        if scope["type"] not in ("http", "websocket"):
            return
        app, path = _target(scope.get("path", "/"))
        if path != scope.get("path", "/"):
            scope = dict(scope)
            scope["path"] = path
            scope["raw_path"] = path.encode()
        await app(scope, receive, send)


app = CombinedApp()
