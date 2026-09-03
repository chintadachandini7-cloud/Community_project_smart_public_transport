with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

import_logic = """
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
        if data_source == 'OFFICIAL' and op not in ['APSRTC', 'TGSRTC']:
            preview['rejected'].append({'row': row, 'error': 'OFFICIAL data must have Operator APSRTC or TGSRTC'})
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
            conn.execute('INSERT INTO routes (route_name, source, destination, operator, service_type, data_source) VALUES (?, ?, ?, ?, ?, ?)',
                         (row.get('Route Name'), row.get('Source'), row.get('Destination'), op, row.get('Service Type'), ds))
            stats['routes'] += 1
            
        elif etype == 'BUS':
            route = conn.execute("SELECT id FROM routes WHERE route_name=?", (row.get('Route Name'),)).fetchone()
            if route:
                conn.execute('INSERT INTO buses (bus_number, bus_name, route_id, current_latitude, current_longitude, status, operator, service_type, data_source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                             (row.get('Bus Number'), row.get('Bus Name'), route['id'], row.get('Latitude', 0), row.get('Longitude', 0), 'Idle', op, row.get('Service Type'), ds))
                stats['buses'] += 1
                
        elif etype == 'STOP':
            route = conn.execute("SELECT id FROM routes WHERE route_name=?", (row.get('Route Name'),)).fetchone()
            if route:
                conn.execute('INSERT INTO stops (route_id, stop_name, latitude, longitude, stop_order, area_type, scheduled_arrival_time, data_source) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                             (route['id'], row.get('Stop Name'), row.get('Latitude'), row.get('Longitude'), row.get('Stop Order', 1), row.get('Area Type'), row.get('Scheduled Arrival Time'), ds))
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
                conn.execute('UPDATE buses SET bus_name=?, route_id=?, operator=?, service_type=?, data_source=? WHERE id=?',
                             (row.get('Bus Name'), route['id'], op, row.get('Service Type'), ds, eid))
                stats['buses'] += 1
                
        elif etype == 'STOP':
            route = conn.execute("SELECT id FROM routes WHERE route_name=?", (row.get('Route Name'),)).fetchone()
            if route:
                conn.execute('UPDATE stops SET latitude=?, longitude=?, stop_order=?, area_type=?, scheduled_arrival_time=?, data_source=? WHERE id=?',
                             (row.get('Latitude'), row.get('Longitude'), row.get('Stop Order', 1), row.get('Area Type'), row.get('Scheduled Arrival Time'), ds, eid))
                stats['stops'] += 1

    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'stats': stats})
"""

code = code.replace("if __name__ == '__main__':", import_logic + "\nif __name__ == '__main__':")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Patched app.py with import APIs")
