import argparse
import asyncio
import os

import flet as ft

from ..client import Client
from ..discovery import DiscoveryBrowser


class ClientView(ft.Column):
    def __init__(self, flet_page, config):
        super().__init__(expand=True)
        self.flet_page = flet_page
        self.config = config
        self.discovered_services = {}
        self.discovered_list = ft.Column()
        self.remotes_list = ft.Column()
        self.saved_commands = ft.Column()
        self.output_text = ft.TextField(multiline=True, read_only=True, expand=True)
        self.command_input = ft.TextField(label="Command", expand=True)
        self.browser = DiscoveryBrowser(self.on_discovery_update)

    def on_discovery_update(self, services):
        self.discovered_services = services
        self.update_discovered_list()

    def update_discovered_list(self):
        self.discovered_list.controls = [
            ft.ListTile(
                title=ft.Text(name),
                subtitle=ft.Text(f"{info['address']}:{info['port']}"),
                trailing=ft.IconButton(
                    ft.icons.Icons.ADD, on_click=lambda e, i=info: self.add_remote(i)
                ),
            )
            for name, info in self.discovered_services.items()
        ]
        self.flet_page.update()

    def add_remote(self, info):
        # Implementation for adding remote and requesting cert
        asyncio.create_task(self.request_cert_and_add(info))

    async def request_cert_and_add(self, info):
        temp_params = argparse.Namespace(
            address=info["address"], port=info["port"], command=None, broker_cert="temp_cert.pem"
        )
        client = Client(temp_params)
        try:
            cert_data = await client.request_certificate()
            # Show dialog to save cert
            cert_path = os.path.join(
                os.path.expanduser("~"), ".config", "cmdbroker", f"{info['name']}.pem"
            )
            os.makedirs(os.path.dirname(cert_path), exist_ok=True)
            with open(cert_path, "wb") as f:
                f.write(cert_data)

            self.config.remotes.append(
                {
                    "name": info["name"],
                    "address": info["address"],
                    "port": info["port"],
                    "cert": cert_path,
                    "commands": [],
                }
            )
            self.config.save()
            self.update_remotes_list()
        except Exception as e:
            self.flet_page.snack_bar = ft.SnackBar(ft.Text(f"Failed to get cert: {e}"))
            self.flet_page.snack_bar.open = True
            self.flet_page.update()

    def did_mount(self):
        self.update_remotes_list()

        self.controls = [
            ft.Row(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Discovered Servers", size=20, weight=ft.FontWeight.BOLD),
                                self.discovered_list,
                                ft.Divider(),
                                ft.Text("Saved Connections", size=20, weight=ft.FontWeight.BOLD),
                                self.remotes_list,
                            ],
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        width=300,
                        padding=ft.padding.only(left=20),
                    ),
                    ft.VerticalDivider(),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    self.command_input,
                                    ft.ElevatedButton("Run", on_click=self.run_command),
                                ]
                            ),
                            ft.Row(
                                [
                                    ft.Text("Quick Commands", size=16, weight=ft.FontWeight.BOLD),
                                    ft.IconButton(ft.icons.Icons.SAVE, on_click=self.save_command),
                                ]
                            ),
                            self.saved_commands,
                            self.output_text,
                        ],
                        expand=True,
                    ),
                ],
                expand=True,
            )
        ]
        self.update()

    def update_remotes_list(self):
        self.remotes_list.controls = [
            ft.ListTile(title=ft.Text(r["name"]), on_click=lambda e, r=r: self.select_remote(r))
            for r in self.config.remotes
        ]
        if hasattr(self, "flet_page"):
            self.flet_page.update()

    def select_remote(self, remote):
        self.selected_remote = remote
        self.update_saved_commands()
        self.flet_page.snack_bar = ft.SnackBar(ft.Text(f"Selected {remote['name']}"))
        self.flet_page.snack_bar.open = True
        self.flet_page.update()

    def update_saved_commands(self):
        if not hasattr(self, "selected_remote"):
            return

        commands = self.selected_remote.get("commands", [])
        self.saved_commands.controls = [
            ft.Row(
                [
                    ft.TextButton(cmd, on_click=lambda e, c=cmd: self.run_saved_command(c)),
                    ft.IconButton(
                        ft.icons.Icons.DELETE,
                        on_click=lambda e, c=cmd: self.delete_saved_command(c),
                    ),
                ]
            )
            for cmd in commands
        ]
        self.flet_page.update()

    def save_command(self, e):
        if not hasattr(self, "selected_remote") or not self.command_input.value:
            return

        if "commands" not in self.selected_remote:
            self.selected_remote["commands"] = []

        if self.command_input.value not in self.selected_remote["commands"]:
            self.selected_remote["commands"].append(self.command_input.value)
            self.config.save()
            self.update_saved_commands()

    def delete_saved_command(self, cmd):
        if cmd in self.selected_remote.get("commands", []):
            self.selected_remote["commands"].remove(cmd)
            self.config.save()
            self.update_saved_commands()

    async def run_saved_command(self, cmd):
        self.command_input.value = cmd
        self.flet_page.update()
        await self.run_command(None)

    async def run_command(self, e):
        if not hasattr(self, "selected_remote"):
            return

        params = argparse.Namespace(
            address=self.selected_remote["address"],
            port=self.selected_remote["port"],
            command=self.command_input.value,
            broker_cert=self.selected_remote["cert"],
        )
        client = Client(params)
        try:
            # We need a way to capture output from Client.run()
            # For now, let's mock the relay_to_server call or modify Client
            from ..message import Message

            payload = {"method": "process", "parameters": {"command": params.command}}
            response = await client.relay_to_server(Message.build(payload))
            self.output_text.value += f"\n> {params.command}\n{response.text.decode('utf-8')}"
            self.flet_page.update()
        except Exception as err:
            self.output_text.value += f"\nError: {err}"
            self.flet_page.update()
