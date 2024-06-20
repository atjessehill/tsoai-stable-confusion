import random
import asyncio
from uuid import UUID, uuid4
import time
import numpy as np

from sanic import Request, Websocket, Sanic

from model import PPMC

app = Sanic("stable_confusion")

"""
todo:
    - sonification
    - multiple inputs (make this model) 
    - autonomous
    - realtime output 

musical ideas:
    - everyone goes in a turn

"""

LATENCY_COMP = 0.0

order = 4  # was 4
noisePar = 0.2  # was 0.18 # determines SD
learnRatio = 0.1  # was 0.1
minQuantizationProb = 0.7  # determines threshold probability for which item will be put in category
maxSD = 2  # 2.5 worked well

alphabet = set([])  ## Initialize empty alphabet

@app.after_server_start
async def setup_chatroom(app: Sanic):
    app.ctx.session = Session()
    app.ctx.ppm = PPMC(order=order, alphabet=alphabet, modelSD=noisePar, maxSD=maxSD, learnRatio=learnRatio)
    app.ctx.last_time = None

@app.websocket("/feed")
async def feed(request: Request, ws: Websocket):


    async def receive_messages():
        count = 0
        while True:
            try:
                resp = {}
                update_last_time = True
                data = await ws.recv()
                data = eval(data)
                event_time = data['clientTime']
                resp['eventTime'] = event_time

                if app.ctx.last_time is not None:
                    print(app.ctx.last_time, event_time, event_time-app.ctx.last_time)
                    interval = (event_time - app.ctx.last_time) / 1000

                    if interval < 0.10:
                        update_last_time = False
                    else:
                        count += 1
                        print(f"======= NEW EVENT {count} ======= {id(app.ctx.ppm)}")
                        pdf, alphabet, curAlphabetIntervals = app.ctx.ppm.fit(interval, verbose=True)

                        placeholder_rand_value = random.random()

                        predicted_events = [
                            [
                                str(alphabet[interval]),
                                float(curAlphabetIntervals[interval] * 1000),  # 0.015151 <- seconds
                                float(pdf[interval]),  # <- velocity/probability
                                placeholder_rand_value
                            ]
                            for interval in range(len(alphabet))
                        ]
                        resp['predictedEvents'] = predicted_events

                        await request.app.ctx.session.push(str(resp))

                else:
                    print("First key press detected")

                if update_last_time:
                    app.ctx.last_time = event_time
            except Exception as e:
                raise e
                print(f"Error receiving message: {e}")
                break

    client = Client(ws)
    request.app.ctx.session.add_client(client)

    receive_task = asyncio.create_task(receive_messages())
    await asyncio.gather(receive_task)


class Client:
    def __init__(self, conn) -> None:
        self.uid = uuid4()
        self.conn = conn

    def __hash__(self) -> int:
        return self.uid.int


class Session:

    def __init__(self):
        self.clients = set()

    def add_client(self, client):
        print("Registering client...")
        self.clients.add(client)

    def remove(self, client):
        print("removing client...")
        self.clients.remove(client)

    async def push(self, message: str):
        await asyncio.gather(*[client.conn.send(message) for client in self.clients])




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9998)
