from flask import Flask, render_template, request, jsonify
import database

app = Flask(__name__)

# Initialize the database and create tables if they don't exist
database.init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

# Helper function to get database connection
def get_db():
    return database.get_db_connection()

# ==========================================
# REST API ENDPOINTS
# ==========================================

# --- ROUTES API ---
@app.route('/api/routes', methods=['GET'])
def get_routes():
    conn = get_db()
    routes = conn.execute('SELECT * FROM routes').fetchall()
    conn.close()
    return jsonify([dict(row) for row in routes])

@app.route('/api/routes', methods=['POST'])
def add_route():
    data = request.json
    conn = get_db()
    cursor = conn.execute('INSERT INTO routes (route_name, source, destination, operator, service_type, data_source) VALUES (?, ?, ?, ?, ?, ?)',
                         (data['route_name'], data['source'], data['destination'], data.get('operator'), data.get('service_type'), data.get('data_source', 'OFFICIAL')))
    conn.commit()
    conn.close()
    return jsonify({'id': cursor.lastrowid, 'message': 'Route added successfully'})

@app.route('/api/routes/<int:id>', methods=['PUT'])
def update_route(id):
    data = request.json
    conn = get_db()
    conn.execute('UPDATE routes SET route_name=?, source=?, destination=?, operator=?, service_type=?, data_source=? WHERE id=?',
                 (data['route_name'], data['source'], data['destination'], data.get('operator'), data.get('service_type'), data.get('data_source', 'OFFICIAL'), id))
    conn.commit()
    conn.close()
# MISSING LINE 51
# MISSING LINE 52
# MISSING LINE 53
# MISSING LINE 54
# MISSING LINE 55
# MISSING LINE 56
# MISSING LINE 57
# MISSING LINE 58
# MISSING LINE 59
# MISSING LINE 60
# MISSING LINE 61
# MISSING LINE 62
# MISSING LINE 63
# MISSING LINE 64
# MISSING LINE 65
# MISSING LINE 66
# MISSING LINE 67
# MISSING LINE 68
# MISSING LINE 69
# MISSING LINE 70
# MISSING LINE 71
# MISSING LINE 72
# MISSING LINE 73
# MISSING LINE 74
# MISSING LINE 75
# MISSING LINE 76
# MISSING LINE 77
# MISSING LINE 78
# MISSING LINE 79
# MISSING LINE 80
# MISSING LINE 81
# MISSING LINE 82
# MISSING LINE 83
# MISSING LINE 84
# MISSING LINE 85
# MISSING LINE 86
# MISSING LINE 87
# MISSING LINE 88
# MISSING LINE 89
# MISSING LINE 90
# MISSING LINE 91
# MISSING LINE 92
# MISSING LINE 93
# MISSING LINE 94
# MISSING LINE 95
# MISSING LINE 96
# MISSING LINE 97
# MISSING LINE 98
# MISSING LINE 99
# MISSING LINE 100
# MISSING LINE 101
# MISSING LINE 102
# MISSING LINE 103
# MISSING LINE 104
# MISSING LINE 105
# MISSING LINE 106
# MISSING LINE 107
# MISSING LINE 108
# MISSING LINE 109
# MISSING LINE 110
# MISSING LINE 111
# MISSING LINE 112
# MISSING LINE 113
# MISSING LINE 114
# MISSING LINE 115
# MISSING LINE 116
# MISSING LINE 117
# MISSING LINE 118
# MISSING LINE 119
# MISSING LINE 120
# MISSING LINE 121
# MISSING LINE 122
# MISSING LINE 123
# MISSING LINE 124
# MISSING LINE 125
# MISSING LINE 126
# MISSING LINE 127
# MISSING LINE 128
# MISSING LINE 129
# MISSING LINE 130
# MISSING LINE 131
# MISSING LINE 132
# MISSING LINE 133
# MISSING LINE 134
# MISSING LINE 135
# MISSING LINE 136
# MISSING LINE 137
# MISSING LINE 138
# MISSING LINE 139
# MISSING LINE 140
# MISSING LINE 141
# MISSING LINE 142
# MISSING LINE 143
# MISSING LINE 144
# MISSING LINE 145
# MISSING LINE 146
# MISSING LINE 147
# MISSING LINE 148
# MISSING LINE 149
# ==========================================
from datetime import datetime, timedelta
import math

