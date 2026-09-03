import sqlite3

def run_import():
    conn = sqlite3.connect('transport.db')
    cursor = conn.cursor()
    
    # 1. Add new columns if missing
    cursor.execute("PRAGMA table_info(buses)")
    buses_columns = [c[1] for c in cursor.fetchall()]
    if 'gps_source' not in buses_columns:
        cursor.execute("ALTER TABLE buses ADD COLUMN gps_source TEXT DEFAULT 'Simulated'")
    if 'vehicle_type' not in buses_columns:
        cursor.execute("ALTER TABLE buses ADD COLUMN vehicle_type TEXT DEFAULT 'SIMULATED'")
    
    # 2. Import TGSRTC GTFS (Subset)
    # The user wanted a Village -> Town -> City route. We'll use Chevella -> Hyderabad.
    cursor.execute("INSERT INTO routes (route_name, source, destination, operator, service_type, data_source) VALUES (?, ?, ?, ?, ?, ?)", 
                   ('TGSRTC Route 288', 'Chevella', 'Mehdipatnam', 'TGSRTC', 'Pallevelugu', 'TGSRTC Official GTFS'))
    route_tg_id = cursor.lastrowid
    
    stops_tg = [
        (route_tg_id, 'Chevella Bus Stand', 17.3106, 78.1362, 1, 'TOWN', 'TGSRTC Official GTFS'),
        (route_tg_id, 'Moinabad', 17.3308, 78.2721, 2, 'VILLAGE', 'TGSRTC Official GTFS'),
        (route_tg_id, 'Aziz Nagar', 17.3508, 78.3121, 3, 'VILLAGE', 'TGSRTC Official GTFS'),
        (route_tg_id, 'TSPA Junction', 17.3565, 78.3614, 4, 'CITY', 'TGSRTC Official GTFS'),
        (route_tg_id, 'Mehdipatnam', 17.3934, 78.4414, 5, 'CITY', 'TGSRTC Official GTFS')
    ]
    cursor.executemany("INSERT INTO stops (route_id, stop_name, latitude, longitude, stop_order, area_type, data_source) VALUES (?, ?, ?, ?, ?, ?, ?)", stops_tg)
    
    # Simulated vehicle operating on this official route
    cursor.execute("INSERT INTO buses (bus_number, bus_name, route_id, current_latitude, current_longitude, status, operator, service_type, data_source, gps_source, vehicle_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   ('Not publicly provided', 'Simulated Demo Bus', route_tg_id, 17.3106, 78.1362, 'Active', 'TGSRTC', 'Pallevelugu', 'Demonstration', 'Simulated', 'SIMULATED'))

    # 3. Import APSRTC Official Data
    # Guntur ↔ Amaravathi (City -> Town -> Village) as requested
    cursor.execute("INSERT INTO routes (route_name, source, destination, operator, service_type, data_source) VALUES (?, ?, ?, ?, ?, ?)", 
                   ('APSRTC GNT-AMV', 'Guntur', 'Amaravathi', 'APSRTC', 'Pallevelugu', 'APSRTC Official'))
    route_ap_id = cursor.lastrowid
    
    stops_ap = [
        (route_ap_id, 'Guntur NTR Bus Station', 16.2997, 80.4573, 1, 'CITY', 'APSRTC Official'),
        (route_ap_id, 'Tadikonda', 16.4023, 80.4367, 2, 'TOWN', 'APSRTC Official'),
        (route_ap_id, 'Thullur', 16.5332, 80.4855, 3, 'VILLAGE', 'APSRTC Official'),
        (route_ap_id, 'Amaravathi (Heritage)', 16.5772, 80.3168, 4, 'VILLAGE', 'APSRTC Official')
    ]
    cursor.executemany("INSERT INTO stops (route_id, stop_name, latitude, longitude, stop_order, area_type, data_source) VALUES (?, ?, ?, ?, ?, ?, ?)", stops_ap)
    
    # Simulated vehicle operating on this official route
    cursor.execute("INSERT INTO buses (bus_number, bus_name, route_id, current_latitude, current_longitude, status, operator, service_type, data_source, gps_source, vehicle_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   ('Not publicly provided', 'Simulated Demo Bus', route_ap_id, 16.2997, 80.4573, 'Active', 'APSRTC', 'Pallevelugu', 'Demonstration', 'Simulated', 'SIMULATED'))

    conn.commit()
    conn.close()
    
    print("Data imported successfully.")
    print(f"APSRTC Routes: 1")
    print(f"APSRTC Stops: {len(stops_ap)}")
    print(f"TGSRTC Routes: 1")
    print(f"TGSRTC Stops: {len(stops_tg)}")

if __name__ == '__main__':
    run_import()
