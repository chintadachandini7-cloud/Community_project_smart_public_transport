import os
import shutil
import sqlite3
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
load_dotenv()

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None

# SECURITY FIX: a real Supabase *service_role* key (which bypasses all Row
# Level Security) was previously hardcoded here as a fallback default and
# committed to source control. That key must be treated as compromised —
# rotate it from the Supabase dashboard (Settings > API) immediately.
# The service role key is now REQUIRED to come from the environment only.
CORRECT_URL = 'https://vqbachaigfcxcjqcbisa.supabase.co'
SUPABASE_URL = os.environ.get('SUPABASE_URL', CORRECT_URL)
if 'bsia' in SUPABASE_URL:
    SUPABASE_URL = SUPABASE_URL.replace('bsia', 'bisa')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or ''

# Single admin whitelist used across the whole app (login.html/app.py import
# this rather than each keeping their own copy, which used to be able to
# drift out of sync).
ADMIN_EMAILS = ['chintadachandini2408@gmail.com']

# Default password seeded for the whitelisted admin account(s) the first
# time the app runs, so the unified login works without any Google/Firebase
# setup. CHANGE THIS after first login (see /api/auth/change-password or
# just update the `users` table).
DEFAULT_ADMIN_PASSWORD = 'Admin@123'
DEFAULT_PASSENGER_DEMO = {'email': 'passenger@demo.com', 'password': 'Passenger@123', 'name': 'Demo Passenger'}

supabase_client = None

def get_supabase():
    """Returns the live Supabase client instance."""
    global supabase_client
    if supabase_client is None and create_client and SUPABASE_URL and SUPABASE_KEY:
        try:
            supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            print(f"Failed to connect to Supabase: {e}")
    return supabase_client

# Base database filename (fallback for local dev)
DB_NAME = 'transport.db'

def get_db_path():
    """Returns a writable database path. In serverless environments like Vercel, copies transport.db to /tmp."""
    # Check if running in Vercel or in a read-only filesystem
    is_serverless = os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME')
    is_readonly = not os.access('.', os.W_OK)
    
    if is_serverless or is_readonly:
        tmp_db = os.path.join('/tmp', DB_NAME)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        src_db = os.path.join(base_dir, DB_NAME)
        if os.path.exists(src_db):
            if not os.path.exists(tmp_db) or (os.path.getsize(tmp_db) != os.path.getsize(src_db)):
                try:
                    shutil.copy2(src_db, tmp_db)
                except Exception as e:
                    print(f"Warning: Failed to copy {src_db} to {tmp_db}: {e}")
        return tmp_db
    return DB_NAME

