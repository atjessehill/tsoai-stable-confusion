"""
2-way communication demo between two OSC server/clients

"""

import argparse
import random
import time
import math
import threading

from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server


class TwoWayServer:

    def __init__(self, name, ip, port, client_port):
        self.name = name

        dispatcher = self.get_dispatcher()
        self.server = osc_server.ThreadingOSCUDPServer(
            (ip, port), dispatcher)

        self.client = udp_client.SimpleUDPClient(ip, client_port)

    def get_dispatcher(self):
        dispatcher = Dispatcher()
        dispatcher.map("/recv", self.handler)

        return dispatcher

    def start(self):
        thread = threading.Thread(target=self.server.serve_forever)
        thread.start()

    def handler(self, *args):

        print(f"{self.name}", args)

    def send_message(self):
        self.client.send_message("/recv", random.random())



if __name__ == "__main__":

    s1 = TwoWayServer("Serv1", "0.0.0.0", 8080, 8081)
    s2 = TwoWayServer("Serv2", "0.0.0.0", 8082, 8080)
    s1.start()
    s2.start()

    while True:

        # server = [s1, s2][bool(random.getrandbits(1))]  # choose a random server
        #
        # s2.send_message()

        time.sleep(1)
