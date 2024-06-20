import random
import asyncio
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
    - 

"""

LATENCY_COMP = 0.0


@app.websocket("/feed")
async def feed(request: Request, ws: Websocket):
    categories = ['A', 'B', 'C', 'D']

    order = 4  # was 4
    noisePar = 0.2  # was 0.18 # determines SD
    learnRatio = 0.1  # was 0.1
    minQuantizationProb = 0.7  # determines threshold probability for which item will be put in category
    maxSD = 2  # 2.5 worked well

    alphabet = set([])  ## Initialize empty alphabet
    # onsettimes = np.array([0,1,,3,3.55,4,5,6,7])
    # iois = np.array([1,2,3,1,2.1,2.99,1,2,3,1,2,3])
    ppm = PPMC(order=order, alphabet=alphabet, modelSD=noisePar, maxSD=maxSD, learnRatio=learnRatio)

    start_time = time.time()

    async def send_messages():
        count = 0
        while True:
            count += 1

            # randnum = random.randrange(100000)
            # if randnum == 10:  # if there is an event... send it

            category = categories[random.randrange(4)]
            velocity = random.randrange(128)
            continuous = random.random()

            interval = random.randrange(4) + random.random()

            resp = [category, velocity, interval, continuous]

            await ws.send(str(resp))

            await asyncio.sleep(1)

    async def send_event(_ws, interval, category, velocity):
        # velocity = round(velocity*127)
        interval = max(0, interval - LATENCY_COMP)
        resp = str([str(category), float(velocity), interval, random.random()])
        print(f"Waiting for {interval}")
        await asyncio.sleep(interval)
        print(f"Sending response {resp}")
        await _ws.send(resp)

    async def receive_messages():
        last_time = None
        while True:
            try:
                resp = {}
                data = await ws.recv()
                print(f"======= NEW EVENT =======")
                data = eval(data)
                event_time = data['clientTime']
                resp['eventTime'] = event_time

                if last_time is not None:
                    interval = (event_time - last_time) / 1000
                    print(f"INTERVAL: {interval}")
                    pdf, alphabet, curAlphabetIntervals = ppm.fit(interval, verbose=True)

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
                    print(predicted_events)

                    await ws.send(str(resp))

                else:
                    print("First key press detected")
                last_time = event_time
            except Exception as e:
                raise e
                print(f"Error receiving message: {e}")
                break

    # send_task = asyncio.create_task(send_messages())
    receive_task = asyncio.create_task(receive_messages())
    # await asyncio.gather(receive_task, send_task)
    await asyncio.gather(receive_task)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9998)
