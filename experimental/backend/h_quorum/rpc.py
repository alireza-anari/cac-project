"""Verified HTTPS client for the experiment's authenticated root dispatcher."""
from __future__ import annotations

import base64
import http.client
import json
import ssl

from .common import Denied


MAX_BODY = 1024 * 1024
TIMEOUT = 10


class Client:
    def __init__(self, cfg, role="control", namespace=None):
        self.root = cfg.get("root", cfg)
        self.namespace = namespace
        self.role = role
        roles = cfg.get("roles", self.root.get("roles", {}))
        try:
            password = roles[role]["password"]
            if not isinstance(role, str) or ":" in role or not isinstance(password, str):
                raise ValueError
            self.auth = "Basic " + base64.b64encode((role + ":" + password).encode()).decode("ascii")
            self.tls = ssl.create_default_context(cafile=self.root["tls"]["ca"])
            self.tls.minimum_version = ssl.TLSVersion.TLSv1_2
        except Exception:
            raise Denied("denied") from None

    def call(self, action, args=None, namespace=None):
        connection = None
        try:
            request = {"action": action, "args": {} if args is None else args,
                       "namespace": self.namespace if namespace is None else namespace}
            if not isinstance(action, str) or not isinstance(request["args"], dict):
                raise ValueError
            body = json.dumps(request, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
            if len(body) > MAX_BODY:
                raise ValueError
            connection = http.client.HTTPSConnection("127.0.0.1", int(self.root.get("http_port", 6549)),
                                                     timeout=TIMEOUT, context=self.tls)
            connection.request("POST", "/rpc", body=body,
                               headers={"Authorization": self.auth, "Content-Type": "application/json"})
            response = connection.getresponse()
            if response.status != 200:
                raise ValueError
            length = response.getheader("Content-Length")
            if length is None or not length.isdecimal() or int(length) > MAX_BODY:
                raise ValueError
            raw = response.read(int(length) + 1)
            if len(raw) != int(length):
                raise ValueError
            envelope = json.loads(raw.decode("utf-8"))
            if (not isinstance(envelope, dict) or envelope.get("ok") is not True
                    or not isinstance(envelope.get("result"), dict)):
                raise ValueError
            return envelope["result"]
        except Exception:
            raise Denied("denied") from None
        finally:
            if connection is not None:
                connection.close()
