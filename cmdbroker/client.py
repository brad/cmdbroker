import argparse
import asyncio
import select
import ssl
import sys

from .message import Message


class Client:
    def __init__(self, params: argparse.Namespace):
        self.command = params.command
        self.address = params.address
        self.port = params.port
        self.broker_cert = params.broker_cert

    async def run(self):
        payload = {
            "method": "process",
            "parameters": {
                "command": self.command,
            },
        }

        # Add stdin parameter if there's something in stdin
        if select.select([sys.stdin], [], [], 0.0)[0]:
            payload["stdin"] = await asyncio.to_thread(sys.stdin.read)

        # Forward request to server and get response
        response = await self.relay_to_server(Message.build(payload))

        # Output the response to stdout
        response.write(sys.stdout.buffer)

    async def relay_to_server(self, request):
        # Create an SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.load_verify_locations(self.broker_cert)

        reader, writer = await asyncio.open_connection(self.address, self.port, ssl=ssl_context)

        await request.async_write(writer)

        # Receive response from server
        response = await Message.async_read(reader)

        writer.close()
        await writer.wait_closed()

        return response
