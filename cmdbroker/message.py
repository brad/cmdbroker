import json
import struct
from asyncio import StreamReader
from typing import Any, Dict


class Message:
    """Represents a brokered message."""

    def __init__(self) -> None:
        self.text: bytes = b""
        self.text_length_bytes: bytes = b""

    @staticmethod
    def build(json_data: Dict[str, Any]) -> "Message":
        message = Message()
        message.text = json.dumps(json_data).encode("utf-8")
        message.text_length_bytes = struct.pack("@I", len(message.text))

        return message

    def unpack_length(self) -> int:
        """Unpack the message length from the first 4 bytes."""
        return struct.unpack("@I", self.text_length_bytes)[0]

    def output(self) -> bytes:
        return self.text_length_bytes + self.text

    def json(self) -> Dict[str, Any]:
        return json.loads(self.text.decode("utf-8"))

    @staticmethod
    async def async_read(reader: StreamReader) -> "Message":
        message = Message()
        # Read the message length/text
        message.text_length_bytes = await reader.read(4)
        message.text = await reader.read(message.unpack_length())

        return message

    def write(self, writer) -> None:
        writer.write(self.output())

    async def async_write(self, writer) -> None:
        self.write(writer)
        await writer.drain()
