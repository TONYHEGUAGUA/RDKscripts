import websockets

async def test_handler(websocket, path):  # 正确包含path
    while True:
        await websocket.send("test")
        await asyncio.sleep(1)

async def main():
    async with websockets.serve(test_handler, "localhost", 8765):
        await asyncio.Future()

asyncio.run(main())