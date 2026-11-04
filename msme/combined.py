# =============================================================================
# FILE HEADER
# file    : msme/combined.py
# role    : Entrypoint — one external port for receive + filter
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : authenticate every request (T-047), route one ASGI app on :8899 to the receive
#           dashboard or the filter service, preserve legacy API paths and serve a combined /health.
# pages   : all static pages from dashboard.py and filter_service.py
# calls   : dashboard.app, filter_service.app, db.init_db, receive_queue.start, auth.AuthGate
# called  : run.py (uvicorn `msme.combined:app`)
# amend   : path table is the contract; add a new filter path here. Filter pages keep root-relative
#           URLs, so `/` stays receive and `/filter.html` is the filter home.
#           Test: curl -s localhost:8899/health; curl -s localhost:8899/filter.html
# =============================================================================
"""One ASGI entrypoint: receive at the root, filter at its existing root paths.

The filter pages use root-relative API paths (`/config.json`, `/verdicts`, ...),
so dispatching by path avoids rewriting every filter page. Both FastAPI apps
run in the same process and port.
"""
from msme import auth, db
from msme.filtering import filter_service
from msme.receive import dashboard, receive_queue

# Filter paths that must not fall through to the receive dashboard.
_FILTER_EXACT = {
    "/filter", "/filter.html", "/filter-upload", "/filters.json",
    "/verdicts", "/verdicts.html", "/workflow.html", "/workflow.json",
    "/logs.html", "/logs.json", "/config.json", "/clear",
    "/config-versions",
    "/lab.html", "/testfilter.html", "/reportmanager.html", "/archived",
}
_FILTER_PREFIXES = ("/lab/", "/testfilter/", "/report/", "/archived/", "/config-versions/")

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
                        auth.startup_cleanup()
                        auth.ensure_bootstrap_admin()
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


app = auth.AuthGate(CombinedApp())
