import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

fixed = """@app.route('/conductor/login', methods=['GET', 'POST'])
def conductor_login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        conn = get_db()
        conductor = conn.execute("SELECT * FROM conductors WHERE phone=? AND password=?", (phone, password)).fetchone()
        conn.close()
        if conductor:
            session['conductor_id'] = conductor['id']
            session['conductor_name'] = conductor['name']
            return redirect(url_for('conductor_dashboard'))
        return "Invalid credentials", 401
    return render_template('conductor_login.html')"""

pattern = re.compile(r'@app\.route\(\'/conductor/login\', methods=\[\'GET\', \'POST\'\]\).*?(?=@app\.route\(\'/conductor/logout\'\))', re.DOTALL)
content = pattern.sub(fixed + '\n\n', content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
