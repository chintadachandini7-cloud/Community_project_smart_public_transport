with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("@app.route('/driver/login', methods=['GET', 'POST'])", "@app.route('/driver/login', methods=['GET', 'POST'], strict_slashes=False)")
content = content.replace("@app.route('/conductor/login', methods=['GET', 'POST'])", "@app.route('/conductor/login', methods=['GET', 'POST'], strict_slashes=False)")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
