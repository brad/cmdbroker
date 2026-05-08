import socket

from zeroconf import IPVersion, ServiceBrowser, ServiceInfo, Zeroconf


class Discovery:
    def __init__(self, port=None):
        self.port = port
        self.zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        self.info = None

    def register(self, name, port):
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except socket.gaierror:
            local_ip = "127.0.0.1"

        self.info = ServiceInfo(
            "_cmdbroker._tcp.local.",
            f"{name}._cmdbroker._tcp.local.",
            addresses=[socket.inet_aton(local_ip)],
            port=port,
            properties={"version": "0.0.4"},
            server=f"{hostname}.local.",
        )
        self.zeroconf.register_service(self.info)

    def unregister(self):
        if self.info:
            self.zeroconf.unregister_service(self.info)
        self.zeroconf.close()


class DiscoveryBrowser:
    def __init__(self, on_update):
        self.zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
        self.on_update = on_update
        self.services = {}
        self.browser = ServiceBrowser(self.zeroconf, "_cmdbroker._tcp.local.", self)

    def remove_service(self, zeroconf, type, name):
        if name in self.services:
            del self.services[name]
            self.on_update(self.services)

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            address = socket.inet_ntoa(info.addresses[0])
            self.services[name] = {
                "name": name,
                "address": address,
                "port": info.port,
                "properties": info.properties,
            }
            self.on_update(self.services)

    def update_service(self, zeroconf, type, name):
        self.add_service(zeroconf, type, name)

    def close(self):
        self.zeroconf.close()
