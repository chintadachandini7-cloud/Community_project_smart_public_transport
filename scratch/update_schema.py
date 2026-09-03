import sqlite3
import json
conn = sqlite3.connect('transport.db')
cursor = conn.cursor()

# Update buses schema
cursor.execute("PRAGMA table_info(buses)")
cols = [c[1] for c in cursor.fetchall()]
if 'delay_status' not in cols:
    cursor.execute("ALTER TABLE buses ADD COLUMN delay_status TEXT")
if 'delay_minutes' not in cols:
    cursor.execute("ALTER TABLE buses ADD COLUMN delay_minutes INTEGER DEFAULT 0")

# Update stops schema
cursor.execute("PRAGMA table_info(stops)")
cols = [c[1] for c in cursor.fetchall()]
if 'scheduled_arrival_time' not in cols:
    cursor.execute("ALTER TABLE stops ADD COLUMN scheduled_arrival_time TEXT")

# Update service_updates to link to trip/stop (easier to prevent duplicates and auto-resolve)
cursor.execute("PRAGMA table_info(service_updates)")
cols = [c[1] for c in cursor.fetchall()]
if 'trip_id' not in cols:
    cursor.execute("ALTER TABLE service_updates ADD COLUMN trip_id INTEGER")
if 'stop_id' not in cols:
    cursor.execute("ALTER TABLE service_updates ADD COLUMN stop_id INTEGER")

# Update Route 3 scheduled times
times = {
    1: '18:00:00', # Cheepurupalle Village
    2: '18:30:00', # Garividi Town
    3: '19:15:00'  # Vizianagaram RTC Complex
}
for order, t in times.items():
    cursor.execute("UPDATE stops SET scheduled_arrival_time = ? WHERE route_id = 3 AND stop_order = ?", (t, order))

conn.commit()
conn.close()
print("Schema and Route 3 data updated.")