def get_db_connection():
    """Connects to the SQLite database and returns the connection object."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path, timeout=15)
    # This allows us to access columns by name (e.g., row['bus_number'])
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    """Creates the database tables if they do not exist and adds sample data."""
    try:
        _init_db_worker()
    except Exception as e:
        print(f"Database initialization warning: {e}")

def _init_db_worker():
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
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            picture TEXT,
            role TEXT DEFAULT 'passenger',
            phone TEXT,
            password_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Migration: older databases created `users` before password_hash/phone existed
    cursor.execute("PRAGMA table_info(users)")
    users_columns = [col['name'] for col in cursor.fetchall()]
    if 'password_hash' not in users_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    if 'phone' not in users_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
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

    # Add email columns to drivers and conductors
    cursor.execute("PRAGMA table_info(drivers)")
    drivers_columns = [col['name'] for col in cursor.fetchall()]
    if 'email' not in drivers_columns:
        cursor.execute("ALTER TABLE drivers ADD COLUMN email TEXT")

    cursor.execute("PRAGMA table_info(conductors)")
    conductors_columns = [col['name'] for col in cursor.fetchall()]
    if 'email' not in conductors_columns:
        cursor.execute("ALTER TABLE conductors ADD COLUMN email TEXT")

        
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

    # --- DB CORRECTION: passwords for drivers/conductors were stored in
    # plain text. Hash any that aren't already hashed yet (idempotent —
    # safe to run on every startup; already-hashed rows are left alone).
    for _table in ('drivers', 'conductors'):
        for _row in cursor.execute(f"SELECT id, password FROM {_table}").fetchall():
            _pwd = _row['password']
            if _pwd and not (_pwd.startswith('pbkdf2:') or _pwd.startswith('scrypt:')):
                cursor.execute(f"UPDATE {_table} SET password=? WHERE id=?", (generate_password_hash(_pwd), _row['id']))

    # --- UNIFIED LOGIN: seed one password-based account per role so a
    # single login form (email/phone + password) works for every role,
    # including admin, without needing Google/Firebase to be configured.
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    if cursor.fetchone()[0] == 0:
        for _admin_email in ADMIN_EMAILS:
            cursor.execute(
                "INSERT OR IGNORE INTO users (email, name, role, password_hash) VALUES (?, 'Administrator', 'admin', ?)",
                (_admin_email, generate_password_hash(DEFAULT_ADMIN_PASSWORD))
            )
    cursor.execute("SELECT COUNT(*) FROM users WHERE email=?", (DEFAULT_PASSENGER_DEMO['email'],))
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT OR IGNORE INTO users (email, name, role, password_hash) VALUES (?, ?, 'passenger', ?)",
            (DEFAULT_PASSENGER_DEMO['email'], DEFAULT_PASSENGER_DEMO['name'], generate_password_hash(DEFAULT_PASSENGER_DEMO['password']))
        )
        
    # Sample seeding disabled — waiting for user dataset
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
    # --- DB CORRECTION: the database had zero indexes anywhere besides the
    # auto-indexes on UNIQUE columns — despite routes (~2.9k rows) and stops
    # (~56k rows) being queried constantly (by route_id, by source/destination,
    # by stop_order) for every trip-planning/live-tracking request. Add the
    # indexes the actual query patterns need.
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_routes_source ON routes(source)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_routes_destination ON routes(destination)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stops_route_order ON stops(route_id, stop_order)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stops_name ON stops(stop_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_buses_route ON buses(route_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trips_driver ON trips(driver_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trips_conductor ON trips(conductor_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trips_bus ON trips(bus_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trips_status ON trips(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_live_locations_trip ON live_locations(trip_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_complaints_passenger ON complaints(passenger_id)")
    # Partial unique index: many rows will have a NULL phone, only enforce
    # uniqueness once a phone number is actually set.
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone ON users(phone) WHERE phone IS NOT NULL")

    conn.commit()
    conn.close()
    print("Database initialization complete.")


# ==========================================
# UNIFIED AUTHENTICATION (one login for every role)
# ==========================================

def _password_ok(stored_hash, plain_password):
    if not stored_hash or not plain_password:
        return False
    try:
        return check_password_hash(stored_hash, plain_password)
    except Exception:
        return False


def hash_password(plain_password):
    return generate_password_hash(plain_password)


def authenticate_unified(identifier, password):
    """Single entry point for logging in as ANY role (passenger, driver,
    conductor, admin). Looks the identifier (email or phone) up across
    every role table and verifies the password against it, so the person
    logging in never has to pick a role first — the account determines it.

    Returns a dict {role, id, name, email, phone} on success, else None.
    """
    if not identifier or not password:
        return None
    identifier = identifier.strip()
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM drivers WHERE phone=? OR email=?", (identifier, identifier)).fetchone()
        if row and _password_ok(row['password'], password):
            return {'role': 'driver', 'id': row['id'], 'name': row['name'], 'email': row['email'], 'phone': row['phone']}

        row = conn.execute("SELECT * FROM conductors WHERE phone=? OR email=?", (identifier, identifier)).fetchone()
        if row and _password_ok(row['password'], password):
            return {'role': 'conductor', 'id': row['id'], 'name': row['name'], 'email': row['email'], 'phone': row['phone']}

        row = conn.execute("SELECT * FROM users WHERE email=? OR phone=?", (identifier, identifier)).fetchone()
        if row and _password_ok(row['password_hash'], password):
            role = row['role'] or 'passenger'
            # Defense in depth: never grant admin unless the email is
            # actually on the whitelist, even if the row says role=admin.
            if role == 'admin' and (row['email'] or '').lower() not in [e.lower() for e in ADMIN_EMAILS]:
                role = 'passenger'
            return {'role': role, 'id': row['id'], 'name': row['name'], 'email': row['email'], 'phone': row['phone']}
    finally:
        conn.close()
    return None


def register_passenger(name, email, phone, password):
    """Self-service sign-up for passengers through the same unified login
    page. Returns (user_id, error_message)."""
    if not email or not password:
        return None, 'Email and password are required.'
    conn = get_db_connection()
    try:
        existing = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if existing:
            return None, 'An account with this email already exists — try logging in instead.'
        cur = conn.execute(
            "INSERT INTO users (email, name, phone, role, password_hash) VALUES (?, ?, ?, 'passenger', ?)",
            (email.strip().lower(), name or email, (phone or '').strip() or None, hash_password(password))
        )
        conn.commit()
        return cur.lastrowid, None
    except sqlite3.IntegrityError:
        return None, 'That email or phone number is already registered.'
    finally:
        conn.close()