@app.route('/api/tracking_data', methods=['GET'])
def get_tracking_data():
    conn = get_db()
    buses = conn.execute('SELECT * FROM buses').fetchall()
    stops = conn.execute('SELECT * FROM stops ORDER BY route_id, stop_order').fetchall()
    routes = conn.execute('SELECT * FROM routes').fetchall()
    service_updates = conn.execute('SELECT * FROM service_updates ORDER BY created_at DESC LIMIT 5').fetchall()
    
    # Fetch latest arrivals for each bus to get ATA/Delay info
    arrivals = conn.execute('''
        SELECT a.*, s.stop_name 
        FROM arrivals a
        JOIN stops s ON a.stop_id = s.id
        WHERE a.id IN (SELECT MAX(id) FROM arrivals GROUP BY bus_id)
    ''').fetchall()
    conn.close()
    
    return jsonify({
        'buses': [dict(b) for b in buses],
        'stops': [dict(s) for s in stops],
        'routes': [dict(r) for r in routes],
        'updates': [dict(u) for u in service_updates],
        'latest_arrivals': {a['bus_id']: dict(a) for a in arrivals}
    })

def calculate_distance(lat1, lon1, lat2, lon2):
    # Simple Euclidean distance for demo simulation
    return math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2)

@app.route('/api/simulate/move/<int:bus_id>', methods=['POST'])
def simulate_move(bus_id):
    conn = get_db()
    bus = conn.execute('SELECT * FROM buses WHERE id=?', (bus_id,)).fetchone()
    if not bus:
        return jsonify({'error': 'Bus not found'}), 404
        
    route_id = bus['route_id']
    if not route_id:
        return jsonify({'error': 'Bus has no route assigned'}), 400
        
    stops = conn.execute('SELECT * FROM stops WHERE route_id=? ORDER BY stop_order', (route_id,)).fetchall()
    if not stops:
        return jsonify({'error': 'No stops found for this route'}), 400
        
    next_stop_id = bus['next_stop_id']
    
    # Assign target stop
    if not next_stop_id:
        target_stop = stops[0]
    else:
        target_stop = next((s for s in stops if s['id'] == next_stop_id), stops[0])
             
    current_lat, current_lon = bus['current_latitude'], bus['current_longitude']
    target_lat, target_lon = target_stop['latitude'], target_stop['longitude']
    else:
        target_stop = next((s for s in stops if s['id'] == next_stop_id), stops[0])
             
    current_lat, current_lon = bus['current_latitude'], bus['current_longitude']
    target_lat, target_lon = target_stop['latitude'], target_stop['longitude']
    
    distance = calculate_distance(current_lat, current_lon, target_lat, target_lon)
    STEP = 0.0003 # Map units to move per tick
    
    arrived = False
    if distance <= STEP:
        arrived = True
        new_lat, new_lon = target_lat, target_lon
    else:
        ratio = STEP / distance
        new_lat = current_lat + (target_lat - current_lat) * ratio
        new_lon = current_lon + (target_lon - current_lon) * ratio
        
    # Calculate simple ETA
    ticks_remaining = distance / STEP
    eta_time = (datetime.now() + timedelta(seconds=ticks_remaining)).strftime("%H:%M:%S")
    
    if arrived:
                     (new_lat, new_lon, new_next_stop_id, bus_id))
                     
        ata_time = datetime.now().strftime("%H:%M:%S")
        import random
        delay = random.choice([0, 0, 0, 2, 5, -1]) # Demo delay
        
        conn.execute('INSERT INTO arrivals (bus_id, stop_id, eta, ata, delay_minutes) VALUES (?, ?, ?, ?, ?)',
                     (bus_id, target_stop['id'], eta_time, ata_time, delay))
    else:
        conn.execute('UPDATE buses SET current_latitude=?, current_longitude=?, next_stop_id=? WHERE id=?',
                     (new_lat, new_lon, target_stop['id'], bus_id))

    conn.commit()
    conn.close()
    
    return jsonify({
        'arrived': arrived, 'new_lat': new_lat, 'new_lon': new_lon,
        'eta': eta_time, 'target_stop_name': target_stop['stop_name']
    })
    
    return jsonify({
        'arrived': arrived, 'new_lat': new_lat, 'new_lon': new_lon,
        'eta': eta_time, 'target_stop_name': target_stop['stop_name']
    })

