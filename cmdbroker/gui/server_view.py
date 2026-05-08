import flet as ft
import asyncio
import os
import argparse
import socket
from ..server import Server
from ..discovery import Discovery

class ServerView(ft.Column):
    def __init__(self, flet_page, config):
        super().__init__(expand=True)
        self.flet_page = flet_page
        self.config = config
        self.running_servers = {}
        self.server_name = ft.TextField(label="Server Name", value=socket.gethostname())
        self.server_port = ft.TextField(label="Port", value="8889")
        self.server_list = ft.Column()

    def did_mount(self):
        self.update_server_list()

        self.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Manage Servers", size=20, weight=ft.FontWeight.BOLD),
                        ft.Row([self.server_name, self.server_port, ft.ElevatedButton("Start Server", on_click=self.start_server)]),
                        ft.Divider(),
                        self.server_list,
                    ],
                    scroll=ft.ScrollMode.AUTO,
                ),
                expand=True,
                padding=ft.padding.only(left=20),
            )
        ]
        self.update()

    def update_server_list(self):
        self.server_list.controls = [
            ft.ListTile(
                title=ft.Text(f"{name} (Port: {info['port']})"),
                subtitle=ft.Text("Running" if info['running'] else "Stopped"),
                trailing=ft.IconButton(
                    ft.icons.Icons.STOP if info['running'] else ft.icons.Icons.PLAY_ARROW,
                    on_click=lambda e, n=name: self.toggle_server(n)
                )
            ) for name, info in self.running_servers.items()
        ]
        if hasattr(self, "flet_page"):
            self.flet_page.update()

    async def start_server(self, e):
        name = self.server_name.value
        port = int(self.server_port.value)

        cert_path = os.path.join(os.path.expanduser("~"), ".config", "cmdbroker", f"{name}_cert.pem")
        key_path = os.path.join(os.path.expanduser("~"), ".config", "cmdbroker", f"{name}_key.pem")
        os.makedirs(os.path.dirname(cert_path), exist_ok=True)

        password = self.config.get_password(key_path)
        if not password:
            # Need to prompt for password
            def set_pw(pw):
                self.config.set_password(key_path, pw)
                self.flet_page.dialog.open = False
                self.flet_page.update()
                asyncio.create_task(self.run_server_logic(name, port, cert_path, key_path, pw))

            pw_field = ft.TextField(label="Password", password=True, can_reveal_password=True)
            self.flet_page.dialog = ft.AlertDialog(
                title=ft.Text("Set Server Password"),
                content=pw_field,
                actions=[ft.TextButton("OK", on_click=lambda e: set_pw(pw_field.value))],
            )
            self.flet_page.dialog.open = True
            self.flet_page.update()
            return

        asyncio.create_task(self.run_server_logic(name, port, cert_path, key_path, password))

    async def run_server_logic(self, name, port, cert_path, key_path, password):
        params = argparse.Namespace(
            address="0.0.0.0",
            port=port,
            broker_cert=cert_path,
            broker_key=key_path,
            password=password,
            generate_cert_and_key=not os.path.exists(cert_path),
            cert_country="US",
            cert_state="CA",
            cert_locality="SF",
            cert_org="cmdbroker",
            cert_days=365
        )

        server = Server(params)

        # Override approve_cert_request
        async def approve(client_name):
            result = asyncio.Future()
            def on_click(approved):
                self.flet_page.dialog.open = False
                self.flet_page.update()
                result.set_result(approved)

            self.flet_page.dialog = ft.AlertDialog(
                title=ft.Text("Certificate Request"),
                content=ft.Text(f"Allow '{client_name}' to download the public certificate?"),
                actions=[
                    ft.TextButton("Deny", on_click=lambda e: on_click(False)),
                    ft.TextButton("Allow", on_click=lambda e: on_click(True)),
                ],
            )
            self.flet_page.dialog.open = True
            self.flet_page.update()
            return await result

        server.approve_cert_request = approve

        discovery = Discovery()
        discovery.register(name, port)

        self.running_servers[name] = {
            "port": port,
            "running": True,
            "server": server,
            "discovery": discovery
        }
        self.update_server_list()

        try:
            await server.run()
        except Exception as e:
            if not isinstance(e, asyncio.CancelledError):
                print(f"Server error: {e}")
        finally:
            discovery.unregister()
            if name in self.running_servers:
                self.running_servers[name]["running"] = False
                self.update_server_list()

    def toggle_server(self, name):
        info = self.running_servers[name]
        if info['running']:
            info['server'].stop()
            info['discovery'].unregister()
            info['running'] = False
        else:
            # Re-start logic would go here
            pass
        self.update_server_list()
