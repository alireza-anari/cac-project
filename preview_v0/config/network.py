"""No outbound socket traffic in this local application (not an OS sandbox)."""
import sys

_installed = False


def install():
    global _installed
    if _installed:
        return

    def guard(event, args):
        if event in ('socket.connect', 'socket.sendto'):
            raise RuntimeError('Outbound network is disabled in CAC Preview V0.')
        if event in ('socket.getaddrinfo', 'socket.gethostbyname', 'socket.gethostbyaddr'):
            host = args[0]
            if host not in ('localhost', '127.0.0.1', '::1'):
                raise RuntimeError('External DNS is disabled in CAC Preview V0.')

    sys.addaudithook(guard)
    _installed = True
