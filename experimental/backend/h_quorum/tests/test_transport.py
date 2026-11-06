"""Q_SURVIVAL_ONLY. Real local TLS/HTTP negative transport; no consensus claim."""
import copy
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import ssl
import threading
import unittest
from h_quorum.common import config,Denied,BANNER
from h_quorum.etcd import Etcd

class TransportTests(unittest.TestCase):
    def test_redirect_cannot_forward_authority_credentials(self):
        cfg=copy.deepcopy(config());calls=[]
        class Sink(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                calls.append(True);body=b'{}';self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        sink=ThreadingHTTPServer(('127.0.0.1',0),Sink)
        class Redirect(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                self.rfile.read(int(self.headers.get('Content-Length','0')))
                self.send_response(302);self.send_header('Location','http://127.0.0.1:'+str(sink.server_port)+'/credential-sink');self.send_header('Content-Length','0');self.end_headers()
        origin=ThreadingHTTPServer(('127.0.0.1',0),Redirect)
        tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);tls.load_cert_chain(cfg['tls']['gateway_cert'],cfg['tls']['gateway_key']);tls.load_verify_locations(cfg['tls']['ca']);tls.verify_mode=ssl.CERT_REQUIRED
        origin.socket=tls.wrap_socket(origin.socket,server_side=True)
        for server in (sink,origin):threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            cfg['etcd']['endpoints']=['https://127.0.0.1:'+str(origin.server_port)]
            client=Etcd(cfg);client.token='synthetic-redirect-negative-fixture'
            with self.assertRaises(Denied,msg='Redirect escaped the pinned HTTPS authority endpoint'):client.call('/v3/kv/range',{'key':'YQ=='})
            self.assertEqual(calls,[],'Redirect forwarded authority credentials outside the TLS endpoint')
            print(BANNER,'TRANSPORT redirect denied without contacting synthetic sink; no quorum proof',flush=True)
        finally:
            for server in (origin,sink):server.shutdown();server.server_close()
