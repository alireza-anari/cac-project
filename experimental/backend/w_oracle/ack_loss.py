"""W_ORACLE_ASSUMED. One disposable plaintext PG wire fault, never production."""
import socket
import struct
import threading


class CommitReplyLoss:
    """Pass opaque auth/query bytes; drop COMMIT CommandComplete + remaining ACK.

    No protocol payload, credential or query is logged or retained. sslmode is
    explicitly disabled only for this loopback fault fixture. Not a TLS test.
    """
    def __init__(self,target_port=5432):
        self.target_port=target_port;self.armed=threading.Event();self.dropped=threading.Event()
        self.errors=[];self.sockets=[]
        self.listener=socket.socket();self.listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.listener.bind(('127.0.0.1',0));self.port=self.listener.getsockname()[1]
        self.listener.listen(1);self.listener.settimeout(10)
        self.thread=threading.Thread(target=self._run,daemon=True);self.thread.start()
    @staticmethod
    def _read(sock,count):
        data=bytearray()
        while len(data)<count:
            part=sock.recv(count-len(data))
            if not part:return None
            data.extend(part)
        return bytes(data)
    def _upstream(self,client,server):
        try:
            while True:
                data=client.recv(65536)
                if not data:break
                server.sendall(data)
        except OSError:pass
        finally:
            try:server.shutdown(socket.SHUT_WR)
            except OSError:pass
    def _run(self):
        try:
            client,_=self.listener.accept();server=socket.create_connection(('127.0.0.1',self.target_port),timeout=8)
            self.sockets=[client,server];server.settimeout(8)
            forward=threading.Thread(target=self._upstream,args=(client,server),daemon=True);forward.start()
            while True:
                header=self._read(server,5)
                if header is None:break
                length=struct.unpack('!I',header[1:])[0]
                if not 4<=length<=16*1024*1024:raise AssertionError('Invalid fixture protocol frame')
                payload=self._read(server,length-4)
                if payload is None:break
                if self.armed.is_set() and header[:1]==b'C' and payload==b'COMMIT\x00':
                    self.dropped.set();break
                client.sendall(header+payload)
        except Exception as error:
            self.errors.append(type(error).__name__)
        finally:
            for sock in self.sockets:
                try:sock.shutdown(socket.SHUT_RDWR)
                except OSError:pass
                sock.close()
            self.listener.close()
    def close(self):
        for sock in self.sockets:
            try:sock.shutdown(socket.SHUT_RDWR)
            except OSError:pass
        self.listener.close();self.thread.join(3)
