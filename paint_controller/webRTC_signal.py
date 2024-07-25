import asyncio
from aiortc.contrib.signaling import BYE

class TcpSocketSignalingServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connections = []

    async def handle_client(self, reader, writer):
        self.connections.append((reader, writer))
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
                message = data.decode()
                print(f"Received message: {message}")
                if message == BYE:
                    break
                for r, w in self.connections:
                    if w is not writer:
                        w.write(data)
                        await w.drain()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            self.connections.remove((reader, writer))

    async def start_server(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        async with server:
            print(f"Server started on {self.host}:{self.port}")
            await server.serve_forever()

if __name__ == "__main__":
    host = "192.168.11.199"  # Replace with your server's IP address
    port = 1234
    signaling_server = TcpSocketSignalingServer(host, port)
    asyncio.run(signaling_server.start_server())
