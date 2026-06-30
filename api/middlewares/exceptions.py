from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError


async def sqlalchemy_integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": "Contrainte d'intégrité violée", "errors": str(exc.orig)},
    )


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )
