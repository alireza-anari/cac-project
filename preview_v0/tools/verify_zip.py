"""Cold-install ZIP and exercise real local HTTP, restart and persistence.

Run with Python 3.12: python tools/verify_zip.py ZIP NEW_DIRECTORY.
Installs dependencies only during setup. HTTP traffic stays on 127.0.0.1.
Never prints generated credentials, cookies or secret keys.
"""
import hashlib
import http.cookiejar
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import zipfile

archive_path = Path(sys.argv[1]).resolve()
target = Path(sys.argv[2]).resolve()
target.mkdir(exist_ok=False, parents=True)
with zipfile.ZipFile(archive_path) as archive:
    names = archive.namelist()
    for name in names:
        p = Path(name)
        assert not p.is_absolute() and '..' not in p.parts
        assert not any(x in p.parts for x in ('.local_state', '.venv', '__pycache__'))
        assert not any(x.startswith('.env') for x in p.parts)
        assert not name.endswith(('.sqlite3', '.pyc', '.log'))
    archive.extractall(target)
root = target / 'preview_v0'
for line in (root/'MANIFEST.sha256').read_text().splitlines():
    digest, name = line.split('  ', 1)
    assert hashlib.sha256((target/name).read_bytes()).hexdigest() == digest
print('ZIP manifest and exclusion audit: PASS', flush=True)
env = target / 'fresh-venv'
subprocess.run([sys.executable, '-m', 'venv', str(env)], check=True)
python = env / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def command(*args, private=False):
    result = subprocess.run([str(python), *args], cwd=root, text=True,
                            capture_output=True, timeout=180)
    print('COMMAND:', ' '.join(args), 'EXIT:', result.returncode, flush=True)
    if not private:
        print(result.stdout, result.stderr, flush=True)
    result.check_returncode()
    return result.stdout


command('-m', 'pip', 'install', '-r', 'requirements.txt')
command('manage.py', 'check')
command('manage.py', 'migrate')
bootstrap = command('manage.py', 'setup_demo', private=True)
password = bootstrap.split('رمز تصادفی: ', 1)[1].splitlines()[0]
command('manage.py', 'test', '--verbosity', '1')
with socket.socket() as probe:
    probe.bind(('127.0.0.1', 0))
    port = probe.getsockname()[1]
base = f'http://127.0.0.1:{port}'
cookiejar = http.cookiejar.CookieJar()
# Disable environmental proxies for this authorized loopback-only test client.
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                   urllib.request.HTTPCookieProcessor(cookiejar))


def get(path):
    with opener.open(base+path, timeout=4) as response:
        return response.read().decode(), response.geturl()


def post(path, values):
    get(path)
    values['csrfmiddlewaretoken'] = next(c.value for c in cookiejar if c.name == 'csrftoken')
    req = urllib.request.Request(base+path, data=urllib.parse.urlencode(values).encode(),
                                 headers={'Origin': base})
    with opener.open(req, timeout=5) as response:
        return response.read().decode(), response.geturl()


def start():
    process = subprocess.Popen([str(python), '-u', 'manage.py', 'runserver', f'127.0.0.1:{port}', '--noreload'],
                               cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    deadline = time.monotonic()+15
    while time.monotonic() < deadline:
        try:
            get('/login/')
            return process
        except (OSError, urllib.error.URLError):
            if process.poll() is not None:
                raise RuntimeError(process.stdout.read().decode())
            time.sleep(0.1)
    process.terminate()
    raise RuntimeError('Local HTTP server did not start.')


process = start()
try:
    page, url = post('/login/', {'username': 'demo', 'password': password})
    assert urllib.parse.urlparse(url).path == '/'
    page, url = post('/stores/new/', {'name': 'فروشگاه سرد', 'description': 'فقط داده ساختگی'})
    home = urllib.parse.urlparse(url).path
    assert re.fullmatch(r'/s/\d+/', home)
    for name, price in [('قهوه عربیکا', '125000'), ('مشاوره نمونه', '')]:
        page, _ = post(home+'products/new/', {'name': name, 'description': 'محلی', 'kind': 'product', 'price': price, 'available': 'on'})
        assert name in page
    post(home+'assistant/', {'name': 'یار سرد', 'greeting': 'خوش آمدید به نمونه', 'tone': 'friendly'})
    page, _ = post(home+'chat/', {'question': 'قیمت قهوه عربیکا چقدر است؟'})
    assert '125,000' in page and 'هوش مصنوعی واقعی متصل نیست' in page
    page, _ = get(home)
    edit = re.search(r'href="([^"]+/products/\d+/edit/)"', page).group(1)
    post(edit, {'name': 'قهوه عربیکا', 'description': 'اطلاعات تازه', 'kind': 'product', 'price': '99000', 'available': 'on'})
    page, _ = post(home+'chat/', {'question': 'قیمت قهوه عربیکا'})
    assert '99,000' in page
    page, _ = post(home+'chat/', {'question': 'هوای فردا چگونه است؟'})
    assert 'اطلاعاتی درباره این پرسش' in page
    assert 'خوش آمدید به نمونه' in page
    print('Real HTTP login → Store → 2 products → assistant → chat → changed price → fallback: PASS', flush=True)
finally:
    process.terminate()
    process.wait(timeout=10)

process = start()
try:
    page, _ = get(home)
    assert 'قهوه عربیکا' in page and 'فروشگاه سرد' in page
    page, _ = post(home+'chat/', {'question': 'قیمت قهوه عربیکا'})
    assert '99,000' in page and 'یار سرد' in page
    print('Process STOP/START: SQLite, session, assistant and updated reply persisted: PASS', flush=True)
finally:
    process.terminate()
    process.wait(timeout=10)
print('Cold ZIP installation + real loopback HTTP journey: PASS. Browser/manual/mobile: NOT_RUN.', flush=True)
