"""Q_SURVIVAL_ONLY. Disposable online dispatcher, no authority cache/fallback."""
import base64
import hmac
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
import signal
import ssl
from h_quorum.authority import Root
from h_quorum.common import config,BANNER
from h_quorum.wire import start_wire

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_POST(self):
        try:
            self.connection.settimeout(12)
            if self.path!='/rpc' or self.headers.get('Transfer-Encoding'):raise ValueError
            length=int(self.headers['Content-Length'])
            if not 0<length<=1024*1024:raise ValueError
            auth=self.headers.get('Authorization','')
            if not auth.startswith('Basic '):raise ValueError
            role,password=base64.b64decode(auth[6:],validate=True).decode().split(':',1)
            record=self.server.cfg['roles'].get(role)
            if not record or not hmac.compare_digest(record['password'],password):raise ValueError
            payload=json.loads(self.rfile.read(length))
            result=self.server.root.dispatch(role,payload)
            response=json.dumps(dict(ok=True,result=result),sort_keys=True,separators=(',',':')).encode();status=200
        except Exception:response=b'{"ok":false}';status=403
        self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(response)));self.end_headers();self.wfile.write(response)

def main():
    cfg=config();root=Root(cfg);wire=start_wire(cfg,root.dispatch)
    server=ThreadingHTTPServer(('127.0.0.1',cfg['http_port']),Handler);server.daemon_threads=True;server.cfg=cfg;server.root=root
    tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);tls.minimum_version=ssl.TLSVersion.TLSv1_2;tls.load_cert_chain(cfg['tls']['gateway_cert'],cfg['tls']['gateway_key'])
    server.socket=tls.wrap_socket(server.socket,server_side=True)
    print(BANNER,'online authenticated root transport started',flush=True)
    try:server.serve_forever()
    finally:wire.shutdown();wire.server_close();server.server_close()
if __name__=='__main__':main()