# ==========================================
# STAGE 4: DRIVER & CONDUCTOR APIs
# ==========================================

@app.route('/driver/login', methods=['GET', 'POST'])
def driver_login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        conn = get_db()
        driver = conn.execute("SELECT * FROM drivers WHERE phone=? AND password=?", (phone, password)).fetchone()
        conn.close()
        if driver:
            session['driver_id'] = driver['id']
            session['driver_name'] = driver['name']
            return redirect(url_for('driver_dashboard'))
        return "Invalid credentials", 401
    return render_template('driver_login.html')

@app.route('/driver/logout')
def driver_logout():
    session.pop('driver_id', None)
    return redirect(url_for('driver_login'))

@app.route('/driver/dashboard')
def driver_dashboard():
    if 'driver_id' not in session:
        return redirect(url_for('driver_login'))
    
    conn = get_db()
    # Check if driver has an active trip
    trip = conn.execute("SELECT t.*, b.bus_number, b.bus_name, b.operator, b.service_type, r.route_name FROM trips t JOIN buses b ON t.bus_id = b.id LEFT JOIN routes r ON t.route_id = r.id WHERE t.driver_id=? AND t.status='Active'", (session['driver_id'],)).fetchone()
    conn.close()
    
    return render_template('driver_dashboard.html', driver_name=session['driver_name'], trip=trip)

@app.route('/api/bus/by-number/<bus_number>', methods=['GET'])
def get_bus_by_number(bus_number):
    conn = get_db()
    bus = conn.execute('''
        SELECT b.id as bus_id, b.bus_number, b.bus_name, b.operator, b.service_type, b.status, 
               r.id as route_id, r.route_name, r.source, r.destination 
        FROM buses b 
        LEFT JOIN routes r ON b.route_id = r.id 
        WHERE b.bus_number=? COLLATE NOCASE
    ''', (bus_number,)).fetchone()
    conn.close()
    
    if bus:
        return jsonify(dict(bus))
    else:
        return jsonify({'error': 'Bus not found. Please check the bus number or contact the administrator.'}), 404

@app.route('/conductor/login', methods=['GET', 'POST'])
def conductor_login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        conn = get_db()
        conductor = conn.execute("SELECT * FROM conductors WHERE phone=? AND password=?", (phone, password)).fetchone()
    trip = None
    if bus:
        trip = conn.execute("SELECT * FROM trips WHERE bus_id=? AND status='Active'", (bus['id'],)).fetchone()
    conn.close()
    
