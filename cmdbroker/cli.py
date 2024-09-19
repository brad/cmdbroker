import argparse
import asyncio
import json
import os

from .client import Client
from .server import Server


# Main function to start server and client
async def main(args: argparse.Namespace):
    if args.server:
        await Server(args).run()
    else:
        await Client(args).run()


async def run():
    parser = argparse.ArgumentParser(prog="cmdbroker", description="Run as server or client.")
    parser.add_argument(
        "--config", type=str, default="cmdbroker.json", help="Path to the configuration file"
    )
    # Temporarily parse known args to get config file path
    temp_args, _ = parser.parse_known_args()

    config = {}
    if temp_args.config and os.path.exists(temp_args.config):
        with open(temp_args.config, "r") as f:
            config = json.load(f)

    # Define all other arguments
    parser.add_argument(
        "command",
        type=str,
        nargs="?",
        help="The command to execute on the broker",
        default=config.get("command"),
    )
    parser.add_argument(
        "--server",
        action="store_true",
        help="Run in server mode",
        default=config.get("server", False),
    )
    parser.add_argument(
        "--generate-cert-and-key",
        action="store_true",
        help="Generate a certificate and key",
        default=config.get("generate-cert-and-key", False),
    )
    parser.add_argument(
        "--password",
        type=str,
        default=config.get("password"),
        help="The password to use for the key",
    )
    parser.add_argument(
        "--cert-country",
        type=str,
        default=config.get("cert-country"),
        help="The country for the certificate",
    )
    parser.add_argument(
        "--cert-state",
        type=str,
        default=config.get("cert-state"),
        help="The state for the certificate",
    )
    parser.add_argument(
        "--cert-locality",
        type=str,
        default=config.get("cert-locality"),
        help="The locality for the certificate",
    )
    parser.add_argument(
        "--cert-org",
        type=str,
        default=config.get("cert-org"),
        help="The organization for the certificate",
    )
    parser.add_argument(
        "--cert-days",
        type=int,
        default=config.get("cert-days", 365),
        help="The number of days the certificate is valid for",
    )
    parser.add_argument(
        "--broker-key",
        type=str,
        default=config.get("broker-key", "broker-key.pem"),
        help="The broker key file",
    )
    parser.add_argument(
        "--broker-cert",
        type=str,
        default=config.get("broker-cert", "broker-cert.pem"),
        help="The broker certificate file",
    )
    parser.add_argument(
        "--address",
        type=str,
        required="address" not in config,
        help="The address to bind to",
        default=config.get("address"),
    )
    parser.add_argument(
        "--port", type=int, default=config.get("port", 8889), help="The port to bind to"
    )

    args = parser.parse_args()

    if not args.server and not args.command:
        parser.error("You must provide a command when running in client mode")

    if not args.generate_cert_and_key or not args.server:
        if not os.path.exists(args.broker_cert):
            parser.error("Broker certificate file not found")

    if not args.generate_cert_and_key and args.server:
        if not os.path.exists(args.broker_key):
            parser.error("Broker key file not found")

    await main(args)


def async_run():
    asyncio.run(run())
