import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = [
    'https://127.0.0.1:5000/',
    'https://127.0.0.1:5000/admin',
    'https://127.0.0.1:5000/driver/login',
    'https://127.0.0.1:5000/conductor/login'
]

for url in urls:
    try:
        html = urllib.request.urlopen(url, context=ctx).read().decode("utf-8")
        title = re.search(r"<title>(.*?)</title>", html).group(1)
        print(f"{url} -> {title}")
    except Exception as e:
        print(f"{url} -> ERROR: {e}")
