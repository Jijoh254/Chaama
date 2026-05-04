"""M-Pesa webhooks - placeholders for Phase 1, will be implemented in Phase 4-5."""
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("/stk-callback")
async def stk_callback(request: Request):
    """Handle M-Pesa STK Push callback (Phase 4)."""
    return JSONResponse(content={"ResultCode": 0, "ResultDesc": "Accepted"})


@router.post("/b2c-result")
async def b2c_result(request: Request):
    """Handle M-Pesa B2C result callback (Phase 5)."""
    return JSONResponse(content={"ResultCode": 0, "ResultDesc": "Accepted"})


@router.post("/b2c-timeout")
async def b2c_timeout(request: Request):
    """Handle M-Pesa B2C timeout callback (Phase 5)."""
    return JSONResponse(content={"ResultCode": 0, "ResultDesc": "Accepted"})
