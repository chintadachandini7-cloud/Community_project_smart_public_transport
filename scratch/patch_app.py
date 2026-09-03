import sqlite3

def patch_app_py():
    with open('app_recovered.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    # Recreate the missing lines 51-149 block
    block1 = """
@app.route('/api/routes/<int:id>', methods=['PUT'])
def update_route(id):
    data = request.json
    conn = get_db()
    conn.execute('UPDATE routes SET route_name=?, source=?, destination=?, operator=?, service_type=?, data_source=? WHERE id=?',
                 (data['route_name'], data['source'], data['destination'], data.get('operator'), data.get('service_type'), data.get('data_source', 'OFFICIAL'), id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/routes/<int:id>', methods=['DELETE'])
def delete_route(id):
    conn = get_db()
    conn.execute('DELETE FROM routes WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/stops', methods=['GET', 'POST'])
def manage_stops():
    conn = get_db()
    if request.method == 'GET':
        stops = conn.execute('SELECT s.*, r.route_name FROM stops s LEFT JOIN routes r ON s.route_id = r.id ORDER BY s.route_id, s.stop_order').fetchall()
        conn.close()
        return jsonify([dict(s) for s in stops])
    else:
        data = request.json
        conn.execute('INSERT INTO stops (route_id, stop_name, latitude, longitude, stop_order, area_type, data_source) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (data['route_id'], data['stop_name'], data['latitude'], data['longitude'], data['stop_order'], data.get('area_type'), data.get('data_source', 'OFFICIAL')))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/api/stops/<int:id>', methods=['PUT', 'DELETE'])
def manage_stop(id):
    conn = get_db()
    if request.method == 'PUT':
        data = request.json
        conn.execute('UPDATE stops SET route_id=?, stop_name=?, latitude=?, longitude=?, stop_order=?, area_type=?, data_source=? WHERE id=?',
                     (data['route_id'], data['stop_name'], data['latitude'], data['longitude'], data['stop_order'], data.get('area_type'), data.get('data_source', 'OFFICIAL'), id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    elif request.method == 'DELETE':
        conn.execute('DELETE FROM stops WHERE id=?', (id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/api/buses', methods=['GET', 'POST'])
def manage_buses():
    conn = get_db()
    if request.method == 'GET':
        buses = conn.execute('SELECT b.*, r.route_name FROM buses b LEFT JOIN routes r ON b.route_id = r.id').fetchall()
        conn.close()
        return jsonify([dict(b) for b in buses])
    else:
        data = request.json
        conn.execute('INSERT INTO buses (bus_number, bus_name, route_id, current_latitude, current_longitude, status, operator, service_type, data_source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     (data['bus_number'], data.get('bus_name'), data['route_id'], data['current_latitude'], data['current_longitude'], data['status'], data.get('operator'), data.get('service_type'), data.get('data_source', 'OFFICIAL')))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/api/buses/<int:id>', methods=['PUT', 'DELETE'])
def manage_bus(id):
    conn = get_db()
    if request.method == 'PUT':
        data = request.json
        conn.execute('UPDATE buses SET bus_number=?, bus_name=?, route_id=?, current_latitude=?, current_longitude=?, status=?, operator=?, service_type=?, data_source=? WHERE id=?',
                     (data['bus_number'], data.get('bus_name'), data['route_id'], data['current_latitude'], data['current_longitude'], data['status'], data.get('operator'), data.get('service_type'), data.get('data_source', 'OFFICIAL'), id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    elif request.method == 'DELETE':
        conn.execute('DELETE FROM buses WHERE id=?', (id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
"""

    block2 = """
    conn = get_db()
    conductor = conn.execute("SELECT * FROM conductors WHERE phone=? AND password=?", (phone, password)).fetchone()
    conn.close()
    if conductor:
        session['conductor_id'] = conductor['id']
        session['conductor_name'] = conductor['name']
        return redirect(url_for('conductor_dashboard'))
    return "Invalid credentials", 401

@app.route('/conductor/logout')
def conductor_logout():
    session.pop('conductor_id', None)
    return redirect(url_for('conductor_login'))

@app.route('/conductor/dashboard')
def conductor_dashboard():
    if 'conductor_id' not in session:
        return redirect(url_for('conductor_login'))
    return render_template('conductor_dashboard.html', conductor_name=session['conductor_name'])
"""

    out = []
    in_block1 = False
    in_block2 = False
    for line in lines:
        if "# MISSING LINE 51" in line:
            in_block1 = True
            out.append(block1)
        elif "# MISSING LINE 321" in line:
            in_block2 = True
            out.append(block2)
        elif "# MISSING LINE" in line:
            continue
        else:
            out.append(line)

    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(out)

if __name__ == '__main__':
    patch_app_py()
