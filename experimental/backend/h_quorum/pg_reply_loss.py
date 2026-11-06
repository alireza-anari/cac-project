"""Q_SURVIVAL_ONLY. Disposable loopback PG proxy drops an actual terminal ACK.

Synthetic local plaintext connection only. No protocol payload/credential logs.
The actual server COMMIT/ROLLBACK CommandComplete + ReadyForQuery are observed
and withheld from the owned client. This is not an exception-based simulation.
"""
import socket
import socketserver
import struct
import threading
import psycopg

def read_exact(channel,count):
    data=bytearray()
    while len(data)<count:
        chunk=channel.recv(count-len(data))
        if not chunk:raise EOFError
        data.extend(chunk)
    return bytes(data)

def frame(channel):
    kind=read_exact(channel,1);length=read_exact(channel,4);size=struct.unpack('!I',length)[0]
    if not 4<=size<=1024*1024:raise ValueError('Invalid bounded PG frame')
    body=read_exact(channel,size-4);return kind,body,kind+length+body

class PgReplyLoss:
    def __init__(self,lab):
        self.lab=lab;self.armed=None;self.seen=[];outer=self
        class Server(socketserver.ThreadingTCPServer):
            allow_reuse_address=True
            daemon_threads=True
        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                upstream=None;lock=threading.Lock();pending=[None]
                try:
                    upstream=socket.create_connection(('127.0.0.1',lab.cfg['A']['connection']['port']),timeout=5)
                    upstream.settimeout(60);self.request.settimeout(60)
                    length=read_exact(self.request,4);size=struct.unpack('!I',length)[0]
                    if not 8<=size<=8192:raise ValueError('Invalid startup')
                    body=read_exact(self.request,size-4)
                    if struct.unpack('!I',body[:4])[0]!=196608:raise ValueError('Synthetic local proxy requires explicit non-TLS startup')
                    upstream.sendall(length+body)
                    def incoming():
                        try:
                            while True:
                                kind,body,raw=frame(self.request)
                                action=body[:-1].decode('ascii') if kind==b'Q' and body in (b'COMMIT\x00',b'ROLLBACK\x00') else None
                                with lock:
                                    if action and outer.armed==action:pending[0]=action
                                upstream.sendall(raw)
                        except (EOFError,OSError,ValueError):
                            try:upstream.shutdown(socket.SHUT_RDWR)
                            except OSError:pass
                    reader=threading.Thread(target=incoming,daemon=True);reader.start();buffer=[];tag=None
                    while True:
                        kind,body,raw=frame(upstream)
                        with lock:action=pending[0]
                        if action:
                            buffer.append(raw)
                            if sum(map(len,buffer))>1024*1024:raise ValueError('Oversized terminal response')
                            if kind==b'C':tag=body.rstrip(b'\x00').decode('ascii')
                            if kind==b'Z':
                                if body!=b'I' or tag!=action:raise ValueError('Missing positive exact terminal outcome')
                                outer.seen.append(dict(action=action,command_complete=tag,ready='IDLE',reply_dropped=True))
                                self.request.shutdown(socket.SHUT_RDWR);upstream.shutdown(socket.SHUT_RDWR);break
                        else:self.request.sendall(raw)
                except (EOFError,OSError,ValueError):pass
                finally:
                    if upstream:upstream.close()
        self.server=Server(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def connect(self):
        connection=dict(self.lab.cfg['A']['connection']);connection.update(host='127.0.0.1',port=self.server.server_address[1],sslmode='disable')
        return psycopg.connect(**connection,user='cac_ctx_runtime',password=self.lab.cfg['A']['passwords']['cac_ctx_runtime'],connect_timeout=2,prepare_threshold=None)
    def close(self):self.server.shutdown();self.server.server_close();self.thread.join(timeout=3)
