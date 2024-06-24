import asyncio

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
