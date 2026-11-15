import os
import sys


def main():
    os.umask(0o077)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
        addresses = [a for a in sys.argv[2:] if not a.startswith('-')]
        if not addresses:
            sys.argv.append('127.0.0.1:8000')
        elif len(addresses) != 1 or not addresses[0].startswith('127.0.0.1:'):
            raise SystemExit('Preview binds only to 127.0.0.1:PORT.')
        if '-6' in sys.argv or '--ipv6' in sys.argv:
            raise SystemExit('IPv6/public binding is disabled.')
    from config.network import install
    install()
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
