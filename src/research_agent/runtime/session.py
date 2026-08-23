import hmac
import secrets

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def install_api_token_guard(app: FastAPI, expected_token: str | None) -> None:
    if expected_token is None:
        return
    if expected_token == "":
        raise ValueError("expected_token must be non-empty or None")

    @app.middleware("http")
    async def api_token_guard(request: Request, call_next):
        if request.url.path.startswith("/api/"):
            supplied_token = request.headers.get("X-PaleoRigor-Token", "")
            if not hmac.compare_digest(supplied_token, expected_token):
                return JSONResponse(
                    status_code=401,
                    content={"detail": {"error": "invalid_session"}},
                )
        return await call_next(request)
