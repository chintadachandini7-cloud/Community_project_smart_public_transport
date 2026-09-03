import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace SELECT from stops to include scheduled_arrival_time and stop_name
old_select = "SELECT id, latitude, longitude, stop_order FROM stops WHERE route_id=? ORDER BY stop_order"
new_select = "SELECT id, latitude, longitude, stop_order, stop_name, scheduled_arrival_time FROM stops WHERE route_id=? ORDER BY stop_order"
code = code.replace(old_select, new_select)

# Replace the block that updates the bus location with the new delay logic
old_block = """            # If we are very close to the closest stop, target the next one in sequence
            if min_dist < 0.5: 
                curr_idx = stops.index(closest_stop)
                if curr_idx + 1 < len(stops):
                    next_stop_id = stops[curr_idx + 1]['id']
            
            # Update bus current location and next stop
            conn.execute("UPDATE buses SET current_latitude=?, current_longitude=?, next_stop_id=? WHERE id=?", (lat, lon, next_stop_id, bus_id))"""

new_block = """            # Delay Calculation Logic
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
                        r_info = conn.execute("SELECT route_name FROM routes WHERE id=?", (b_info['route_id'],)).fetchone()
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
                         (lat, lon, next_stop_id, delay_status, delay_minutes, bus_id))"""

code = code.replace(old_block, new_block)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Updated app.py")
