Command Broker
_________________

[![PyPI version](https://badge.fury.io/py/cmdbroker.svg)](http://badge.fury.io/py/cmdbroker)
[![Test Status](https://github.com/brad/cmdbroker/workflows/Test/badge.svg?branch=develop)](https://github.com/brad/cmdbroker/actions?query=workflow%3ATest)
[![Lint Status](https://github.com/brad/cmdbroker/workflows/Lint/badge.svg?branch=develop)](https://github.com/brad/cmdbroker/actions?query=workflow%3ALint)
[![codecov](https://codecov.io/gh/brad/cmdbroker/branch/main/graph/badge.svg)](https://codecov.io/gh/brad/cmdbroker)
[![Join the chat at https://gitter.im/brad/cmdbroker](https://badges.gitter.im/brad/cmdbroker.svg)](https://gitter.im/brad/cmdbroker?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![License](https://img.shields.io/github/license/mashape/apistatus.svg)](https://pypi.python.org/pypi/cmdbroker/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
_________________

[Read Latest Documentation](https://brad.github.io/cmdbroker/) - [Browse GitHub Code Repository](https://github.com/brad/cmdbroker/)
_________________

**cmdbroker** Broker commands to a server

## Overview

Command Broker (cmdbroker) is a tool that allows a client to send commands to a server and get the results back. While for most use cases you can simply run commands over SSH, cmdbroker is designed for scenarios where you need to run commands with access to the server's UI. This can be particularly useful for commands that require graphical interfaces or other UI elements that are not accessible through standard SSH sessions.

## Features

- **Client-Server Architecture**: cmdbroker uses a client-server model to facilitate command execution and result retrieval.
- **SSL Encryption**: All communications between the client and server are secured using SSL, ensuring that data is encrypted and protected from eavesdropping.
- **UI Access**: Enables running commands that require access to the server's UI, which is not possible with standard SSH.
- **Easy Integration**: Simple to integrate into existing workflows and systems.

## Installation

You can install cmdbroker using pip:

```bash
pip install cmdbroker
```

## Usage

### Server

```bash
cmdbroker --server
```

This will walk you through generating an SSL certificate and then start the server. Protect the generated key with `chmod 600 broker-key.pem`. Copy the generated `broker-cert.pem` file to your client machine (after copying, protect it with a similar `chmod`) and follow the instructions for the client

### Client

```bash
cmdbroker 'echo "Hello, World!"'
```

The following happens when you do this:
- The client makes a secure connection to the server
- The client sends the command to the server over this connection
- The server component runs `echo "Hello, World!"`
- The server component takes the output from that command and returns it to the client
- The client outputs the results on stdout

You may also redirect stdin and use it in the server-side command, ex:

```bash
echo "Hello, World\!" | cmdbroker cat
```
