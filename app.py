import os
import uuid
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import database

app = Flask(__name__)
app.secret_key = 'your-existing-project-secret'

# Admin email whitelist — add your Google emails here
ADMIN_EMAILS = ['chintadachandini2408@gmail.com']

# Initialize the database and create tables if they don't exist
database.init_db()

# ==========================================
# AUTHENTICATION & LOGIN
# ==========================================

@app.route('/login', strict_slashes=False)
def login_page():
    firebase_config = {
        'apiKey': os.environ.get('FIREBASE_API_KEY', 'AIzaSyDCnxBTdeIZg8oArIh8rRNorm6qaN1EdTU'),
        'authDomain': os.environ.get('FIREBASE_AUTH_DOMAIN', 'smarttransportsystem-5c58c.firebaseapp.com'),
        'projectId': os.environ.get('FIREBASE_PROJECT_ID', 'smarttransportsystem-5c58c'),
        'storageBucket': os.environ.get('FIREBASE_STORAGE_BUCKET', 'smarttransportsystem-5c58c.firebasestorage.app'),
        'messagingSenderId': os.environ.get('FIREBASE_MESSAGING_SENDER_ID', '317309847125'),
        'appId': os.environ.get('FIREBASE_APP_ID', '1:317309847125:web:f13b8676f7c30b061d76dc'),
        'measurementId': os.environ.get('FIREBASE_MEASUREMENT_ID', 'G-3HQ7DH4LCY')
    }
    supabase_url = os.environ.get('SUPABASE_URL', 'https://vqbachaigfcxcjqcbisa.supabase.co')
    supabase_anon_key = os.environ.get('SUPABASE_ANON_KEY', '')
    return render_template('login.html', 
                           firebase_config=firebase_config,
                           supabase_url=supabase_url, 
                           supabase_anon_key=supabase_anon_key)

@app.route('/auth/callback', strict_slashes=False)
def auth_callback():
    supabase_url = os.environ.get('SUPABASE_URL', 'https://vqbachaigfcxcjqcbisa.supabase.co')
    supabase_anon_key = os.environ.get('SUPABASE_ANON_KEY', '')
    return render_template('auth_callback.html', supabase_url=supabase_url, supabase_anon_key=supabase_anon_key)

@app.route('/api/auth/set-session', methods=['POST'])
def set_session():
    data = request.json or {}
    user_id = data.get('user_id')
    email = (data.get('email') or '').strip().lower()
    role = (data.get('role') or '').lower()
    name = data.get('name', email)
    
    # Check admin whitelist
    if email in [e.lower() for e in ADMIN_EMAILS] and role == 'admin':
        role = 'admin'

    # Server-side verification from Supabase profiles
    sb = database.get_supabase()
    if sb and user_id:
        try:
            prof = sb.table('profiles').select('*').eq('id', user_id).maybe_single().execute()
            if prof and prof.data:
                db_role = (prof.data.get('role') or '').lower()
                if db_role and not (email in [e.lower() for e in ADMIN_EMAILS] and role == 'admin'):
                    role = db_role
                email = prof.data.get('email', email)
                name = prof.data.get('full_name', name)
            else:
                # Upsert profile record
                sb.table('profiles').upsert({
                    'id': user_id,
                    'email': email,
                    'full_name': name,
                    'role': role
                }).execute()
        except Exception as e:
            print("Server-side profile verification notice:", e)

    session['user_role'] = role
    session['user_email'] = email
    session['user_name'] = name
    session['user_id'] = user_id

    if role == 'driver':
        session['driver_id'] = user_id
        session['driver_name'] = name
    elif role == 'conductor':
        session['conductor_id'] = user_id
        session['conductor_name'] = name
    elif role in ['user', 'passenger']:
        session['passenger_id'] = user_id

    return jsonify({'success': True})

def sync_profile(sb, email, name, role, uid=None):
    if not sb or not email:
        return
    try:
        prof = sb.table('profiles').select('id').eq('email', email).maybe_single().execute()
        if prof and prof.data:
            sb.table('profiles').update({'role': role, 'full_name': name}).eq('id', prof.data['id']).execute()
        else:
            try:
                new_u = sb.auth.admin.create_user({
                    'email': email,
                    'email_confirm': True,
                    'user_metadata': {'full_name': name, 'role': role}
                })
                if new_u and new_u.user:
                    sb.table('profiles').upsert({'id': new_u.user.id, 'email': email, 'full_name': name, 'role': role}).execute()
            except Exception as auth_err:
                try:
                    users = sb.auth.admin.list_users()
                    for u in users:
                        if (u.email or '').lower() == email.lower():
                            sb.table('profiles').upsert({'id': u.id, 'email': email, 'full_name': name, 'role': role}).execute()
                            break
                except Exception:
                    pass
    except Exception as e:
        print(f"Profile sync notice for {role}:", e)

