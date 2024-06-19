import random
import asyncio

from sanic import Request, Websocket, Sanic

# from .model import FakeEventGenerator

app = Sanic("stable_confusion")


@app.websocket("/feed")
async def feed(request: Request, ws: Websocket):

    categories = ['A', 'B', 'C', 'D']

    async def send_messages():
        count = 0
        while True:
            count += 1

            randnum = random.randrange(100000)
            if randnum == 10:  # if there is an event... send it

                category = categories[random.randrange(4)]
                velocity = random.randrange(128)
                continuous = random.random()

                interval = random.randrange(4) + random.random()

                resp = [category, velocity, interval, continuous]

                await ws.send(str(resp))

            await asyncio.sleep(0.0000001)

    async def receive_messages():
        while True:
            try:
                data = await ws.recv()
                print(data)
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    send_task = asyncio.create_task(send_messages())
    receive_task = asyncio.create_task(receive_messages())
    await asyncio.gather(receive_task, send_task)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9999)
