from unittest.mock import AsyncMock, MagicMock

import pytest

from cmdbroker.message import Message


def test_build(sample_message):
    message = Message.build(sample_message)

    assert (
        message.text
        == b'{"method": "process", "parameters": {"param1": "value1", "param2": "value2"}}'
    )
    assert message.unpack_length() == len(message.text)


def test_unpack_length(sample_message):
    message = Message.build(sample_message)

    assert message.unpack_length() == 77


def test_output(sample_message):
    message = Message.build(sample_message)
    expected_output = message.text_length_bytes + message.text

    assert message.output() == expected_output


def test_json(sample_message):
    message = Message.build(sample_message)

    assert message.json() == sample_message


def test_write(sample_message):
    message = Message.build(sample_message)
    mocked_writer = MagicMock()
    message.write(mocked_writer)

    mocked_writer.write.assert_called_with(message.output())


@pytest.mark.asyncio
async def test_async_read_write(sample_message):
    message = Message.build(sample_message)
    mocked_writer = AsyncMock()
    mocked_writer.write = MagicMock()
    mocked_writer.drain = AsyncMock()
    await message.async_write(mocked_writer)
    mocked_writer.write.assert_called_with(message.output())
    mocked_writer.drain.assert_awaited_once()
    mocked_reader = AsyncMock()
    mocked_reader.read = AsyncMock(side_effect=[message.text_length_bytes, message.text])

    received = await Message.async_read(mocked_reader)

    assert received.json() == sample_message
