"""Bounded, mutually authenticated etcd v3 JSON gateway client.

Etcd accepts the complete H config, whose ``etcd`` member is the transport
configuration. Bootstrap alone may explicitly use auth_enabled=False.
"""
import base64
import json
import ssl
import urllib.error
import urllib.request

from h_quorum.common import Denied


def b64(value):
    return base64.b64encode(value.encode() if isinstance(value, str) else value).decode()


def unb64(value):
    return base64.b64decode(value, validate=True)


class Etcd:
    def __init__(self, cfg):
        self.cfg = cfg.get('etcd', cfg)
        self.endpoints = tuple(self.cfg['endpoints'])
        if not self.endpoints or any(not e.startswith('https://') for e in self.endpoints):
            raise Denied('denied')
        self.context = ssl.create_default_context(cafile=self.cfg['ca'])
        self.context.minimum_version = ssl.TLSVersion.TLSv1_2
        self.context.load_cert_chain(self.cfg['cert'], self.cfg['key'])
        # Never honor proxy variables for this private loopback channel.
        self.opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=self.context))
        self.token = None

    def _request(self, endpoint, path, body, token=None):
        # etcd AuthInfoFromTLS ignores the gateway's server CN only when
        # Grpcgateway-Accept is present (pinned upstream auth/store.go).
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        if token:
            headers['Authorization'] = token
        request = urllib.request.Request(endpoint.rstrip('/') + path,
                                         json.dumps(body).encode(), headers, method='POST')
        try:
            with self.opener.open(request, timeout=2) as response:
                raw = response.read(16 * 1024 * 1024 + 1)
                if len(raw) > 16 * 1024 * 1024:
                    raise Denied('denied')
                result = json.loads(raw)
        except urllib.error.HTTPError as error:
            # Inspect privately only to distinguish token expiration from failures.
            raw = error.read(65536)
            self.last_http_status=error.code
            diagnostic=raw.decode('utf-8','replace')[:500]
            for secret in (self.cfg.get('password',''),token or '',self.token or ''):
                if secret:diagnostic=diagnostic.replace(secret,'[REDACTED]')
            self.last_error=diagnostic
            self.last_path=path
            if error.code in (502, 503, 504):
                raise _Unavailable() from None
            try:
                result = json.loads(raw)
            except (ValueError, UnicodeError):
                raise Denied('denied') from None
            self.last_rpc_code=result.get('code')
            if error.code == 401 or result.get('code') == 16:
                raise _Expired() from None
            if error.code in (502, 503, 504) or result.get('code') == 14:
                raise _Unavailable() from None
            raise Denied('denied') from None
        if 'error' in result or result.get('code', 0):
            self.last_rpc_code=result.get('code')
            if result.get('code') == 16:
                raise _Expired()
            if result.get('code') == 14:
                raise _Unavailable()
            raise Denied('denied')
        return result

    def _authenticate(self, endpoint):
        result = self._request(endpoint, '/v3/auth/authenticate',
                               {'name': self.cfg['user'], 'password': self.cfg['password']})
        self.token = result.get('token')
        if not self.token:
            raise Denied('denied')

    def call(self, path, body, endpoint=None):
        if not path.startswith('/v3/') or not isinstance(body, dict):
            raise Denied('denied')
        endpoints = (endpoint,) if endpoint else self.endpoints
        if any(e not in self.endpoints for e in endpoints):
            raise Denied('denied')
        for current in endpoints:
            try:
                authenticated = self.cfg.get('auth_enabled', True)
                if authenticated and not self.token:
                    self._authenticate(current)
                try:
                    return self._request(current, path, body, self.token if authenticated else None)
                except _Expired:
                    if not authenticated:
                        raise Denied('denied')
                    self._authenticate(current)
                    return self._request(current, path, body, self.token)
            except (OSError, ValueError, urllib.error.URLError, _Expired, _Unavailable):
                continue
        raise Denied('denied') from None

    def range(self, key, prefix=False, revision=None, serializable=False, endpoint=None):
        raw = key.encode() if isinstance(key, str) else key
        body = {'key': b64(raw), 'serializable': bool(serializable)}
        if prefix:
            end = bytearray(raw)
            while end and end[-1] == 255:
                end.pop()
            if end:
                end[-1] += 1
            body['range_end'] = b64(bytes(end) if end else b'\0')
        if revision is not None:
            body['revision'] = str(revision)
        return self.call('/v3/kv/range', body, endpoint)

    def txn(self, compare, success, failure=None):
        return self.call('/v3/kv/txn', {'compare': compare, 'success': success,
                                       'failure': [] if failure is None else failure})


class _Expired(Exception):
    pass


class _Unavailable(Exception):
    pass