@app.route('/auth/google', methods=['POST'])
def auth_google():
    data = request.json or {}
    role = (data.get('role') or 'passenger').lower()
    demo_mode = data.get('demo_mode', False)
    
    if demo_mode:
        demo_identities = {
            'passenger': {'email': 'demo_passenger@example.com', 'name': 'Demo Passenger'},
            'driver': {'email': 'demo_driver@example.com', 'name': 'Ramesh Kumar'},
            'conductor': {'email': 'demo_conductor@example.com', 'name': 'Srikanth Babu'},
            'admin': {'email': ADMIN_EMAILS[0], 'name': 'Admin User'},
        }
        identity = demo_identities.get(role, demo_identities['passenger'])
        email = identity['email']
        name = identity['name']
    else:
        email = (data.get('email') or '').strip()
        name = data.get('name', email)
        
        if not email:
            return jsonify({'success': False, 'error': 'No Google email provided'}), 400
    
    sb = database.get_supabase()
    
    try:
        if role == 'admin':
            if email.lower() not in [e.lower() for e in ADMIN_EMAILS] and not demo_mode:
                return jsonify({'success': False, 'error': f'This Google account ({email}) is not authorized for Administrator access.'}), 403
            
            sync_profile(sb, email, name, 'admin')
                    
            session['user_role'] = 'admin'
            session['user_email'] = email
            session['user_name'] = name
            return jsonify({'success': True, 'redirect': '/admin/dashboard'})
        
        elif role == 'driver':
            driver = None
            if sb:
                try:
                    r = sb.table('drivers').select('*').limit(1).execute()
                    driver = r.data[0] if r.data else None
                    sync_profile(sb, email, name, 'driver')
                except Exception as sb_err:
                    print("Supabase driver lookup notice:", sb_err)
            
            if not driver:
                try:
                    conn = get_db()
                    driver = conn.execute("SELECT * FROM drivers LIMIT 1").fetchone()
                    conn.close()
                except Exception as db_err:
                    print("Local driver lookup fallback notice:", db_err)
            
            d_id = driver['id'] if driver else str(uuid.uuid4())
            d_name = driver.get('driver_name', driver.get('name', name)) if isinstance(driver, dict) else (driver['name'] if driver and 'name' in driver.keys() else name)
            session['driver_id'] = str(d_id)
            session['driver_name'] = str(d_name)
            session['user_role'] = 'driver'
            session['user_email'] = email
            session['user_name'] = name
            return jsonify({'success': True, 'redirect': '/driver/dashboard'})
        
        elif role == 'conductor':
            conductor = None
            if sb:
                try:
                    r = sb.table('conductors').select('*').limit(1).execute()
                    conductor = r.data[0] if r.data else None
                    sync_profile(sb, email, name, 'conductor')
                except Exception as sb_err:
                    print("Supabase conductor lookup notice:", sb_err)
            
            if not conductor:
                try:
                    conn = get_db()
                    conductor = conn.execute("SELECT * FROM conductors LIMIT 1").fetchone()
                    conn.close()
                except Exception as db_err:
                    print("Local conductor lookup fallback notice:", db_err)
            
            c_id = conductor['id'] if conductor else str(uuid.uuid4())
            c_name = conductor.get('conductor_name', conductor.get('name', name)) if isinstance(conductor, dict) else (conductor['name'] if conductor and 'name' in conductor.keys() else name)
            session['conductor_id'] = str(c_id)
            session['conductor_name'] = str(c_name)
            session['user_role'] = 'conductor'
            session['user_email'] = email
            session['user_name'] = name
            return jsonify({'success': True, 'redirect': '/conductor/dashboard'})
        
        elif role in ['passenger', 'user']:
            session['user_role'] = 'passenger'
            session['user_email'] = email
            session['user_name'] = name
            return jsonify({'success': True, 'redirect': '/user/dashboard'})
        
        else:
            # Passenger — cloud-authenticated via Supabase, safe on Vercel
            passenger_id = str(uuid.uuid4())
            if sb:
                try:
                    prof = sb.table('profiles').select('*').eq('email', email).execute()
                    if prof.data:
                        passenger_id = str(prof.data[0]['id'])
                    else:
                        new_u = sb.auth.admin.create_user({
                            'email': email,
                            'email_confirm': True,
                            'user_metadata': {'full_name': name, 'role': 'user'}
                        })
                        passenger_id = str(new_u.user.id)
                except Exception as sb_err:
                    print("Supabase profile notice:", sb_err)
            
            session['passenger_id'] = passenger_id
            session['user_role'] = 'passenger'
            session['user_email'] = email
            session['user_name'] = name
            return jsonify({'success': True, 'redirect': '/'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

def get_role_redirect(role):
    redirects = {
        'passenger': '/user/dashboard',
        'user': '/user/dashboard',
        'driver': '/driver/dashboard',
        'conductor': '/conductor/dashboard',
        'admin': '/admin/dashboard',
    }
    return redirects.get(role, '/user/dashboard')

import uuid

# 1. Passenger / User Dashboard — NO authentication required!
@app.route('/user/dashboard', strict_slashes=False)
def user_dashboard():
    if 'passenger_id' not in session:
        session['passenger_id'] = str(uuid.uuid4())
    session['user_role'] = 'passenger'
    return render_template('index.html')

@app.route('/', strict_slashes=False)
def index():
    # If user has an active session, send to their dashboard; otherwise show login
    if 'user_role' in session:
        return redirect(get_role_redirect(session['user_role']))
    return redirect(url_for('login_page'))

# 4. Administrator Dashboard — Strictly protected by role = 'admin'
@app.route('/admin', strict_slashes=False)
@app.route('/admin/dashboard', strict_slashes=False)
def admin():
    if session.get('user_role') != 'admin':
        return redirect(url_for('login_page'))
    return render_template('admin.html')

# Helper function to get database connection
def get_db():
    return database.get_db_connection()


# ==========================================
# REST API ENDPOINTS

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
    err = validate_route_data(data)
    if err: return jsonify({'error': err}), 400
    conn = get_db()
    cursor = conn.execute('INSERT INTO routes (route_name, source, destination, operator, service_type, data_source) VALUES (?, ?, ?, ?, ?, ?)',
                         (data['route_name'], data['source'], data['destination'], data.get('operator'), data.get('service_type'), data.get('data_source', 'DEMO')))
    conn.commit()
    conn.close()
    return jsonify({'id': cursor.lastrowid, 'message': 'Route added successfully'})


@app.route('/api/routes/<int:id>', methods=['PUT'])
def update_route(id):
    data = request.json
    err = validate_route_data(data)
    if err: return jsonify({'error': err}), 400
    conn = get_db()
    conn.execute('UPDATE routes SET route_name=?, source=?, destination=?, operator=?, service_type=?, data_source=? WHERE id=?',
                 (data['route_name'], data['source'], data['destination'], data.get('operator'), data.get('service_type'), data.get('data_source', 'DEMO'), id))
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
        route_id = request.args.get('route_id', type=int)
        limit = request.args.get('limit', type=int)
        fetch_all = request.args.get('all', '').lower() in ('true', '1')

        if route_id:
            stops = conn.execute('SELECT s.*, r.route_name FROM stops s LEFT JOIN routes r ON s.route_id = r.id WHERE s.route_id=? ORDER BY s.stop_order', (route_id,)).fetchall()
        elif fetch_all:
            stops = conn.execute('SELECT s.*, r.route_name FROM stops s LEFT JOIN routes r ON s.route_id = r.id ORDER BY s.route_id, s.stop_order').fetchall()
        elif limit:
            stops = conn.execute('SELECT s.*, r.route_name FROM stops s LEFT JOIN routes r ON s.route_id = r.id ORDER BY s.route_id, s.stop_order LIMIT ?', (limit,)).fetchall()
        else:
            stops = conn.execute('SELECT s.*, r.route_name FROM stops s LEFT JOIN routes r ON s.route_id = r.id ORDER BY s.route_id, s.stop_order LIMIT 100').fetchall()
        conn.close()
        return jsonify([dict(s) for s in stops])
    else:
        data = request.json
        err = validate_stop_data(data, conn)
        if err:
            conn.close()
            return jsonify({'error': err}), 400
        conn.execute('INSERT INTO stops (route_id, stop_name, latitude, longitude, stop_order, area_type, scheduled_arrival_time, data_source) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                     (data['route_id'], data['stop_name'], data['latitude'], data['longitude'], data['stop_order'], data.get('area_type'), data.get('scheduled_arrival_time'), data.get('data_source', 'DEMO')))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/api/stops/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def manage_stop(id):
    conn = get_db()
    if request.method == 'GET':
        # Treat <id> as a route_id and return ordered stops for that route
        stops = conn.execute(
            'SELECT s.*, r.route_name FROM stops s LEFT JOIN routes r ON s.route_id = r.id WHERE s.route_id=? ORDER BY s.stop_order',
            (id,)
        ).fetchall()
        conn.close()
        return jsonify([dict(s) for s in stops])
    elif request.method == 'PUT':
        data = request.json
        err = validate_stop_data(data, conn)
        if err:
            conn.close()
            return jsonify({'error': err}), 400
        conn.execute('UPDATE stops SET route_id=?, stop_name=?, latitude=?, longitude=?, stop_order=?, area_type=?, scheduled_arrival_time=?, data_source=? WHERE id=?',
                     (data['route_id'], data['stop_name'], data['latitude'], data['longitude'], data['stop_order'], data.get('area_type'), data.get('scheduled_arrival_time'), data.get('data_source', 'DEMO'), id))
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
    if request.method == 'GET':
        sb = database.get_supabase()
        if sb:
            try:
                res = sb.table('admin_bus_overview').select('*').execute()
                if res.data:
                    # Build route_name -> SQLite route_id + source/dest lookup for Leaflet stop fetching
                    route_id_lookup = {}
                    route_detail_lookup = {}
                    try:
                        lconn = get_db()
                        local_routes = lconn.execute('SELECT id, route_name, source, destination FROM routes').fetchall()
                        for lr in local_routes:
                            route_id_lookup[lr['route_name']] = lr['id']
                            route_detail_lookup[lr['route_name']] = {'source': lr['source'], 'destination': lr['destination']}
                        lconn.close()
                    except Exception:
                        pass

                    mapped = []
                    for b in res.data:
                        # Resolve route_id from local SQLite by matching route_name
                        route_name = b.get('route_name') or ''
                        local_route_id = route_id_lookup.get(route_name)
                        route_detail = route_detail_lookup.get(route_name, {})
                        # Also try partial match: "SOURCE - DESTINATION"
                        if not local_route_id:
                            for rn, rid in route_id_lookup.items():
                                if route_name and route_name in rn:
                                    local_route_id = rid
                                    route_detail = route_detail_lookup.get(rn, {})
                                    break
                        # Tokenized match if still not found
                        if not local_route_id and route_name and '-' in route_name:
                            parts = [p.strip().upper() for p in route_name.split('-') if p.strip()]
                            if len(parts) == 2:
                                for rn, detail in route_detail_lookup.items():
                                    s_up = detail.get('source', '').upper()
                                    d_up = detail.get('destination', '').upper()
                                    if (parts[0] in s_up or s_up in parts[0]) and (parts[1] in d_up or d_up in parts[1]):
                                        local_route_id = route_id_lookup.get(rn)
                                        route_detail = detail
                                        break

                        # Fallback source/destination from route_name if still empty
                        resolved_source = route_detail.get('source', '')
                        resolved_dest = route_detail.get('destination', '')
                        if not resolved_source and '-' in route_name:
                            name_parts = [p.strip() for p in route_name.split('-') if p.strip()]
                            if len(name_parts) >= 2:
                                resolved_source = name_parts[0]
                                resolved_dest = name_parts[1]

                        mapped.append({
                            'id': b.get('bus_id'),
                            'bus_number': b.get('bus_number'),
                            'bus_name': b.get('route_name') or b.get('bus_number'),
                            'route_name': b.get('route_name'),
                            'route_number': b.get('route_number'),
                            'route_id': local_route_id,
                            'source': resolved_source,
                            'destination': resolved_dest,
                            'operator': 'APSRTC' if 'AP' in (b.get('bus_number') or '') else 'TGSRTC',
                            'service_type': b.get('bus_type', 'Standard'),
                            'capacity': b.get('capacity', 40),
                            'status': b.get('bus_status', 'Active'),
                            'gps_source': 'Real' if b.get('latitude') else 'Simulated',
                            'current_latitude': b.get('latitude') or 16.5062,
                            'current_longitude': b.get('longitude') or 80.6480,
                            'current_stop': b.get('current_stop'),
                            'next_stop': b.get('next_stop'),
                            'next_stop_name': b.get('next_stop') or 'En route',
                            'speed': b.get('speed', 0),
                            'driver_name': b.get('driver_name'),
                            'driver_phone': b.get('driver_phone'),
                            'conductor_name': b.get('conductor_name'),
                            'conductor_phone': b.get('conductor_phone'),
                            'delay_status': 'ON TIME',
                            'delay_minutes': 0
                        })
                    return jsonify(mapped)
            except Exception as e:
                print("Supabase bus fetch fallback to local:", e)
                
        conn = get_db()
        buses = conn.execute('SELECT b.*, r.route_name, r.source, r.destination FROM buses b LEFT JOIN routes r ON b.route_id = r.id').fetchall()
        conn.close()
        return jsonify([dict(b) for b in buses])
    else:
        conn = get_db()
        data = request.json
        err = validate_bus_data(data, conn)
        if err:
            conn.close()
            return jsonify({'error': err}), 400
        conn.execute('INSERT INTO buses (bus_number, bus_name, route_id, current_latitude, current_longitude, status, operator, service_type, data_source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     (data['bus_number'], data.get('bus_name'), data['route_id'], data['current_latitude'], data['current_longitude'], data['status'], data.get('operator'), data.get('service_type'), data.get('data_source', 'DEMO')))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/api/buses/<int:id>', methods=['PUT', 'DELETE'])
def manage_bus(id):
    conn = get_db()
    if request.method == 'PUT':
        data = request.json
        err = validate_bus_data(data, conn, is_update=True, bus_id=id)
        if err:
            conn.close()
            return jsonify({'error': err}), 400
        conn.execute('UPDATE buses SET bus_number=?, bus_name=?, route_id=?, current_latitude=?, current_longitude=?, status=?, operator=?, service_type=?, data_source=? WHERE id=?',
                     (data['bus_number'], data.get('bus_name'), data['route_id'], data['current_latitude'], data['current_longitude'], data['status'], data.get('operator'), data.get('service_type'), data.get('data_source', 'DEMO'), id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    elif request.method == 'DELETE':
        conn.execute('DELETE FROM buses WHERE id=?', (id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
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
        'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
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
        conn.execute('UPDATE buses SET current_latitude=?, current_longitude=?, next_stop_id=? WHERE id=?',
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

@app.route('/driver/login', methods=['GET', 'POST'], strict_slashes=False)
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
            session['user_role'] = 'driver'
            return redirect(url_for('driver_dashboard'))
        return "Invalid credentials", 401
    return redirect(url_for('login_page'))

@app.route('/driver/logout')
def driver_logout():
    session.clear()
    return redirect(url_for('login_page'))

# 2. Driver Dashboard — Strictly protected by role = 'driver'
@app.route('/driver/dashboard')
def driver_dashboard():
    if session.get('user_role') != 'driver':
        return redirect(url_for('login_page', role='driver', error='unauthorized'))
    
    trip = None
    driver_id = session.get('driver_id')
    
    # 1. Try Supabase cloud database for active assignment
    sb = database.get_supabase()
    if sb and driver_id:
        try:
            assign = sb.table('bus_assignments').select('*, buses(*)').eq('driver_id', str(driver_id)).eq('status', 'Active').maybe_single().execute()
            if assign and assign.data and assign.data.get('buses'):
                b = assign.data['buses']
                r_name = b.get('route_name') or ''
                parts = [p.strip() for p in r_name.split('-')] if '-' in r_name else [r_name, '']
                trip = {
                    'id': assign.data.get('id'),
                    'bus_id': b.get('id'),
                    'bus_number': b.get('bus_number'),
                    'bus_name': b.get('route_name') or b.get('bus_number'),
                    'route_name': r_name,
                    'operator': 'APSRTC' if 'AP' in (b.get('bus_number') or '') else 'TGSRTC',
                    'service_type': b.get('bus_type', 'Standard'),
                    'start_time': assign.data.get('created_at', 'Active')
                }
        except Exception as sb_err:
            print("Supabase driver trip query notice:", sb_err)

    # 2. Local fallback
    if not trip:
        try:
            conn = get_db()
            if driver_id:
                trip = conn.execute("SELECT t.*, b.bus_number, b.bus_name, b.operator, b.service_type, r.route_name FROM trips t JOIN buses b ON t.bus_id = b.id LEFT JOIN routes r ON t.route_id = r.id WHERE t.driver_id=? AND t.status='Active'", (driver_id,)).fetchone()
            conn.close()
        except Exception as e:
            print("Driver trip query notice:", e)
    
    driver_name = session.get('driver_name', session.get('user_name', 'Driver'))
    return render_template('driver_dashboard.html', driver_name=driver_name, trip=trip)

@app.route('/api/health')
def api_health():
    sb = database.get_supabase()
    sb_connected = False
    sb_buses = 0
    if sb:
        try:
            r = sb.table('buses').select('id', count='exact').execute()
            sb_buses = len(r.data) if r and r.data else 0
            sb_connected = True
        except Exception as e:
            print("Health check Supabase notice:", e)
    return jsonify({
        'status': 'ok',
        'supabase_connected': sb_connected,
        'supabase_buses': sb_buses
    })

@app.route('/api/bus/by-number/<bus_number>', methods=['GET'])
def get_bus_by_number(bus_number):
    cleaned_no = bus_number.strip()
    normalized_target = cleaned_no.replace(' ', '').upper()

    # 1. First check Supabase cloud database
    sb = database.get_supabase()
    if sb:
        try:
            # Check all buses to handle both exact and space-insensitive matches (e.g. 'AP 16 Z 2209' vs 'AP16Z2209')
            res = sb.table('buses').select('*').execute()
            if res and res.data:
                for b in res.data:
                    b_no = (b.get('bus_number') or '').strip()
                    if b_no.upper() == cleaned_no.upper() or b_no.replace(' ', '').upper() == normalized_target:
                        route_name = b.get('route_name') or ''
                        parts = [p.strip() for p in route_name.split('-')] if '-' in route_name else [route_name, '']
                        src = parts[0] if len(parts) >= 1 else ''
                        dst = parts[1] if len(parts) >= 2 else ''
                        return jsonify({
                            'bus_id': b.get('id'),
                            'bus_number': b.get('bus_number'),
                            'bus_name': b.get('route_name') or b.get('bus_number'),
                            'operator': 'APSRTC' if 'AP' in (b.get('bus_number') or '') else 'TGSRTC',
                            'service_type': b.get('bus_type', 'Standard'),
                            'status': b.get('status', 'Active'),
                            'route_id': b.get('route_number'),
                            'route_name': route_name,
                            'source': src,
                            'destination': dst
                        })
        except Exception as sb_err:
            print("Supabase get_bus_by_number notice:", sb_err)

    # 2. Fallback to SQLite
    try:
        conn = get_db()
        buses = conn.execute('''
            SELECT b.id as bus_id, b.bus_number, b.bus_name, b.operator, b.service_type, b.status, 
                   r.id as route_id, r.route_name, r.source, r.destination 
            FROM buses b 
            LEFT JOIN routes r ON b.route_id = r.id
        ''').fetchall()
        conn.close()
        
        for bus in buses:
            b_no = (bus['bus_number'] or '').strip()
            if b_no.upper() == cleaned_no.upper() or b_no.replace(' ', '').upper() == normalized_target:
                return jsonify(dict(bus))
    except Exception as db_err:
        print("SQLite get_bus_by_number notice:", db_err)

    return jsonify({'error': 'Bus not found. Please check the bus number or contact the administrator.'}), 404

@app.route('/conductor/login', methods=['GET', 'POST'], strict_slashes=False)
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
            session['user_role'] = 'conductor'
            return redirect(url_for('conductor_dashboard'))
        return "Invalid credentials", 401
    return redirect(url_for('login_page'))

@app.route('/conductor/logout')
def conductor_logout():
    session.clear()
    return redirect(url_for('login_page'))

# 3. Conductor Dashboard — Strictly protected by role = 'conductor'
@app.route('/conductor/dashboard')
def conductor_dashboard():
    if session.get('user_role') != 'conductor':
        return redirect(url_for('login_page', role='conductor', error='unauthorized'))
    
    trip = None
    try:
        conn = get_db()
        conductor_id = session.get('conductor_id')
        if conductor_id:
            trip = conn.execute('''
                SELECT t.*, b.bus_number, b.bus_name, b.operator, b.service_type, b.delay_status, b.delay_minutes, r.route_name 
                FROM trips t 
                JOIN buses b ON t.bus_id = b.id 
                LEFT JOIN routes r ON t.route_id = r.id 
                WHERE t.conductor_id=? AND t.status='Active'
            ''', (conductor_id,)).fetchone()
        conn.close()
    except Exception as e:
        print("Conductor trip query notice:", e)
    
    conductor_name = session.get('conductor_name', session.get('user_name', 'Conductor'))
    return render_template('conductor_dashboard.html', conductor_name=conductor_name, trip=trip)

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

@app.route('/api/driver/start-trip', methods=['POST'])
def start_trip():
    if 'driver_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json or {}
    bus_id = data.get('bus_id')
    driver_id = session.get('driver_id')
    trip_id = None
    
    # 1. First update Supabase cloud database
    sb = database.get_supabase()
    if sb and bus_id:
        try:
            # Query bus in Supabase
            sb_bus = None
            if len(str(bus_id)) == 36 and '-' in str(bus_id):
                sb_bus = sb.table('buses').select('*').eq('id', str(bus_id)).maybe_single().execute()
            else:
                sb_bus = sb.table('buses').select('*').eq('bus_number', str(bus_id)).maybe_single().execute()
                
            if sb_bus and sb_bus.data:
                actual_bus_id = sb_bus.data['id']
                sb.table('buses').update({'status': 'Active'}).eq('id', actual_bus_id).execute()
                sb.table('bus_assignments').upsert({
                    'bus_id': actual_bus_id,
                    'driver_id': str(driver_id),
                    'status': 'Active'
                }, on_conflict='bus_id').execute()
                trip_id = actual_bus_id
        except Exception as sb_err:
            print("Supabase start_trip notice:", sb_err)
            
    # 2. Local SQLite fallback (safe on Vercel)
    try:
        conn = get_db()
        bus = conn.execute("SELECT id, route_id FROM buses WHERE id=? OR bus_number=?", (bus_id, str(bus_id))).fetchone()
        if bus:
            sqlite_bus_id = bus['id']
            existing_trip = conn.execute("SELECT id FROM trips WHERE driver_id=? AND status='Active'", (driver_id,)).fetchone()
            if not existing_trip:
                cursor = conn.execute("INSERT INTO trips (bus_id, driver_id, route_id, status) VALUES (?, ?, ?, 'Active')", 
                                     (sqlite_bus_id, driver_id, bus['route_id']))
                if not trip_id:
                    trip_id = cursor.lastrowid
            conn.execute("UPDATE buses SET gps_source='Real', status='Active Trip' WHERE id=?", (sqlite_bus_id,))
            conn.commit()
        conn.close()
    except Exception as db_err:
        print("SQLite start_trip notice:", db_err)
        
    return jsonify({'message': 'Trip started', 'trip_id': trip_id or str(uuid.uuid4())})

@app.route('/api/driver/end-trip', methods=['POST'])
def end_trip():
    if 'driver_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json or {}
    trip_id = data.get('trip_id')
    driver_id = session.get('driver_id')

    # 1. Update Supabase
    sb = database.get_supabase()
    if sb and driver_id:
        try:
            sb.table('bus_assignments').update({'status': 'Completed'}).eq('driver_id', str(driver_id)).execute()
        except Exception as sb_err:
            print("Supabase end_trip notice:", sb_err)
            
    # 2. Update SQLite
    try:
        conn = get_db()
        conn.execute("UPDATE trips SET status='Completed', end_time=CURRENT_TIMESTAMP WHERE id=? OR driver_id=?", (trip_id, driver_id))
        trip = conn.execute("SELECT bus_id FROM trips WHERE id=?", (trip_id,)).fetchone()
        if trip:
            conn.execute("UPDATE buses SET gps_source='Simulated', status='Idle' WHERE id=?", (trip['bus_id'],))
        conn.commit()
        conn.close()
    except Exception as db_err:
        print("SQLite end_trip notice:", db_err)
    
    return jsonify({'message': 'Trip ended'})

@app.route('/api/driver/location', methods=['POST'])
def update_location():
    if 'driver_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json or {}
    trip_id = data.get('trip_id')
    bus_id = data.get('bus_id')
    lat = data.get('latitude')
    lon = data.get('longitude')
    acc = data.get('accuracy')
    speed = data.get('speed', 0)
    
    if not all([trip_id, bus_id, lat is not None, lon is not None]):
        return jsonify({'error': 'Missing data'}), 400
    
    # 1. Update live locations in Supabase (Cloud First)
    sb = database.get_supabase()
    if sb:
        try:
            sb_bus_id = None
            if len(str(bus_id)) == 36 and '-' in str(bus_id):
                sb_bus_id = str(bus_id)
            else:
                sb_bus = sb.table('buses').select('id').or_(f"id.eq.{bus_id},bus_number.eq.{bus_id}").maybe_single().execute()
                sb_bus_id = sb_bus.data.get('id') if sb_bus and sb_bus.data else None
                
            if sb_bus_id:
                sb.table('bus_locations').upsert({
                    'bus_id': sb_bus_id,
                    'latitude': float(lat),
                    'longitude': float(lon),
                    'speed': float(speed or 0),
                    'updated_at': datetime.now().isoformat()
                }, on_conflict='bus_id').execute()
        except Exception as sb_err:
            print("Supabase bus_locations update notice:", sb_err)
            
    # 2. Local SQLite update (safe fallback)
    try:
        conn = get_db()
        conn.execute("INSERT INTO live_locations (trip_id, bus_id, latitude, longitude, accuracy) VALUES (?, ?, ?, ?, ?)",
                     (trip_id, bus_id, lat, lon, acc))
                     
        bus_row = conn.execute("SELECT bus_number, route_id, next_stop_id FROM buses WHERE id=? OR bus_number=?", (bus_id, str(bus_id))).fetchone()
        bus = dict(bus_row) if bus_row else None
                      
        # ---- ETA FOUNDATION & NEXT STOP CALCULATION ----
        if bus and bus['route_id']:
            raw_stops = conn.execute("SELECT id, latitude, longitude, stop_order, stop_name, scheduled_arrival_time FROM stops WHERE route_id=? ORDER BY stop_order", (bus['route_id'],)).fetchall()
            stops = [dict(s) for s in raw_stops]
            if stops:
                # Simple heuristic: find the closest stop that hasn't been passed
                closest_stop = stops[0]
                min_dist = float('inf')
                
                for s in stops:
                    dist = calculate_distance(lat, lon, s['latitude'], s['longitude'])
                    if dist < min_dist:
                        min_dist = dist
                        closest_stop = s
                        
                next_stop_id = closest_stop['id']
                
                # Delay Calculation Logic
                delay_status = 'ON TIME'
                delay_minutes = 0
                now = datetime.now()
                
                # Identify the actual target stop object
                target_stop = closest_stop
                arrived = False
                
                # If we are very close to the closest stop, target the next one in sequence
                if min_dist < 0.5: 
                    arrived = True
                    curr_idx = stops.index(closest_stop)
                    if curr_idx + 1 < len(stops):
                        target_stop = stops[curr_idx + 1]
                        next_stop_id = target_stop['id']
                
                # 1. Delay detection for the target stop
                sched_str = target_stop.get('scheduled_arrival_time')
                if sched_str:
                    sched_dt = datetime.strptime(f"{now.strftime('%Y-%m-%d')} {sched_str}", '%Y-%m-%d %H:%M:%S')
                    if now > sched_dt:
                        delay_status = 'DELAYED'
                        delay_minutes = int((now - sched_dt).total_seconds() / 60)
                        
                        # Create/Update notification
                        existing_alert = conn.execute("SELECT id FROM service_updates WHERE trip_id=? AND stop_id=? AND status='Active'", (trip_id, next_stop_id)).fetchone()
                        if not existing_alert:
                            b_info = conn.execute("SELECT bus_number, route_id FROM buses WHERE id=?", (bus_id,)).fetchone()
                            msg = f"Next Stop: {target_stop['stop_name']}. Scheduled: {sched_dt.strftime('%I:%M %p')}. Expected: {now.strftime('%I:%M %p')}."
                            conn.execute("INSERT INTO service_updates (title, message, status, trip_id, stop_id) VALUES (?, ?, 'Active', ?, ?)", 
                                         (f"🔴 {b_info['bus_number']} delayed by {delay_minutes} minutes.", msg, trip_id, next_stop_id))
                
                # 2. Arrival Logic (Record true ATA & Resolve alert)
                if arrived:
                    # Record ATA in arrivals
                    ata_str = now.strftime('%I:%M %p')
                    # Calculate exact delay for the arrived stop
                    arr_sched_str = closest_stop.get('scheduled_arrival_time')
                    arr_delay_mins = 0
                    if arr_sched_str:
                        arr_sched_dt = datetime.strptime(f"{now.strftime('%Y-%m-%d')} {arr_sched_str}", '%Y-%m-%d %H:%M:%S')
                        if now > arr_sched_dt:
                            arr_delay_mins = int((now - arr_sched_dt).total_seconds() / 60)
                    
                    conn.execute("INSERT INTO arrivals (bus_id, stop_id, ata, delay_minutes) VALUES (?, ?, ?, ?)", 
                                 (bus_id, closest_stop['id'], ata_str, arr_delay_mins))
                    
                    # Resolve the delay notification for the ARRIVED stop
                    conn.execute("UPDATE service_updates SET status='Resolved' WHERE trip_id=? AND stop_id=? AND status='Active'", 
                                 (trip_id, closest_stop['id']))

                # Update bus current location, next stop, and delay state
                conn.execute("UPDATE buses SET current_latitude=?, current_longitude=?, next_stop_id=?, delay_status=?, delay_minutes=? WHERE id=?", 
                             (lat, lon, next_stop_id, delay_status, delay_minutes, bus_id))
            else:
                conn.execute("UPDATE buses SET current_latitude=?, current_longitude=? WHERE id=?", (lat, lon, bus_id))
        else:
            conn.execute("UPDATE buses SET current_latitude=?, current_longitude=? WHERE id=?", (lat, lon, bus_id))

        conn.commit()
    finally:
        conn.close()
    
    return jsonify({'message': 'Location updated'})


# ==========================================
# IMPORT API
# ==========================================

@app.route('/api/import/preview', methods=['POST'])
def import_preview():
    records = request.json.get('records', [])
    conn = get_db()
    
    preview = {
        'adds': [],
        'updates': [],
        'duplicates': [],
        'rejected': []
    }
    
    # We will process rows. Each row can represent a Route, Stop, or Bus.
    for row in records:
        entity_type = row.get('Type', '').upper()
        
        # General validations
        data_source = row.get('Data Source', 'OFFICIAL')
        op = row.get('Operator', '')
        if data_source == 'OFFICIAL':
            if op not in ['APSRTC', 'TGSRTC']:
                preview['rejected'].append({'row': row, 'error': 'OFFICIAL data must have Operator APSRTC or TGSRTC'})
                continue
            if not row.get('Source URL') and not row.get('Source Reference'):
                preview['rejected'].append({'row': row, 'error': 'OFFICIAL data requires a Source URL or Source Reference'})
                continue
            if not row.get('Verification Date'):
                preview['rejected'].append({'row': row, 'error': 'OFFICIAL data requires a Verification Date'})
                continue

            
        if entity_type == 'ROUTE':
            existing = conn.execute("SELECT id FROM routes WHERE route_name=? AND source=? AND destination=?", (row.get('Route Name'), row.get('Source'), row.get('Destination'))).fetchone()
            if existing:
                preview['duplicates'].append({'row': row, 'reason': 'Route already exists'})
            else:
                preview['adds'].append({'row': row, 'type': 'ROUTE'})
                
        elif entity_type == 'BUS':
            bus_no = row.get('Bus Number')
            existing = conn.execute("SELECT id, status FROM buses WHERE bus_number=?", (bus_no,)).fetchone()
            
            # Route existence check
            r_name = row.get('Route Name')
            route = conn.execute("SELECT id FROM routes WHERE route_name=?", (r_name,)).fetchone()
            if not route:
                preview['rejected'].append({'row': row, 'error': f'Route {r_name} does not exist in DB yet (import routes first)'})
                continue
                
            if existing:
                if existing['status'] == 'Active Trip':
                    preview['rejected'].append({'row': row, 'error': 'Cannot overwrite bus on an active trip'})
                else:
                    preview['updates'].append({'row': row, 'type': 'BUS', 'id': existing['id']})
            else:
                preview['adds'].append({'row': row, 'type': 'BUS'})
                
        elif entity_type == 'STOP':
            r_name = row.get('Route Name')
            route = conn.execute("SELECT id FROM routes WHERE route_name=?", (r_name,)).fetchone()
            if not route:
                preview['rejected'].append({'row': row, 'error': f'Route {r_name} does not exist in DB'})
                continue
                
            s_name = row.get('Stop Name')
            existing = conn.execute("SELECT id FROM stops WHERE route_id=? AND stop_name=?", (route['id'], s_name)).fetchone()
            
            try:
                lat = float(row.get('Latitude', 0))
                lng = float(row.get('Longitude', 0))
                if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                    preview['rejected'].append({'row': row, 'error': 'Invalid coordinates'})
                    continue
            except:
                preview['rejected'].append({'row': row, 'error': 'Invalid coordinates format'})
                continue
                
            if existing:
                preview['updates'].append({'row': row, 'type': 'STOP', 'id': existing['id']})
            else:
                preview['adds'].append({'row': row, 'type': 'STOP'})
        else:
            preview['rejected'].append({'row': row, 'error': 'Unknown Type (must be ROUTE, BUS, or STOP)'})
            
    conn.close()
    return jsonify(preview)

@app.route('/api/import/commit', methods=['POST'])
def import_commit():
    payload = request.json
    adds = payload.get('adds', [])
    updates = payload.get('updates', [])
    
    conn = get_db()
    stats = {'routes': 0, 'buses': 0, 'stops': 0}
    
    # Process Adds
    for item in adds:
        row = item['row']
        etype = item['type']
        ds = row.get('Data Source', 'OFFICIAL')
        op = row.get('Operator')
        
        if etype == 'ROUTE':
            conn.execute('INSERT INTO routes (route_name, source, destination, operator, service_type, data_source, source_url, source_name, source_type, verified_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                         (row.get('Route Name'), row.get('Source'), row.get('Destination'), op, row.get('Service Type'), ds, row.get('Source URL'), row.get('Source Name'), row.get('Source Type'), row.get('Verification Date')))
            stats['routes'] += 1
            
        elif etype == 'BUS':
            route = conn.execute("SELECT id FROM routes WHERE route_name=?", (row.get('Route Name'),)).fetchone()
            if route:
                conn.execute('INSERT INTO buses (bus_number, bus_name, route_id, current_latitude, current_longitude, status, operator, service_type, data_source, source_url, source_name, source_type, verified_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                             (row.get('Bus Number'), row.get('Bus Name'), route['id'], row.get('Latitude', 0), row.get('Longitude', 0), 'Idle', op, row.get('Service Type'), ds, row.get('Source URL'), row.get('Source Name'), row.get('Source Type'), row.get('Verification Date')))
                stats['buses'] += 1
                
        elif etype == 'STOP':
            route = conn.execute("SELECT id FROM routes WHERE route_name=?", (row.get('Route Name'),)).fetchone()
            if route:
                conn.execute('INSERT INTO stops (route_id, stop_name, latitude, longitude, stop_order, area_type, scheduled_arrival_time, data_source, source_url, source_name, source_type, verified_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                             (route['id'], row.get('Stop Name'), row.get('Latitude'), row.get('Longitude'), row.get('Stop Order', 1), row.get('Area Type'), row.get('Scheduled Arrival Time'), ds, row.get('Source URL'), row.get('Source Name'), row.get('Source Type'), row.get('Verification Date')))
                stats['stops'] += 1

    # Process Updates
    for item in updates:
        row = item['row']
        etype = item['type']
        eid = item['id']
        ds = row.get('Data Source', 'OFFICIAL')
        op = row.get('Operator')
        
        if etype == 'BUS':
            route = conn.execute("SELECT id FROM routes WHERE route_name=?", (row.get('Route Name'),)).fetchone()
            if route:
                conn.execute('UPDATE buses SET bus_name=?, route_id=?, operator=?, service_type=?, data_source=?, source_url=?, source_name=?, source_type=?, verified_at=? WHERE id=?',
                             (row.get('Bus Name'), route['id'], op, row.get('Service Type'), ds, row.get('Source URL'), row.get('Source Name'), row.get('Source Type'), row.get('Verification Date'), eid))
                stats['buses'] += 1
                
        elif etype == 'STOP':
            route = conn.execute("SELECT id FROM routes WHERE route_name=?", (row.get('Route Name'),)).fetchone()
            if route:
                conn.execute('UPDATE stops SET latitude=?, longitude=?, stop_order=?, area_type=?, scheduled_arrival_time=?, data_source=?, source_url=?, source_name=?, source_type=?, verified_at=? WHERE id=?',
                             (row.get('Latitude'), row.get('Longitude'), row.get('Stop Order', 1), row.get('Area Type'), row.get('Scheduled Arrival Time'), ds, row.get('Source URL'), row.get('Source Name'), row.get('Source Type'), row.get('Verification Date'), eid))
                stats['stops'] += 1

    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'stats': stats})

@app.route('/api/admin/trips', methods=['GET'])
def admin_trips():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    sql = """
        SELECT 
            t.id as trip_id, 
            b.bus_number, 
            b.bus_name, 
            COALESCE(r.operator, b.operator) as operator,
            r.route_name, 
            d.name as driver_name, 
            c.name as conductor_name, 
            t.start_time, 
            t.end_time, 
            t.status as trip_status,
            (SELECT COUNT(*) FROM stops s WHERE s.route_id = COALESCE(t.route_id, b.route_id)) as num_stops,
            (SELECT COUNT(*) FROM arrivals a WHERE a.bus_id = t.bus_id AND a.recorded_at >= t.start_time AND (t.end_time IS NULL OR a.recorded_at <= t.end_time)) as num_arrivals,
            (SELECT COUNT(*) FROM arrivals a WHERE a.bus_id = t.bus_id AND a.recorded_at >= t.start_time AND (t.end_time IS NULL OR a.recorded_at <= t.end_time) AND a.delay_minutes > 0) as delayed_stops,
            (SELECT SUM(delay_minutes) FROM arrivals a WHERE a.bus_id = t.bus_id AND a.recorded_at >= t.start_time AND (t.end_time IS NULL OR a.recorded_at <= t.end_time) AND a.delay_minutes > 0) as total_delay_minutes
        FROM trips t
        JOIN buses b ON t.bus_id = b.id
        LEFT JOIN routes r ON COALESCE(t.route_id, b.route_id) = r.id
        LEFT JOIN drivers d ON t.driver_id = d.id
        LEFT JOIN conductors c ON t.conductor_id = c.id
        ORDER BY t.start_time DESC
    """
    rows = conn.execute(sql).fetchall()
    conn.close()
    
    trips = []
    for r in rows:
        d = dict(r)
        d['total_delay_minutes'] = d['total_delay_minutes'] or 0
        trips.append(d)
        
    return jsonify(trips)

@app.route('/api/admin/trips/<int:trip_id>', methods=['GET'])
def admin_trip_details(trip_id):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    trip = conn.execute("SELECT bus_id, COALESCE(route_id, (SELECT route_id FROM buses WHERE id = trips.bus_id)) as route_id, start_time, end_time FROM trips WHERE id = ?", (trip_id,)).fetchone()
    if not trip:
        conn.close()
        return jsonify({'error': 'Trip not found'}), 404
        
    sql = """
        SELECT 
            s.stop_name, 
            s.stop_order, 
            s.scheduled_arrival_time,
            a.ata,
            a.delay_minutes
        FROM stops s
        LEFT JOIN arrivals a 
            ON s.id = a.stop_id 
            AND a.bus_id = ? 
            AND a.recorded_at >= ? 
            AND (? IS NULL OR a.recorded_at <= ?)
        WHERE s.route_id = ?
        ORDER BY s.stop_order
    """
    rows = conn.execute(sql, (trip['bus_id'], trip['start_time'], trip['end_time'], trip['end_time'], trip['route_id'])).fetchall()
    conn.close()
    
    stops = []
    for r in rows:
        d = dict(r)
        
        status = "NOT REACHED"
        if d['ata'] is not None:
            if d['delay_minutes'] is not None and d['delay_minutes'] > 0:
                status = "DELAYED"
            elif d['delay_minutes'] is not None and d['delay_minutes'] <= 0:
                status = "ON TIME"
            else:
                status = "ARRIVED"
        
        d['status'] = status
        stops.append(d)
        
    return jsonify(stops)


@app.route('/api/admin/analytics', methods=['GET'])
def admin_analytics():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    sql = """
        SELECT 
            t.id as trip_id, 
            b.id as bus_id,
            b.bus_number, 
            b.bus_name, 
            COALESCE(r.operator, b.operator) as operator,
            r.id as route_id,
            r.route_name, 
            date(t.start_time) as trip_date,
            t.status as trip_status,
            (SELECT COUNT(*) FROM arrivals a WHERE a.bus_id = t.bus_id AND a.recorded_at >= t.start_time AND (t.end_time IS NULL OR a.recorded_at <= t.end_time) AND a.delay_minutes > 0) as delayed_stops,
            (SELECT SUM(delay_minutes) FROM arrivals a WHERE a.bus_id = t.bus_id AND a.recorded_at >= t.start_time AND (t.end_time IS NULL OR a.recorded_at <= t.end_time) AND a.delay_minutes > 0) as total_delay_minutes
        FROM trips t
        JOIN buses b ON t.bus_id = b.id
        LEFT JOIN routes r ON COALESCE(t.route_id, b.route_id) = r.id
    """
    
    params = []
    conditions = []
    
    start_date = request.args.get('start_date')
    if start_date:
        conditions.append("date(t.start_time) >= ?")
        params.append(start_date)
        
    end_date = request.args.get('end_date')
    if end_date:
        conditions.append("date(t.start_time) <= ?")
        params.append(end_date)
        
    operator = request.args.get('operator')
    if operator and operator != 'ALL':
        conditions.append("COALESCE(r.operator, b.operator) = ?")
        params.append(operator)
        
    route = request.args.get('route')
    if route and route != 'ALL':
        conditions.append("r.route_name = ?")
        params.append(route)
        
    bus = request.args.get('bus')
    if bus and bus != 'ALL':
        conditions.append("b.bus_number = ?")
        params.append(bus)
        
    status = request.args.get('status')
    if status and status != 'ALL':
        conditions.append("t.status = ?")
        params.append(status)
        
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
        
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    
    # Compute stats
    summary = {
        'total_trips': len(rows),
        'active_trips': 0,
        'completed_trips': 0,
        'delayed_trips': 0,
        'on_time_trips': 0,
        'avg_delay': 0
    }
    
    total_delay_all = 0
    trips_with_delay = 0
    
    operator_stats = {}
    daily_trend = {}
    bus_stats = {}
    route_stats = {}
    
    for r in rows:
        d = dict(r)
        d['total_delay_minutes'] = d['total_delay_minutes'] or 0
        
        # Summary
        if d['trip_status'] == 'Active':
            summary['active_trips'] += 1
        elif d['trip_status'] == 'Completed':
            summary['completed_trips'] += 1
            
        if d['delayed_stops'] > 0:
            summary['delayed_trips'] += 1
        else:
            summary['on_time_trips'] += 1
            
        if d['total_delay_minutes'] > 0:
            total_delay_all += d['total_delay_minutes']
            trips_with_delay += 1
            
        # Operator stats
        op = d['operator'] or 'Unknown'
        if op not in operator_stats:
            operator_stats[op] = {'trips': 0, 'total_delay': 0, 'delayed_trips': 0}
        operator_stats[op]['trips'] += 1
        operator_stats[op]['total_delay'] += d['total_delay_minutes']
        if d['delayed_stops'] > 0:
            operator_stats[op]['delayed_trips'] += 1
            
        # Daily trend
        tdate = d['trip_date']
        if tdate not in daily_trend:
            daily_trend[tdate] = 0
        daily_trend[tdate] += 1
        
        # Bus stats
        bkey = d['bus_number']
        if bkey not in bus_stats:
            bus_stats[bkey] = {
                'bus_number': d['bus_number'],
                'bus_name': d['bus_name'],
                'operator': op,
                'trips': 0,
                'delayed_trips': 0,
                'total_delay': 0
            }
        bus_stats[bkey]['trips'] += 1
        bus_stats[bkey]['total_delay'] += d['total_delay_minutes']
        if d['delayed_stops'] > 0:
            bus_stats[bkey]['delayed_trips'] += 1
            
        # Route stats
        rkey = d['route_name'] or 'Unknown Route'
        if rkey not in route_stats:
            route_stats[rkey] = {
                'route': rkey,
                'operator': op,
                'trips': 0,
                'delayed_trips': 0,
                'total_delay': 0
            }
        route_stats[rkey]['trips'] += 1
        route_stats[rkey]['total_delay'] += d['total_delay_minutes']
        if d['delayed_stops'] > 0:
            route_stats[rkey]['delayed_trips'] += 1

    if trips_with_delay > 0:
        summary['avg_delay'] = round(total_delay_all / trips_with_delay)
        
    # Formatting
    # Operator
    op_list = []
    for k, v in operator_stats.items():
        v['operator'] = k
        v['avg_delay'] = round(v['total_delay'] / v['delayed_trips']) if v['delayed_trips'] > 0 else 0
        op_list.append(v)
        
    # Daily
    dt_list = [{'date': k, 'trips': v} for k, v in sorted(daily_trend.items())]
    
    # Buses
    b_list = list(bus_stats.values())
    for b in b_list:
        b['avg_delay'] = round(b['total_delay'] / b['delayed_trips']) if b['delayed_trips'] > 0 else 0
    b_list.sort(key=lambda x: x['avg_delay'], reverse=True)
    
    # Routes
    r_list = list(route_stats.values())
    for r in r_list:
        r['avg_delay'] = round(r['total_delay'] / r['delayed_trips']) if r['delayed_trips'] > 0 else 0
    r_list.sort(key=lambda x: x['avg_delay'], reverse=True)
    
    # Full trip data for CSV export
    return jsonify({
        'summary': summary,
        'operator_comparison': op_list,
        'daily_trend': dt_list,
        'most_delayed_buses': b_list,
        'most_delayed_routes': r_list,
        'raw_trips': [dict(r) for r in rows]
    })


@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    bus_id = request.args.get('bus_id')
    conn = get_db()
    conn.row_factory = sqlite3.Row
    
    # We want active alerts for the selected bus (via trip_id)
    # The active trip for a bus is where status = 'Active'
    
    if bus_id:
        sql = """
            SELECT su.* 
            FROM service_updates su
            JOIN trips t ON su.trip_id = t.id
            WHERE t.bus_id = ? AND su.status = 'Active'
            ORDER BY su.created_at DESC
        """
        rows = conn.execute(sql, (bus_id,)).fetchall()
    else:
        # If no bus selected, maybe show global active alerts (where trip_id is NULL)
        sql = "SELECT * FROM service_updates WHERE status = 'Active' AND trip_id IS NULL ORDER BY created_at DESC"
        rows = conn.execute(sql).fetchall()
        
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/admin/alerts', methods=['GET'])
def admin_alerts():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    sql = """
        SELECT 
            su.id as alert_id,
            su.title as alert_type,
            su.message,
            su.status,
            su.created_at,
            su.trip_id,
            t.bus_id,
            b.bus_number,
            r.route_name,
            COALESCE(r.operator, b.operator) as operator,
            s.stop_name
        FROM service_updates su
        LEFT JOIN trips t ON su.trip_id = t.id
        LEFT JOIN buses b ON t.bus_id = b.id
        LEFT JOIN routes r ON COALESCE(t.route_id, b.route_id) = r.id
        LEFT JOIN stops s ON su.stop_id = s.id
        ORDER BY su.created_at DESC
    """
    rows = conn.execute(sql).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/complaints', methods=['POST'])
def create_complaint():
    if 'passenger_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json
    category = data.get('category')
    description = data.get('description')
    bus_id = data.get('bus_id')
    route_id = data.get('route_id')
    
    if not category or not description:
        return jsonify({'error': 'Category and description are required'}), 400
        
    conn = get_db()
    
    # Validate bus and route
    if bus_id:
        b = conn.execute("SELECT id FROM buses WHERE id=?", (bus_id,)).fetchone()
        if not b:
            conn.close()
            return jsonify({'error': 'Invalid bus ID'}), 400
            
    if route_id:
        r = conn.execute("SELECT id FROM routes WHERE id=?", (route_id,)).fetchone()
        if not r:
            conn.close()
            return jsonify({'error': 'Invalid route ID'}), 400
            
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO complaints (passenger_id, bus_id, route_id, category, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (session['passenger_id'], bus_id, route_id, category, description))
    complaint_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'complaint_id': complaint_id, 'message': 'Complaint submitted successfully'})

@app.route('/api/complaints/my', methods=['GET'])
def get_my_complaints():
    if 'passenger_id' not in session:
        return jsonify([])
        
    conn = get_db()
    conn.row_factory = sqlite3.Row
    sql = """
        SELECT c.*, b.bus_number, r.route_name 
        FROM complaints c
        LEFT JOIN buses b ON c.bus_id = b.id
        LEFT JOIN routes r ON c.route_id = r.id
        WHERE c.passenger_id = ?
        ORDER BY c.created_at DESC
    """
    rows = conn.execute(sql, (session['passenger_id'],)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/admin/complaints', methods=['GET'])
def get_admin_complaints():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    sql = """
        SELECT c.*, b.bus_number, r.route_name, COALESCE(r.operator, b.operator) as operator 
        FROM complaints c
        LEFT JOIN buses b ON c.bus_id = b.id
        LEFT JOIN routes r ON c.route_id = r.id
        ORDER BY c.created_at DESC
    """
    rows = conn.execute(sql).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/admin/complaints/<int:id>', methods=['PUT'])
def update_complaint(id):
    data = request.json
    status = data.get('status')
    admin_response = data.get('admin_response')
    
    if not status:
        return jsonify({'error': 'Status is required'}), 400
        
    conn = get_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if status in ['Resolved', 'Rejected']:
        conn.execute('''
            UPDATE complaints 
            SET status=?, admin_response=?, updated_at=?, resolved_at=? 
            WHERE id=?
        ''', (status, admin_response, now, now, id))
    else:
        conn.execute('''
            UPDATE complaints 
            SET status=?, admin_response=?, updated_at=? 
            WHERE id=?
        ''', (status, admin_response, now, id))
        
    conn.commit()
    conn.close()
    return jsonify({'success': True})


if __name__ == '__main__':
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000
    )
