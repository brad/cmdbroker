import argparse
import asyncio
import getpass
import ipaddress
import os
import signal
import ssl
import sys
from datetime import datetime, timedelta

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    BestAvailableEncryption,
    Encoding,
    PrivateFormat,
)
from cryptography.x509.oid import NameOID

from .message import Message


class Server:
    """Server class to handle incoming requests from clients."""

    def __init__(self, params: argparse.Namespace):
        self.address = params.address
        self.port = params.port
        self.broker_cert = params.broker_cert
        self.broker_key = params.broker_key
        self.password = params.password
        self.cert_country = params.cert_country
        self.cert_state = params.cert_state
        self.cert_locality = params.cert_locality
        self.cert_org = params.cert_org
        self.cert_days = params.cert_days
        self.server = None

        if params.generate_cert_and_key:
            if not self.cert_country:
                self.cert_country = input("Enter the country for the certificate: ")
            if not self.cert_state:
                self.cert_state = input("Enter the state for the certificate: ")
            if not self.cert_locality:
                self.cert_locality = input("Enter the locality for the certificate: ")
            if not self.cert_org:
                self.cert_org = input("Enter the organization for the certificate: ")

        if self.password is None:
            try:
                # Prompt the user for a password, do not echo the input
                self.password = getpass.getpass("Enter password for key: ")
            except KeyboardInterrupt:
                sys.exit(0)
            if not self.password:
                print("Password cannot be empty.")
                sys.exit(0)

        if params.generate_cert_and_key:
            self.generate_cert_and_key()

        if not (os.path.exists(self.broker_cert) and os.path.exists(self.broker_key)):
            raise ValueError("SSL files do not exist. Use --generate-cert-and-key to create them.")

    def stop(self):
        if self.server:
            print("Server stopped by user.")
            self.server.close()
        else:
            print("There is no server running.")

    async def run(self):
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, self.stop)

        # Create an SSL context
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        try:
            ssl_context.load_cert_chain(self.broker_cert, self.broker_key, self.password)
        except ssl.SSLError:
            print("Wrong password for key")
            sys.exit(0)

        # Start an SSL server
        self.server = await asyncio.start_server(
            self.handle_request, self.address, self.port, ssl=ssl_context
        )
        addr = ":".join([str(part) for part in self.server.sockets[0].getsockname()])
        print(f"Server listening on {addr}. Press Ctrl+C to stop.")
        try:
            await self.server.serve_forever()
        except asyncio.exceptions.CancelledError:
            # Occurs as a side-effect of SIGINT (Ctrl+C) but we handle that signal
            # in self.stop() so we can safely ignore it here.
            pass

    async def handle_request(self, reader, writer):
        # Process incoming data
        request = await Message.async_read(reader)

        request_json = request.json()
        method = request_json["method"]
        if method == "process":
            parameters = request_json["parameters"]
            cmd = parameters["command"]

            process = await asyncio.create_subprocess_shell(
                cmd, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE
            )

            if "stdin" in request_json:
                process.stdin.write(request_json["stdin"].encode("utf8"))
                process.stdin.close()

            response_text = await process.stdout.read()
        else:
            raise ValueError(f"Invalid method: {method}")

        # Send response to the client
        writer.write(response_text)
        await writer.drain()

        writer.close()
        await writer.wait_closed()

    def generate_cert_and_key(self):
        # Generate a private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Generate a self-signed certificate
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, self.cert_country),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, self.cert_state),
                x509.NameAttribute(NameOID.LOCALITY_NAME, self.cert_locality),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, self.cert_org),
                x509.NameAttribute(NameOID.COMMON_NAME, self.address),
            ]
        )
        # Check if `address` is an IP address
        try:
            # This will succeed if `address` is a valid IP address
            ip_address = ipaddress.ip_address(self.address)
            alt_name = x509.IPAddress(ip_address)
        except ValueError:
            # If it's not an IP address, assume it's a DNS name
            alt_name = x509.DNSName(self.address)
        now = datetime.utcnow()
        certificate = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + timedelta(days=self.cert_days))
            .add_extension(
                x509.SubjectAlternativeName([alt_name]),
                critical=False,
            )
            .sign(private_key, hashes.SHA256())
        )

        # Write out the certificate
        with open(self.broker_cert, "wb") as f:
            f.write(certificate.public_bytes(Encoding.PEM))

        # Write out the private key
        with open(self.broker_key, "wb") as f:
            encryption_algorithm = BestAvailableEncryption(self.password.encode())
            f.write(
                private_key.private_bytes(
                    Encoding.PEM,
                    PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm,
                )
            )

        print(f"Generated certificate {self.broker_cert} and key {self.broker_key}")
