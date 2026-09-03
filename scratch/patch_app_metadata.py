import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Update import_preview
old_preview = """        # General validations
        data_source = row.get('Data Source', 'OFFICIAL')
        op = row.get('Operator', '')
        if data_source == 'OFFICIAL' and op not in ['APSRTC', 'TGSRTC']:
            preview['rejected'].append({'row': row, 'error': 'OFFICIAL data must have Operator APSRTC or TGSRTC'})
            continue"""

new_preview = """        # General validations
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
"""
code = code.replace(old_preview, new_preview)

# Update import_commit
old_commit_r_insert = """            conn.execute('INSERT INTO routes (route_name, source, destination, operator, service_type, data_source) VALUES (?, ?, ?, ?, ?, ?)',
                         (row.get('Route Name'), row.get('Source'), row.get('Destination'), op, row.get('Service Type'), ds))"""
new_commit_r_insert = """            conn.execute('INSERT INTO routes (route_name, source, destination, operator, service_type, data_source, source_url, source_name, source_type, verified_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                         (row.get('Route Name'), row.get('Source'), row.get('Destination'), op, row.get('Service Type'), ds, row.get('Source URL'), row.get('Source Name'), row.get('Source Type'), row.get('Verification Date')))"""
code = code.replace(old_commit_r_insert, new_commit_r_insert)

old_commit_b_insert = """                conn.execute('INSERT INTO buses (bus_number, bus_name, route_id, current_latitude, current_longitude, status, operator, service_type, data_source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                             (row.get('Bus Number'), row.get('Bus Name'), route['id'], row.get('Latitude', 0), row.get('Longitude', 0), 'Idle', op, row.get('Service Type'), ds))"""
new_commit_b_insert = """                conn.execute('INSERT INTO buses (bus_number, bus_name, route_id, current_latitude, current_longitude, status, operator, service_type, data_source, source_url, source_name, source_type, verified_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                             (row.get('Bus Number'), row.get('Bus Name'), route['id'], row.get('Latitude', 0), row.get('Longitude', 0), 'Idle', op, row.get('Service Type'), ds, row.get('Source URL'), row.get('Source Name'), row.get('Source Type'), row.get('Verification Date')))"""
code = code.replace(old_commit_b_insert, new_commit_b_insert)

old_commit_s_insert = """                conn.execute('INSERT INTO stops (route_id, stop_name, latitude, longitude, stop_order, area_type, scheduled_arrival_time, data_source) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                             (route['id'], row.get('Stop Name'), row.get('Latitude'), row.get('Longitude'), row.get('Stop Order', 1), row.get('Area Type'), row.get('Scheduled Arrival Time'), ds))"""
new_commit_s_insert = """                conn.execute('INSERT INTO stops (route_id, stop_name, latitude, longitude, stop_order, area_type, scheduled_arrival_time, data_source, source_url, source_name, source_type, verified_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                             (route['id'], row.get('Stop Name'), row.get('Latitude'), row.get('Longitude'), row.get('Stop Order', 1), row.get('Area Type'), row.get('Scheduled Arrival Time'), ds, row.get('Source URL'), row.get('Source Name'), row.get('Source Type'), row.get('Verification Date')))"""
code = code.replace(old_commit_s_insert, new_commit_s_insert)

old_commit_b_update = """                conn.execute('UPDATE buses SET bus_name=?, route_id=?, operator=?, service_type=?, data_source=? WHERE id=?',
                             (row.get('Bus Name'), route['id'], op, row.get('Service Type'), ds, eid))"""
new_commit_b_update = """                conn.execute('UPDATE buses SET bus_name=?, route_id=?, operator=?, service_type=?, data_source=?, source_url=?, source_name=?, source_type=?, verified_at=? WHERE id=?',
                             (row.get('Bus Name'), route['id'], op, row.get('Service Type'), ds, row.get('Source URL'), row.get('Source Name'), row.get('Source Type'), row.get('Verification Date'), eid))"""
code = code.replace(old_commit_b_update, new_commit_b_update)

old_commit_s_update = """                conn.execute('UPDATE stops SET latitude=?, longitude=?, stop_order=?, area_type=?, scheduled_arrival_time=?, data_source=? WHERE id=?',
                             (row.get('Latitude'), row.get('Longitude'), row.get('Stop Order', 1), row.get('Area Type'), row.get('Scheduled Arrival Time'), ds, eid))"""
new_commit_s_update = """                conn.execute('UPDATE stops SET latitude=?, longitude=?, stop_order=?, area_type=?, scheduled_arrival_time=?, data_source=?, source_url=?, source_name=?, source_type=?, verified_at=? WHERE id=?',
                             (row.get('Latitude'), row.get('Longitude'), row.get('Stop Order', 1), row.get('Area Type'), row.get('Scheduled Arrival Time'), ds, row.get('Source URL'), row.get('Source Name'), row.get('Source Type'), row.get('Verification Date'), eid))"""
code = code.replace(old_commit_s_update, new_commit_s_update)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Patched app.py with validation logic")
