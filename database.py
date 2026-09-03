import sqlite3
import os

# The name of our database file
DB_NAME = 'transport.db'

def get_db_connection():
    """Connects to the SQLite database and returns the connection object."""
    conn = sqlite3.connect(DB_NAME)
    # This allows us to access columns by name (e.g., row['bus_number'])
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    """Creates the database tables if they do not exist and adds sample data."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. buses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS buses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bus_number TEXT NOT NULL,
            bus_name TEXT,
            route_id INTEGER,
            current_latitude REAL,
            current_longitude REAL,
            status TEXT,
            delay_status TEXT,
            delay_minutes INTEGER DEFAULT 0
        )
    ''')

    # 2. routes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_name TEXT NOT NULL,
            source TEXT,
            destination TEXT
        )
    ''')

    # 3. stops table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_id INTEGER,
            stop_name TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            stop_order INTEGER,
            scheduled_arrival_time TEXT
        )
    ''')

    # 4. arrivals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS arrivals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bus_id INTEGER,
            stop_id INTEGER,
            eta TEXT,
            ata TEXT,
            delay_minutes INTEGER,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 5. service_updates table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT,
            trip_id INTEGER,
            stop_id INTEGER
        )
    ''')
    
    # 6. Stage 4: Real GPS Tracking Tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            status TEXT DEFAULT 'Active'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conductors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            status TEXT DEFAULT 'Active'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bus_id INTEGER,
            driver_id INTEGER,
            conductor_id INTEGER,
            route_id INTEGER,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            status TEXT DEFAULT 'Active',
            FOREIGN KEY(bus_id) REFERENCES buses(id),
            FOREIGN KEY(driver_id) REFERENCES drivers(id),
            FOREIGN KEY(conductor_id) REFERENCES conductors(id),
            FOREIGN KEY(route_id) REFERENCES routes(id)
        )
    ''')
    
    # Ensure route_id exists in trips (for migration)
    cursor.execute("PRAGMA table_info(trips)")
    trips_columns = [col['name'] for col in cursor.fetchall()]
    if 'route_id' not in trips_columns:
        cursor.execute("ALTER TABLE trips ADD COLUMN route_id INTEGER")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS live_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER,
            bus_id INTEGER,
            latitude REAL,
            longitude REAL,
            accuracy REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(trip_id) REFERENCES trips(id),
            FOREIGN KEY(bus_id) REFERENCES buses(id)
        )
    ''')
    
    # 7. Database Migration (Scope Update & Data Source)
    cursor.execute("PRAGMA table_info(buses)")
    buses_columns = [col['name'] for col in cursor.fetchall()]
    if 'next_stop_id' not in buses_columns:
        cursor.execute("ALTER TABLE buses ADD COLUMN next_stop_id INTEGER")
    if 'operator' not in buses_columns:
        cursor.execute("ALTER TABLE buses ADD COLUMN operator TEXT")
    if 'service_type' not in buses_columns:
        cursor.execute("ALTER TABLE buses ADD COLUMN service_type TEXT")
    if 'data_source' not in buses_columns:
        cursor.execute("ALTER TABLE buses ADD COLUMN data_source TEXT DEFAULT 'OFFICIAL'")
    if 'gps_source' not in buses_columns:
        cursor.execute("ALTER TABLE buses ADD COLUMN gps_source TEXT DEFAULT 'Simulated'")
    if 'vehicle_type' not in buses_columns:
        cursor.execute("ALTER TABLE buses ADD COLUMN vehicle_type TEXT DEFAULT 'SIMULATED'")
    if 'driver_id' not in buses_columns:
        cursor.execute("ALTER TABLE buses ADD COLUMN driver_id INTEGER")

    if 'conductor_id' not in buses_columns:
        cursor.execute("ALTER TABLE buses ADD COLUMN conductor_id INTEGER")
    if 'source_url' not in buses_columns:
        cursor.execute("ALTER TABLE buses ADD COLUMN source_url TEXT")
    if 'source_name' not in buses_columns:
        cursor.execute("ALTER TABLE buses ADD COLUMN source_name TEXT")
    if 'source_type' not in buses_columns:
        cursor.execute("ALTER TABLE buses ADD COLUMN source_type TEXT")
    if 'verified_at' not in buses_columns:
        cursor.execute("ALTER TABLE buses ADD COLUMN verified_at TEXT")

        
    cursor.execute("PRAGMA table_info(routes)")
    routes_columns = [col['name'] for col in cursor.fetchall()]
    if 'operator' not in routes_columns:
        cursor.execute("ALTER TABLE routes ADD COLUMN operator TEXT")
    if 'service_type' not in routes_columns:
        cursor.execute("ALTER TABLE routes ADD COLUMN service_type TEXT")

    if 'data_source' not in routes_columns:
        cursor.execute("ALTER TABLE routes ADD COLUMN data_source TEXT DEFAULT 'OFFICIAL'")
    if 'source_url' not in routes_columns:
        cursor.execute("ALTER TABLE routes ADD COLUMN source_url TEXT")
    if 'source_name' not in routes_columns:
        cursor.execute("ALTER TABLE routes ADD COLUMN source_name TEXT")
    if 'source_type' not in routes_columns:
        cursor.execute("ALTER TABLE routes ADD COLUMN source_type TEXT")
    if 'verified_at' not in routes_columns:
        cursor.execute("ALTER TABLE routes ADD COLUMN verified_at TEXT")


    cursor.execute("PRAGMA table_info(stops)")
    stops_columns = [col['name'] for col in cursor.fetchall()]
    if 'area_type' not in stops_columns:
        cursor.execute("ALTER TABLE stops ADD COLUMN area_type TEXT")

    if 'data_source' not in stops_columns:
        cursor.execute("ALTER TABLE stops ADD COLUMN data_source TEXT DEFAULT 'OFFICIAL'")
    if 'source_url' not in stops_columns:
        cursor.execute("ALTER TABLE stops ADD COLUMN source_url TEXT")
    if 'source_name' not in stops_columns:
        cursor.execute("ALTER TABLE stops ADD COLUMN source_name TEXT")
    if 'source_type' not in stops_columns:
        cursor.execute("ALTER TABLE stops ADD COLUMN source_type TEXT")
    if 'verified_at' not in stops_columns:
        cursor.execute("ALTER TABLE stops ADD COLUMN verified_at TEXT")

        
    # Check if we need to add a default driver for testing
    cursor.execute("SELECT COUNT(*) FROM drivers")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO drivers (name, phone, password) VALUES ('Test Driver', '1234567890', 'password123')")
        cursor.execute("INSERT INTO conductors (name, phone, password) VALUES ('Test Conductor', '0987654321', 'password123')")
        
    # Only seed routes if empty. NEVER delete existing data.
    cursor.execute("SELECT COUNT(*) FROM routes")
    if cursor.fetchone()[0] == 0:
        print("Database is empty. Adding official sample records...")
        seed_data(cursor)
        
    # Save (commit) the changes and close the connection
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            passenger_id TEXT NOT NULL,
            bus_id INTEGER,
            route_id INTEGER,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'Open',
            admin_response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            FOREIGN KEY(bus_id) REFERENCES buses(id),
            FOREIGN KEY(route_id) REFERENCES routes(id)
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialization complete.")

def seed_data(cursor):
    """Inserts official RTC sample records into the database for testing inter-city connectivity."""
    
    # 1. APSRTC Route: Village -> Town -> City
    cursor.execute("INSERT INTO routes (route_name, source, destination, operator, service_type, data_source) VALUES (?, ?, ?, ?, ?, ?)", 
                   ('APSRTC Pallevelugu Corridor', 'Neerukonda', 'Vijayawada', 'APSRTC', 'Pallevelugu', 'OFFICIAL'))
    route1_id = cursor.lastrowid

    stops1 = [
        (route1_id, 'Neerukonda', 16.4385, 80.5152, 1, 'VILLAGE', 'OFFICIAL'),
        (route1_id, 'Kuragallu', 16.4312, 80.5367, 2, 'VILLAGE', 'OFFICIAL'),
        (route1_id, 'Mangalagiri Bus Station', 16.4316, 80.5658, 3, 'TOWN', 'OFFICIAL'),
        (route1_id, 'Tadepalli', 16.4719, 80.6127, 4, 'TOWN', 'OFFICIAL'),
        (route1_id, 'Vijayawada PNBS', 16.5062, 80.6480, 5, 'CITY', 'OFFICIAL')
    ]
    cursor.executemany("INSERT INTO stops (route_id, stop_name, latitude, longitude, stop_order, area_type, data_source) VALUES (?, ?, ?, ?, ?, ?, ?)", stops1)

    buses1 = [
        ('Simulated Vehicle', 'Demo Bus', route1_id, 16.4385, 80.5152, 'Active', 'APSRTC', 'Pallevelugu', 'SIMULATED')
    ]
    cursor.executemany("INSERT INTO buses (bus_number, bus_name, route_id, current_latitude, current_longitude, status, operator, service_type, data_source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", buses1)

    # 2. TGSRTC Route: Village -> Town -> City
    cursor.execute("INSERT INTO routes (route_name, source, destination, operator, service_type, data_source) VALUES (?, ?, ?, ?, ?, ?)", 
                   ('TGSRTC Pallevelugu Corridor', 'Moinabad', 'Hyderabad', 'TGSRTC', 'Pallevelugu', 'OFFICIAL'))
    route2_id = cursor.lastrowid

    stops2 = [
        (route2_id, 'Moinabad Village', 17.3308, 78.2721, 1, 'VILLAGE', 'OFFICIAL'),
        (route2_id, 'Chevella', 17.3106, 78.1362, 2, 'TOWN', 'OFFICIAL'),
        (route2_id, 'Mehdipatnam', 17.3934, 78.4414, 3, 'CITY', 'OFFICIAL'),
        (route2_id, 'MGBS Hyderabad', 17.3770, 78.4800, 4, 'CITY', 'OFFICIAL')
    ]
    cursor.executemany("INSERT INTO stops (route_id, stop_name, latitude, longitude, stop_order, area_type, data_source) VALUES (?, ?, ?, ?, ?, ?, ?)", stops2)

    buses2 = [
        ('Simulated Vehicle', 'Demo Bus', route2_id, 17.3308, 78.2721, 'Active', 'TGSRTC', 'Pallevelugu', 'SIMULATED')
    ]
    cursor.executemany("INSERT INTO buses (bus_number, bus_name, route_id, current_latitude, current_longitude, status, operator, service_type, data_source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", buses2)

