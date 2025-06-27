"""Simple multi-NIC SOCKS5 proxy (TCP only).

Run manually for quick test:
    python multipath_proxy.py -lhost 127.0.0.1 -lport 1080 192.168.225.100 172.20.10.2@2

Positional arguments are "ip[@weight]" pairs. Weights default to 1.

For each outgoing connection the proxy chooses a source IP from the list
provided at start() and binds() the socket accordingly. A round-robin
algorithm with optional integer weights is used.

Only basic SOCKS5 (no authentication, CONNECT command) is implemented.
This keeps the implementation lightweight and dependency-free.

Tested on Windows 10+ and Python 3.9+.
"""
from __future__ import annotations

import socket
import struct
import threading
import itertools
import select
from typing import List, Tuple

SOCKS_VERSION = 5

class _WeightedRoundRobin:
    """Return items according to weight in a simple round-robin cycle."""

    def __init__(self, items: List[Tuple[str, int]]):
        expanded = []
        for ip, w in items:
            expanded.extend([ip] * max(1, int(w)))
        self._cycle = itertools.cycle(expanded)

    def next(self) -> str:
        return next(self._cycle)

class MultiNICSOCKSProxy:
    def __init__(self, listen_host: str, listen_port: int,
                 ip_weights: List[Tuple[str, int]], quiet: bool = False):
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.ip_weights = ip_weights
        self.quiet = quiet
        self._rr = _WeightedRoundRobin(ip_weights)
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._stop_event = threading.Event()
        self._threads: List[threading.Thread] = []

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------
    def start(self):
        self._server.bind((self.listen_host, self.listen_port))
        self._server.listen(128)
        t = threading.Thread(target=self._accept_loop, daemon=True)
        t.start()
        self._threads.append(t)
        if not self.quiet:
            print(f"[INFO] SOCKS5 server started on {self.listen_host}:{self.listen_port}")

    def stop(self):
        self._stop_event.set()
        try:
            self._server.close()
        except Exception:
            pass
        for th in self._threads:
            if th.is_alive():
                th.join(timeout=0.2)
        if not self.quiet:
            print("[INFO] SOCKS5 server stopped")

    # ------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------
    def _accept_loop(self):
        while not self._stop_event.is_set():
            try:
                client, addr = self._server.accept()
            except OSError:
                break  # socket closed
            t = threading.Thread(target=self._handle_client, args=(client,), daemon=True)
            t.start()
            self._threads.append(t)

    def _log(self, msg: str):
        if not self.quiet:
            print(msg)

    def _handle_client(self, client: socket.socket):
        try:
            if not self._socks5_handshake(client):
                client.close()
                return
            dest_addr, dest_port = self._socks5_parse_request(client)
            if dest_addr is None:
                client.close()
                return
            # choose interface
            src_ip = self._rr.next()
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                # bind to chosen NIC
                remote.bind((src_ip, 0))
            except OSError as e:
                self._log(f"[WARN] bind({src_ip}) failed: {e}, falling back to default")
            remote.settimeout(10)
            remote.connect((dest_addr, dest_port))
            # reply success to client
            reply = b"\x05\x00\x00\x01" + socket.inet_aton("0.0.0.0") + struct.pack("!H", 0)
            client.sendall(reply)
            self._relay_tcp(client, remote)
        except Exception as e:
            self._log(f"[ERR] client error: {e}")
        finally:
            try:
                client.close()
            except Exception:
                pass

    # ---- SOCKS5 helpers --------------------------------------------------
    def _socks5_handshake(self, client: socket.socket) -> bool:
        data = client.recv(2)
        if len(data) < 2 or data[0] != SOCKS_VERSION:
            return False
        n_methods = data[1]
        methods = client.recv(n_methods)
        # we only support NO AUTH (0x00)
        if 0x00 not in methods:
            # no acceptable methods
            client.sendall(struct.pack("!BB", SOCKS_VERSION, 0xFF))
            return False
        # reply NO AUTH
        client.sendall(struct.pack("!BB", SOCKS_VERSION, 0x00))
        return True

    def _socks5_parse_request(self, client: socket.socket):
        # request: ver, cmd, rsv, atyp
        data = client.recv(4)
        if len(data) < 4:
            return None, None
        ver, cmd, _, atyp = data
        if ver != SOCKS_VERSION or cmd != 1:  # CONNECT only
            return None, None
        if atyp == 1:  # IPv4
            addr = socket.inet_ntoa(client.recv(4))
        elif atyp == 3:  # domain
            domain_len = client.recv(1)[0]
            addr = client.recv(domain_len).decode()
        else:
            return None, None
        port = struct.unpack("!H", client.recv(2))[0]
        return addr, port

    # ---- Data relay ------------------------------------------------------
    def _relay_tcp(self, sock1: socket.socket, sock2: socket.socket):
        sock1.setblocking(False)
        sock2.setblocking(False)
        while True:
            r, _, _ = select.select([sock1, sock2], [], [], 60)
            if not r:
                break  # timeout
            if sock1 in r:
                data = sock1.recv(4096)
                if not data:
                    break
                sock2.sendall(data)
            if sock2 in r:
                data = sock2.recv(4096)
                if not data:
                    break
                sock1.sendall(data)
        try:
            sock1.close()
        except Exception:
            pass
        try:
            sock2.close()
        except Exception:
            pass

# ---------------------------------------------------------------------
# CLI helper
# ---------------------------------------------------------------------
if __name__ == "__main__":
    import argparse, sys

    def parse_ip_weight(arg: str):
        if "@" in arg:
            ip, w = arg.split("@", 1)
            return ip, int(w)
        return arg, 1

    p = argparse.ArgumentParser(description="Multi-NIC SOCKS5 proxy")
    p.add_argument("ips", nargs="+", help="IP[@weight] list for NICs")
    p.add_argument("--lhost", default="127.0.0.1", help="Listen host (default 127.0.0.1)")
    p.add_argument("--lport", type=int, default=1080, help="Listen port (default 1080)")
    p.add_argument("--quiet", action="store_true", help="Suppress logs")
    args = p.parse_args()

    ip_weights = [parse_ip_weight(a) for a in args.ips]
    proxy = MultiNICSOCKSProxy(args.lhost, args.lport, ip_weights, quiet=args.quiet)
    proxy.start()
    try:
        while True:
            # run until Ctrl+C
            threading.Event().wait(60)
    except KeyboardInterrupt:
        proxy.stop()
        sys.exit(0)
