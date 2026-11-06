"""Bounded TLS PostgreSQL-wire adapter for read-only checker RPCs.

This is not a SQL engine or an authority. Each query calls the supplied live
dispatcher with the authenticated role, which must bind that role to its node.
"""
from __future__ import annotations

import base64
import hmac
import json
import re
import secrets
import socketserver
import ssl
import struct
import threading


MAX_PAYLOAD = 8192
MAX_FRAME = 16384
MAX_STARTUP = 4096
TIMEOUT = 10
SSL_REQUEST = 80877103
PROTOCOL_3 = 196608
QUERY = re.compile(rb"SELECT h_call\('([A-Za-z0-9+/]*={0,2})'\);?\x00\Z")


def _json(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate key")
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))


class _Denied(Exception):
    pass


class _Handler(socketserver.BaseRequestHandler):
    def _read(self, size):
        chunks = bytearray()
        while len(chunks) < size:
            part = self.request.recv(size - len(chunks))
            if not part:
                raise EOFError
            chunks.extend(part)
        return bytes(chunks)

    def _packet(self, kind, body=b""):
        self.request.sendall(kind + struct.pack("!I", len(body) + 4) + body)

    def _error(self):
        self._packet(b"E", b"SERROR\x00VERROR\x00C42501\x00Mdenied\x00\x00")

    def _frame(self):
        kind = self._read(1)
        size = struct.unpack("!I", self._read(4))[0]
        if not 4 <= size <= MAX_FRAME:
            raise _Denied
        return kind, self._read(size - 4)

    def _startup(self):
        size = struct.unpack("!I", self._read(4))[0]
        if not 8 <= size <= MAX_STARTUP:
            raise _Denied
        body = self._read(size - 4)
        if struct.unpack("!I", body[:4])[0] != PROTOCOL_3:
            raise _Denied
        fields = body[4:].split(b"\x00")
        if len(fields) < 6 or fields[-2:] != [b"", b""]:
            raise _Denied
        fields = fields[:-2]
        if len(fields) % 2:
            raise _Denied
        params = {}
        for key, value in zip(fields[::2], fields[1::2]):
            key, value = key.decode("ascii"), value.decode("utf-8")
            if key in params or key not in {"user", "database", "client_encoding", "application_name"}:
                raise _Denied
            params[key] = value
        if params.get("database") != "rcheck":
            raise _Denied
        role = params.get("user", "")
        record = self.server.roles.get(role)
        # Return the same generic error for missing, coordinator and control roles.
        valid = isinstance(record, dict) and record.get("kind") == "check"
        expected = str(record.get("password", "")) if valid else secrets.token_hex(32)
        self._packet(b"R", struct.pack("!I", 3))
        kind, supplied = self._frame()
        if kind != b"p" or not supplied.endswith(b"\x00") or b"\x00" in supplied[:-1]:
            raise _Denied
        if not hmac.compare_digest(supplied[:-1], expected.encode("utf-8")) or not valid:
            raise _Denied
        self.role = role
        self._packet(b"R", struct.pack("!I", 0))
        for key, value in [("server_version", "17.11"), ("client_encoding", "UTF8"),
                           ("standard_conforming_strings", "on")]:
            self._packet(b"S", key.encode() + b"\x00" + value.encode() + b"\x00")
        self._packet(b"K", struct.pack("!II", secrets.randbits(31), secrets.randbits(31)))
        self._packet(b"Z", b"I")

    def _query(self, body):
        match = QUERY.fullmatch(body)
        if not match:
            raise _Denied
        encoded = match.group(1)
        if len(encoded) > 4 * ((MAX_PAYLOAD + 2) // 3):
            raise _Denied
        raw = base64.b64decode(encoded, validate=True)
        if len(raw) > MAX_PAYLOAD or base64.b64encode(raw) != encoded:
            raise _Denied
        payload = _json(raw.decode("utf-8"))
        if (not isinstance(payload, dict) or set(payload) != {"action", "args", "namespace"}
                or payload["action"] not in {"status", "guard", "verify"}
                or not isinstance(payload["args"], dict)
                or not isinstance(payload["namespace"], str)
                or not 1 <= len(payload["namespace"]) <= 256):
            raise _Denied
        result = self.server.callback(self.role, payload)
        if not isinstance(result, dict):
            raise _Denied
        value = json.dumps(result, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=True, allow_nan=False).encode("utf-8")
        if len(value) > MAX_FRAME:
            raise _Denied
        # One text column called r: table=0, attribute=0, type=text(25), size=-1.
        self._packet(b"T", struct.pack("!H", 1) + b"r\x00" +
                     struct.pack("!IhIhih", 0, 0, 25, -1, -1, 0))
        self._packet(b"D", struct.pack("!Hi", 1, len(value)) + value)
        self._packet(b"C", b"SELECT 1\x00")
        self._packet(b"Z", b"I")

    def handle(self):
        encrypted = False
        try:
            self.request.settimeout(TIMEOUT)
            # Refuse plaintext startup, CancelRequest and every other pre-TLS input.
            if self._read(8) != struct.pack("!II", 8, SSL_REQUEST):
                return
            self.request.sendall(b"S")
            self.request = self.server.tls.wrap_socket(self.request, server_side=True)
            encrypted = True
            self.request.settimeout(TIMEOUT)
            self._startup()
            while True:
                kind, body = self._frame()
                if kind == b"X" and not body:
                    return
                if kind != b"Q":
                    raise _Denied
                self._query(body)
        except Exception:
            if encrypted:
                try:
                    self._error()
                except Exception:
                    pass
        finally:
            self.request.close()


class _Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
    block_on_close = False

    def handle_error(self, request, client_address):
        # Never send request data, credentials or callback exceptions to logs.
        pass


def start_wire(cfg, callback):
    """Start a daemon listener; caller shuts it down with shutdown/server_close."""
    root = cfg.get("root", cfg)
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.minimum_version = ssl.TLSVersion.TLSv1_2
    tls.load_cert_chain(root["tls"]["gateway_cert"], root["tls"]["gateway_key"])
    server = _Server((root.get("wire_host", "0.0.0.0"), int(root.get("wire_port", 6548))), _Handler)
    server.tls = tls
    server.roles = cfg.get("roles", root.get("roles", {}))
    server.callback = callback
    threading.Thread(target=server.serve_forever, name="h-checker-wire", daemon=True).start()
    return server