# MISSING LINE 321
# MISSING LINE 322
# MISSING LINE 323
# MISSING LINE 324
# MISSING LINE 325
# MISSING LINE 326
# MISSING LINE 327
# MISSING LINE 328
# MISSING LINE 329
# MISSING LINE 330
# MISSING LINE 331
# MISSING LINE 332
# MISSING LINE 333
# MISSING LINE 334
# MISSING LINE 335
# MISSING LINE 336
# MISSING LINE 337
# MISSING LINE 338
# MISSING LINE 339
# MISSING LINE 340
# MISSING LINE 341
# MISSING LINE 342
# MISSING LINE 343
# MISSING LINE 344
def start_trip():
    if 'driver_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json
    bus_id = data.get('bus_id')
    
    conn = get_db()
    # Ensure bus exists and get route
    bus = conn.execute("SELECT route_id FROM buses WHERE id=?", (bus_id,)).fetchone()
    if not bus:
        conn.close()
        return jsonify({'error': 'Bus not found'}), 404
        
    cursor = conn.execute("INSERT INTO trips (bus_id, driver_id, route_id, status) VALUES (?, ?, ?, 'Active')", (bus_id, session['driver_id'], bus['route_id']))
    trip_id = cursor.lastrowid
    
    # Mark bus as LIVE
    conn.execute("UPDATE buses SET gps_source='Real', status='Active Trip' WHERE id=?", (bus_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Trip started', 'trip_id': trip_id})

        return jsonify({'error': 'This bus is already on an active trip.'}), 400
        
    cursor = conn.execute("INSERT INTO trips (bus_id, driver_id, route_id, status) VALUES (?, ?, ?, 'Active')", (bus_id, session['driver_id'], bus['route_id']))
    trip_id = cursor.lastrowid
    
    # Mark bus as LIVE
    conn.execute("UPDATE buses SET gps_source='Real', status='Active Trip' WHERE id=?", (bus_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Trip started', 'trip_id': trip_id})

@app.route('/api/driver/end-trip', methods=['POST'])
def end_trip():
    if 'driver_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json
    trip_id = data.get('trip_id')
    
    conn = get_db()
    conn.execute("UPDATE trips SET status='Completed', end_time=CURRENT_TIMESTAMP WHERE id=?", (trip_id,))
    
    # Revert bus status
    trip = conn.execute("SELECT bus_id FROM trips WHERE id=?", (trip_id,)).fetchone()
    if trip:
        conn.execute("UPDATE buses SET gps_source='Simulated', status='Idle' WHERE id=?", (trip['bus_id'],))
        
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Trip ended'})
    
    if not all([trip_id, bus_id, lat, lon]):
        return jsonify({'error': 'Missing data'}), 400
        
    conn = get_db()
    # Log the location
    conn.execute("INSERT INTO live_locations (trip_id, bus_id, latitude, longitude, accuracy) VALUES (?, ?, ?, ?, ?)",
                 (trip_id, bus_id, lat, lon, acc))
                 
    # ---- ETA FOUNDATION & NEXT STOP CALCULATION ----
    bus = conn.execute("SELECT route_id, next_stop_id FROM buses WHERE id=?", (bus_id,)).fetchone()
    if bus and bus['route_id']:
        stops = conn.execute("SELECT id, latitude, longitude, stop_order FROM stops WHERE route_id=? ORDER BY stop_order", (bus['route_id'],)).fetchall()
        if stops:
            # Simple heuristic: find the closest stop that hasn't been passed
            # For this foundation, we just find the absolute closest stop. 
            # If the closest stop is < 500m (approx 0.005 degrees), we assume arrived and target the next one.
            closest_stop = stops[0]
            min_dist = float('inf')
            
            for s in stops:
                dist = calculate_distance(lat, lon, s['latitude'], s['longitude'])
                if dist < min_dist:
                    min_dist = dist
                    closest_stop = s
                    
            next_stop_id = closest_stop['id']
            
            # If we are very close to the closest stop, target the next one in sequence
    conn.execute("INSERT INTO live_locations (trip_id, bus_id, latitude, longitude, accuracy) VALUES (?, ?, ?, ?, ?)",
                 (trip_id, bus_id, lat, lon, acc))
                 
    # ---- ETA FOUNDATION & NEXT STOP CALCULATION ----
    bus = conn.execute("SELECT route_id, next_stop_id FROM buses WHERE id=?", (bus_id,)).fetchone()
    if bus and bus['route_id']:
        stops = conn.execute("SELECT id, latitude, longitude, stop_order FROM stops WHERE route_id=? ORDER BY stop_order", (bus['route_id'],)).fetchall()
        if stops:
            # Simple heuristic: find the closest stop that hasn't been passed
            # For this foundation, we just find the absolute closest stop. 
            # If the closest stop is < 500m (approx 0.005 degrees), we assume arrived and target the next one.
            closest_stop = stops[0]
            min_dist = float('inf')
            
            for s in stops:
                dist = calculate_distance(lat, lon, s['latitude'], s['longitude'])
                if dist < min_dist:
                    min_dist = dist
                    closest_stop = s
                    
            next_stop_id = closest_stop['id']
            
            # If we are very close to the closest stop, target the next one in sequence
            if min_dist < 0.5: 
                curr_idx = stops.index(closest_stop)
                if curr_idx + 1 < len(stops):
                    next_stop_id = stops[curr_idx + 1]['id']
            
            # Update bus current location and next stop
            conn.execute("UPDATE buses SET current_latitude=?, current_longitude=?, next_stop_id=? WHERE id=?", (lat, lon, next_stop_id, bus_id))
        else:
            conn.execute("UPDATE buses SET current_latitude=?, current_longitude=? WHERE id=?", (lat, lon, bus_id))
    else:
        conn.execute("UPDATE buses SET current_latitude=?, current_longitude=? WHERE id=?", (lat, lon, bus_id))

    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Location updated'})

if __name__ == '__main__':
