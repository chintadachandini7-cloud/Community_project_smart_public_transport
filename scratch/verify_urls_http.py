import urllib.request
import re

urls = [
    'http://127.0.0.1:5000/',
    'http://127.0.0.1:5000/admin',
    'http://127.0.0.1:5000/driver/login',
    'http://127.0.0.1:5000/conductor/login'
]

for url in urls:
    try:
        html = urllib.request.urlopen(url).read().decode("utf-8")
        title = re.search(r"<title>(.*?)</title>", html).group(1)
        print(f"{url} -> {title}")
    except Exception as e:
        print(f"{url} -> ERROR: {e}")
