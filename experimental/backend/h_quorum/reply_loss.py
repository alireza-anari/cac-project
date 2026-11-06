"""Q_SURVIVAL_ONLY. Real private TLS forwarding fixture drops committed RPC reply."""
import copy
import http.client
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
import socket
import ssl
import threading

class ReplyLoss:
    def __init__(self,cfg,action):
        self.cfg=copy.deepcopy(cfg);self.seen=[];outer=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                self.connection.settimeout(12)
                count=self.headers.get('Content-Length','')
                if self.path!='/rpc' or not count.isdecimal() or int(count)>1024*1024:self.send_error(400);return
                body=self.rfile.read(int(count));request=json.loads(body)
                channel=http.client.HTTPSConnection('127.0.0.1',cfg['http_port'],timeout=12,context=ssl.create_default_context(cafile=cfg['tls']['ca']))
                try:
                    channel.request('POST','/rpc',body,{'Authorization':self.headers.get('Authorization',''),'Content-Type':'application/json'})
                    response=channel.getresponse();raw=response.read(1024*1024+1)
                    if len(raw)>1024*1024:raise AssertionError('Oversized proxy upstream reply')
                    accepted=response.status==200 and json.loads(raw).get('ok') is True
                    if request['action']==action and accepted:
                        outer.seen.append(dict(action=action,namespace=request['namespace'],upstream_ack=True))
                        self.close_connection=True
                        self.connection.shutdown(socket.SHUT_RDWR);self.connection.close();return
                    self.send_response(response.status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
                finally:channel.close()
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);tls.minimum_version=ssl.TLSVersion.TLSv1_2;tls.load_cert_chain(cfg['tls']['gateway_cert'],cfg['tls']['gateway_key'])
        self.server.socket=tls.wrap_socket(self.server.socket,server_side=True)
        self.cfg['http_port']=self.server.server_port
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def close(self):self.server.shutdown();self.server.server_close();self.thread.join(timeout=3)
