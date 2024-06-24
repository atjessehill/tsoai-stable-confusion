from uuid import uuid4


class Client:
    def __init__(self, conn) -> None:
        self.uid = uuid4()
        self.conn = conn

    def __hash__(self) -> int:
        return self.uid.int
