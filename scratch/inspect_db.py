import sqlite3
conn = sqlite3.connect('transport.db')
conn.row_factory = sqlite3.Row

bus = conn.execute("SELECT route_id FROM buses WHERE bus_number = 'B-101'").fetchone()
print(f'Route ID: {bus["route_id"]}')

stops = conn.execute("SELECT stop_order, stop_name, latitude, longitude FROM stops WHERE route_id = ? ORDER BY stop_order", (bus["route_id"],)).fetchall()
for s in stops:
    print(f'{s["stop_order"]}: {s["stop_name"]} ({s["latitude"]}, {s["longitude"]})')
