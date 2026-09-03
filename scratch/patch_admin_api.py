import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Helper block for validation
validation_code = """
def validate_bus_data(data, conn, is_update=False, bus_id=None):
    if data.get('data_source') == 'OFFICIAL' and data.get('operator') not in ['APSRTC', 'TGSRTC']:
        return "OFFICIAL data must have operator APSRTC or TGSRTC"
    
    # Unique bus_number check
    if is_update:
        b = conn.execute('SELECT id FROM buses WHERE bus_number=? AND id!=?', (data['bus_number'], bus_id)).fetchone()
    else:
        b = conn.execute('SELECT id FROM buses WHERE bus_number=?', (data['bus_number'],)).fetchone()
    if b: return "Bus number must be unique"
    
    # Check route exists
    if not conn.execute('SELECT id FROM routes WHERE id=?', (data['route_id'],)).fetchone():
        return "Route does not exist"
        
    try:
        lat = float(data.get('current_latitude', 0))
        lng = float(data.get('current_longitude', 0))
        if not (-90 <= lat <= 90): return "Latitude must be between -90 and 90"
        if not (-180 <= lng <= 180): return "Longitude must be between -180 and 180"
    except:
        return "Invalid latitude or longitude"
    return None

def validate_route_data(data):
    if data.get('data_source') == 'OFFICIAL' and data.get('operator') not in ['APSRTC', 'TGSRTC']:
        return "OFFICIAL data must have operator APSRTC or TGSRTC"
    return None

def validate_stop_data(data, conn):
    if data.get('data_source') == 'OFFICIAL' and not data.get('scheduled_arrival_time'):
        pass # Not strictly required by prompt but good practice
        
    if not conn.execute('SELECT id FROM routes WHERE id=?', (data['route_id'],)).fetchone():
        return "Route does not exist"
        
    try:
        if int(data.get('stop_order', 0)) <= 0: return "Stop order must be > 0"
    except: return "Invalid stop order"
    
    try:
        lat = float(data.get('latitude', 0))
        lng = float(data.get('longitude', 0))
        if not (-90 <= lat <= 90): return "Latitude must be between -90 and 90"
        if not (-180 <= lng <= 180): return "Longitude must be between -180 and 180"
    except:
        return "Invalid latitude or longitude"
    return None

"""

code = code.replace("# ==========================================\n\n# --- ROUTES API ---", validation_code + "\n# ==========================================\n\n# --- ROUTES API ---")

# Replace Routes POST
old_route_post = """@app.route('/api/routes', methods=['POST'])
def add_route():
    data = request.json
    conn = get_db()
    cursor = conn.execute('INSERT INTO routes (route_name, source, destination, operator, service_type, data_source) VALUES (?, ?, ?, ?, ?, ?)',
                         (data['route_name'], data['source'], data['destination'], data.get('operator'), data.get('service_type'), data.get('data_source', 'OFFICIAL')))
    conn.commit()
    conn.close()
    return jsonify({'id': cursor.lastrowid, 'message': 'Route added successfully'})"""

new_route_post = """@app.route('/api/routes', methods=['POST'])
def add_route():
    data = request.json
    err = validate_route_data(data)
    if err: return jsonify({'error': err}), 400
    conn = get_db()
    cursor = conn.execute('INSERT INTO routes (route_name, source, destination, operator, service_type, data_source) VALUES (?, ?, ?, ?, ?, ?)',
                         (data['route_name'], data['source'], data['destination'], data.get('operator'), data.get('service_type'), data.get('data_source', 'DEMO')))
    conn.commit()
    conn.close()
    return jsonify({'id': cursor.lastrowid, 'message': 'Route added successfully'})"""
code = code.replace(old_route_post, new_route_post)

# Replace Routes PUT
old_route_put = """@app.route('/api/routes/<int:id>', methods=['PUT'])
def update_route(id):
    data = request.json
    conn = get_db()
    conn.execute('UPDATE routes SET route_name=?, source=?, destination=?, operator=?, service_type=?, data_source=? WHERE id=?',
                 (data['route_name'], data['source'], data['destination'], data.get('operator'), data.get('service_type'), data.get('data_source', 'OFFICIAL'), id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})"""
    
new_route_put = """@app.route('/api/routes/<int:id>', methods=['PUT'])
def update_route(id):
    data = request.json
    err = validate_route_data(data)
    if err: return jsonify({'error': err}), 400
    conn = get_db()
    conn.execute('UPDATE routes SET route_name=?, source=?, destination=?, operator=?, service_type=?, data_source=? WHERE id=?',
                 (data['route_name'], data['source'], data['destination'], data.get('operator'), data.get('service_type'), data.get('data_source', 'DEMO'), id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})"""
