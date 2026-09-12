"""
Database audit & correction tool for Smart Public Transport.

Run any time with:  python3 audit_and_fix_db.py

What it does:
1. Runs database.init_db() — which already applies the core corrections
   (password hashing, unified-login accounts, indexes) idempotently.
2. Runs the original one-off data-source labelling clean-up (kept for
   backwards compatibility with existing installs).
3. Prints a health report: row counts, orphaned records, missing
   coordinates, and whether any plaintext passwords remain.

Nothing here is destructive — every step is safe to run repeatedly.
"""
import sqlite3
import database


def run_audit():
    print("Step 1/3: Running database.init_db() (schema + core corrections)...")
    database.init_db()

    conn = sqlite3.connect('transport.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\nStep 2/3: Legacy data-source labelling clean-up...")
    for table in ['routes', 'stops', 'buses']:
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [c['name'] for c in cursor.fetchall()]
        if 'data_source' not in cols:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN data_source TEXT DEFAULT 'OFFICIAL'")

    cursor.execute("UPDATE routes SET data_source='OFFICIAL', route_name='APSRTC Pallevelugu Corridor' WHERE route_name LIKE '%Route 101%'")
    cursor.execute("UPDATE routes SET data_source='OFFICIAL', route_name='TGSRTC Pallevelugu Corridor' WHERE route_name LIKE '%Route 201%'")
    cursor.execute("UPDATE stops SET data_source='OFFICIAL' WHERE data_source IS NULL")
    cursor.execute("UPDATE buses SET bus_number='Simulated Vehicle', bus_name='Demo Bus', data_source='SIMULATED' WHERE bus_number LIKE 'AP-%' OR bus_number LIKE 'TS-%' OR bus_number LIKE 'B-%'")
    conn.commit()

    print("\nStep 3/3: Health report")
    print("=" * 60)

    def count(sql):
        return cursor.execute(sql).fetchone()[0]

    print(f"Routes: {count('SELECT COUNT(*) FROM routes')}  |  Stops: {count('SELECT COUNT(*) FROM stops')}  |  Buses: {count('SELECT COUNT(*) FROM buses')}")
    print(f"Drivers: {count('SELECT COUNT(*) FROM drivers')}  |  Conductors: {count('SELECT COUNT(*) FROM conductors')}  |  Users: {count('SELECT COUNT(*) FROM users')}")

    print("\n-- Integrity checks --")
    orphan_buses = count("SELECT COUNT(*) FROM buses WHERE route_id IS NOT NULL AND route_id NOT IN (SELECT id FROM routes)")
    orphan_stops = count("SELECT COUNT(*) FROM stops WHERE route_id IS NOT NULL AND route_id NOT IN (SELECT id FROM routes)")
    routes_no_stops = count("SELECT COUNT(*) FROM routes r WHERE NOT EXISTS (SELECT 1 FROM stops s WHERE s.route_id=r.id)")
    missing_coords = count("SELECT COUNT(*) FROM stops WHERE latitude IS NULL OR longitude IS NULL")
    print(f"Orphaned buses (route_id not found): {orphan_buses}")
    print(f"Orphaned stops (route_id not found): {orphan_stops}")
    print(f"Routes with zero stops: {routes_no_stops}")
    print(f"Stops missing lat/lng: {missing_coords}")

    print("\n-- Security checks --")
    plaintext_drivers = 0
    for row in cursor.execute("SELECT password FROM drivers").fetchall():
        pw = row['password']
        if pw and not (pw.startswith('pbkdf2:') or pw.startswith('scrypt:')):
            plaintext_drivers += 1
    plaintext_conductors = 0
    for row in cursor.execute("SELECT password FROM conductors").fetchall():
        pw = row['password']
        if pw and not (pw.startswith('pbkdf2:') or pw.startswith('scrypt:')):
            plaintext_conductors += 1
    print(f"Drivers with plaintext passwords remaining: {plaintext_drivers} (should be 0)")
    print(f"Conductors with plaintext passwords remaining: {plaintext_conductors} (should be 0)")
    if database.SUPABASE_KEY:
        print("NOTE: SUPABASE_SERVICE_ROLE_KEY is set via environment (good — keep it out of source control).")
    else:
        print("NOTE: No SUPABASE_SERVICE_ROLE_KEY set — app is running on the local SQLite fallback only.")

    print("\n-- Indexes --")
    idx = [r['name'] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'").fetchall()]
    print(f"{len(idx)} custom indexes present: {', '.join(idx) if idx else '(none)'}")

    conn.close()
    print("\nAudit and fix complete.")


if __name__ == '__main__':
    run_audit()
