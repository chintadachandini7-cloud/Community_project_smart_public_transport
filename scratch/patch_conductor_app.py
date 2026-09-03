with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_dashboard = """@app.route('/conductor/dashboard')
def conductor_dashboard():
    if 'conductor_id' not in session:
        return redirect(url_for('conductor_login'))
    return render_template('conductor_dashboard.html', conductor_name=session['conductor_name'])"""

new_dashboard = """@app.route('/conductor/dashboard')
def conductor_dashboard():
    if 'conductor_id' not in session:
        return redirect(url_for('conductor_login'))
    
    conn = get_db()
    # Check if conductor has an active trip
    trip = conn.execute('''
        SELECT t.*, b.bus_number, b.bus_name, b.operator, b.service_type, b.delay_status, b.delay_minutes, r.route_name 
        FROM trips t 
        JOIN buses b ON t.bus_id = b.id 
        LEFT JOIN routes r ON t.route_id = r.id 
        WHERE t.conductor_id=? AND t.status='Active'
    ''', (session['conductor_id'],)).fetchone()
    conn.close()
    
    return render_template('conductor_dashboard.html', conductor_name=session['conductor_name'], trip=trip)

@app.route('/api/conductor/join-trip', methods=['POST'])
def conductor_join_trip():
    if 'conductor_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    bus_id = request.json.get('bus_id')
    if not bus_id:
        return jsonify({'error': 'Bus ID is required'}), 400
        
    conn = get_db()
    
    # Check if conductor is already on an active trip
    existing = conn.execute("SELECT id FROM trips WHERE conductor_id=? AND status='Active'", (session['conductor_id'],)).fetchone()
    if existing:
        conn.close()
        return jsonify({'error': 'You are already assigned to an active trip.'}), 400
        
    # Check if bus has an active trip
    trip = conn.execute("SELECT id, conductor_id FROM trips WHERE bus_id=? AND status='Active'", (bus_id,)).fetchone()
    if not trip:
        conn.close()
        return jsonify({'error': 'No active trip found for this bus. Please wait for the driver to start the trip.'}), 404
        
    if trip['conductor_id'] and trip['conductor_id'] != session['conductor_id']:
        conn.close()
        return jsonify({'error': 'Another conductor is already assigned to this trip.'}), 400
        
    conn.execute("UPDATE trips SET conductor_id=? WHERE id=?", (session['conductor_id'], trip['id']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Joined trip successfully.'})

@app.route('/api/conductor/leave-trip', methods=['POST'])
def conductor_leave_trip():
    if 'conductor_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    conn = get_db()
    conn.execute("UPDATE trips SET conductor_id=NULL WHERE conductor_id=? AND status='Active'", (session['conductor_id'],))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Left trip successfully.'})
"""

code = code.replace(old_dashboard, new_dashboard)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
    
print("Updated app.py!")
