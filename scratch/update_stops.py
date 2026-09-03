import sqlite3
conn = sqlite3.connect('transport.db')

# Route 3 current stops: 
# 1: Neerukonda
# 2: Kuragallu
# 3: Mangalagiri Bus Station
# 4: Tadepalli
# 5: Vijayawada PNBS

# Update the stops to geographically match 18.37, 83.809
stops_data = [
    (1, 'Cheepurupalle Village', 18.3690, 83.8085, 'VILLAGE'),
    (2, 'Garividi Town', 18.2800, 83.5400, 'TOWN'),
    (3, 'Vizianagaram RTC Complex', 18.1100, 83.4100, 'CITY')
]

# Delete old stops for route 3
conn.execute('DELETE FROM stops WHERE route_id = 3')

# Insert new stops
for order, name, lat, lon, area in stops_data:
    conn.execute(
        'INSERT INTO stops (route_id, stop_order, stop_name, latitude, longitude, area_type) VALUES (?, ?, ?, ?, ?, ?)',
        (3, order, name, lat, lon, area)
    )

# Also update the route name slightly to reflect the new region (optional, but requested: "Preserve the existing route name", so I will NOT change the route name or B-101)
# I will only change the route's source and destination fields to match the new stops.
conn.execute("UPDATE routes SET source='Cheepurupalle', destination='Vizianagaram' WHERE id=3")

conn.commit()
conn.close()
print("Successfully updated route 3 stops.")
