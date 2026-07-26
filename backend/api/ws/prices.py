"""WebSocket endpoint for real-time price streaming.

Phase 5 implementation — currently a placeholder.
When active, streams tick-by-tick prices from exchange WebSocket feeds.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/prices/{symbol}")
async def price_stream(websocket: WebSocket, symbol: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # TODO: Phase 5 — subscribe to exchange WebSocket for symbol
            # and stream parsed tick data
            await websocket.send_json({
                "symbol": symbol,
                "type": "heartbeat",
                "timestamp": None,
            })
    except WebSocketDisconnect:
        pass
