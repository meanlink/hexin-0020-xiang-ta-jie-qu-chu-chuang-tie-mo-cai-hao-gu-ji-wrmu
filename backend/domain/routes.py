from fastapi import APIRouter

from domain import rolls_api, sheet_api, windows_api

router = APIRouter()
router.include_router(windows_api.router)
router.include_router(rolls_api.router)
router.include_router(sheet_api.router)
