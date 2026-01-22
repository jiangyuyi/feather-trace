import threading
import asyncio
import time
import logging
from fastapi import FastAPI, WebSocket
import uvicorn

app = FastAPI()
logs = []

# Mimic TaskManager
def background_worker():
    print("Worker started")
    for i in range(5):
        time.sleep(1)
        logs.append(f"Log {i}")
    print("Worker finished")

@app.post("/start")
async def start():
    t = threading.Thread(target=background_worker, daemon=True)
    t.start()
    return {"status": "started"}

@app.post("/reset")
async def reset():
    print("Resetting...")
    time.sleep(2) # Blocking IO simulation
    print("Reset done")
    return {"status": "reset"}

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_text("ping")
            await asyncio.sleep(0.5)
    except Exception as e:
        print(f"WS Exception: {e}")

if __name__ == "__main__":
    # Simulate run
    config = uvicorn.Config(app, port=8001, log_level="info")
    server = uvicorn.Server(config)
    server.run()
