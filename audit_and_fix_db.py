import sqlite3

def run_audit():
    print("Connecting to database...")
    conn = sqlite3.connect('transport.db')
    cursor = conn.cursor()
    
    # Add columns if they don't exist
    for table in ['routes', 'stops', 'buses']:
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [c[1] for c in cursor.fetchall()]
        if 'data_source' not in cols:
            print(f"Adding data_source column to {table}...")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN data_source TEXT DEFAULT 'OFFICIAL'")
            
    # Audit and update existing data to clean up the invented bus numbers
    print("Auditing Routes...")
    # Routes represent physical paths, so they are Official data
    cursor.execute("UPDATE routes SET data_source='OFFICIAL', route_name='APSRTC Pallevelugu Corridor' WHERE route_name LIKE '%Route 101%'")
    cursor.execute("UPDATE routes SET data_source='OFFICIAL', route_name='TGSRTC Pallevelugu Corridor' WHERE route_name LIKE '%Route 201%'")
    
    print("Auditing Stops...")
    # Stops represent physical coordinates, so they are Official
    cursor.execute("UPDATE stops SET data_source='OFFICIAL'")
    
    print("Auditing Buses...")
    # Buses currently have invented numbers (AP-07-1234, TS-09-5678, etc). We must scrub them.
    cursor.execute("UPDATE buses SET bus_number='Simulated Vehicle', bus_name='Demo Bus', data_source='SIMULATED' WHERE bus_number LIKE 'AP-%' OR bus_number LIKE 'TS-%' OR bus_number LIKE 'B-%'")
    
    # Fetch audit report data
    report = {
        'official_routes': cursor.execute("SELECT COUNT(*) FROM routes WHERE data_source='OFFICIAL'").fetchone()[0],
        'simulated_routes': cursor.execute("SELECT COUNT(*) FROM routes WHERE data_source='SIMULATED'").fetchone()[0],
        'official_stops': cursor.execute("SELECT COUNT(*) FROM stops WHERE data_source='OFFICIAL'").fetchone()[0],
        'simulated_stops': cursor.execute("SELECT COUNT(*) FROM stops WHERE data_source='SIMULATED'").fetchone()[0],
        'official_buses': cursor.execute("SELECT COUNT(*) FROM buses WHERE data_source='OFFICIAL'").fetchone()[0],
        'simulated_buses': cursor.execute("SELECT COUNT(*) FROM buses WHERE data_source='SIMULATED'").fetchone()[0],
    }
    
    conn.commit()
    conn.close()
    
    print("\n--- AUDIT REPORT ---")
    print(f"Official Routes: {report['official_routes']}")
    print(f"Simulated Routes: {report['simulated_routes']}")
    print(f"Official Stops: {report['official_stops']}")
    print(f"Simulated Stops: {report['simulated_stops']}")
    print(f"Official Buses: {report['official_buses']}")
    print(f"Simulated Buses: {report['simulated_buses']}")
    print("Audit and fix complete.")

if __name__ == '__main__':
    run_audit()