code = code.replace(old_route_put, new_route_put)

# Replace Stops POST
old_stop_post = """    else:
        data = request.json
        conn.execute('INSERT INTO stops (route_id, stop_name, latitude, longitude, stop_order, area_type, data_source) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (data['route_id'], data['stop_name'], data['latitude'], data['longitude'], data['stop_order'], data.get('area_type'), data.get('data_source', 'OFFICIAL')))
        conn.commit()
        conn.close()
        return jsonify({'success': True})"""
new_stop_post = """    else:
        data = request.json
        err = validate_stop_data(data, conn)
        if err:
            conn.close()
            return jsonify({'error': err}), 400
        conn.execute('INSERT INTO stops (route_id, stop_name, latitude, longitude, stop_order, area_type, scheduled_arrival_time, data_source) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                     (data['route_id'], data['stop_name'], data['latitude'], data['longitude'], data['stop_order'], data.get('area_type'), data.get('scheduled_arrival_time'), data.get('data_source', 'DEMO')))
        conn.commit()
        conn.close()
        return jsonify({'success': True})"""
code = code.replace(old_stop_post, new_stop_post)

# Replace Stops PUT
old_stop_put = """    if request.method == 'PUT':
        data = request.json
        conn.execute('UPDATE stops SET route_id=?, stop_name=?, latitude=?, longitude=?, stop_order=?, area_type=?, data_source=? WHERE id=?',
                     (data['route_id'], data['stop_name'], data['latitude'], data['longitude'], data['stop_order'], data.get('area_type'), data.get('data_source', 'OFFICIAL'), id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})"""
new_stop_put = """    if request.method == 'PUT':
        data = request.json
        err = validate_stop_data(data, conn)
        if err:
            conn.close()
            return jsonify({'error': err}), 400
        conn.execute('UPDATE stops SET route_id=?, stop_name=?, latitude=?, longitude=?, stop_order=?, area_type=?, scheduled_arrival_time=?, data_source=? WHERE id=?',
                     (data['route_id'], data['stop_name'], data['latitude'], data['longitude'], data['stop_order'], data.get('area_type'), data.get('scheduled_arrival_time'), data.get('data_source', 'DEMO'), id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})"""
code = code.replace(old_stop_put, new_stop_put)

# Replace Buses POST
old_bus_post = """    else:
        data = request.json
        conn.execute('INSERT INTO buses (bus_number, bus_name, route_id, current_latitude, current_longitude, status, operator, service_type, data_source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     (data['bus_number'], data.get('bus_name'), data['route_id'], data['current_latitude'], data['current_longitude'], data['status'], data.get('operator'), data.get('service_type'), data.get('data_source', 'OFFICIAL')))
        conn.commit()
        conn.close()
        return jsonify({'success': True})"""
new_bus_post = """    else:
        data = request.json
        err = validate_bus_data(data, conn)
        if err:
            conn.close()
            return jsonify({'error': err}), 400
        conn.execute('INSERT INTO buses (bus_number, bus_name, route_id, current_latitude, current_longitude, status, operator, service_type, data_source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     (data['bus_number'], data.get('bus_name'), data['route_id'], data['current_latitude'], data['current_longitude'], data['status'], data.get('operator'), data.get('service_type'), data.get('data_source', 'DEMO')))
        conn.commit()
        conn.close()
        return jsonify({'success': True})"""
code = code.replace(old_bus_post, new_bus_post)

# Replace Buses PUT
old_bus_put = """    if request.method == 'PUT':
        data = request.json
        conn.execute('UPDATE buses SET bus_number=?, bus_name=?, route_id=?, current_latitude=?, current_longitude=?, status=?, operator=?, service_type=?, data_source=? WHERE id=?',
                     (data['bus_number'], data.get('bus_name'), data['route_id'], data['current_latitude'], data['current_longitude'], data['status'], data.get('operator'), data.get('service_type'), data.get('data_source', 'OFFICIAL'), id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})"""
new_bus_put = """    if request.method == 'PUT':
        data = request.json
        err = validate_bus_data(data, conn, is_update=True, bus_id=id)
        if err:
            conn.close()
            return jsonify({'error': err}), 400
        conn.execute('UPDATE buses SET bus_number=?, bus_name=?, route_id=?, current_latitude=?, current_longitude=?, status=?, operator=?, service_type=?, data_source=? WHERE id=?',
                     (data['bus_number'], data.get('bus_name'), data['route_id'], data['current_latitude'], data['current_longitude'], data['status'], data.get('operator'), data.get('service_type'), data.get('data_source', 'DEMO'), id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})"""
code = code.replace(old_bus_put, new_bus_put)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Patched app.py")
