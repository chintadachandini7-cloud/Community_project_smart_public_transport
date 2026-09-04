#!/usr/bin/env python3
"""
import_apsrtc_gtfs.py
=====================
Reads the official APSRTC GTFS dataset from dataset/apsrtc/ and loads:
  - Routes into local SQLite `routes` table
  - Stops (with stop_times schedule) into local SQLite `stops` table
  - Buses into Supabase `buses` table
  - One active test bus with assignment + live location into Supabase

Usage:
    python import_apsrtc_gtfs.py
"""

import csv
import os
import sys
from collections import defaultdict
from datetime import date

# Ensure project modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database

GTFS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dataset', 'apsrtc')

# ─── Helpers ───────────────────────────────────────────────────────────

def read_gtfs(filename):
    """Read a GTFS .txt file and return list of dicts."""
    path = os.path.join(GTFS_DIR, filename)
    if not os.path.exists(path):
        print(f"  WARNING: {path} not found, skipping.")
        return []
    with open(path, encoding='utf-8') as f:
        return list(csv.DictReader(f))

# ─── 1. Parse GTFS Data ───────────────────────────────────────────────

def parse_gtfs():
    """Parse all GTFS files and return structured data."""
    print("📂 Parsing GTFS data from", GTFS_DIR)

    # Stops master
    raw_stops = read_gtfs('stops.txt')
    stops_lookup = {}
    for s in raw_stops:
        stops_lookup[s['stop_id']] = {
            'stop_id': s['stop_id'],
            'stop_name': s['stop_name'].strip(),
            'lat': float(s['stop_lat']),
            'lon': float(s['stop_lon']),
        }
    print(f"  ✅ Loaded {len(stops_lookup)} stops")

    # Trips -> route mapping (trip_id == route_id in this feed)
    raw_trips = read_gtfs('trips.txt')
    trip_to_route = {}
    for t in raw_trips:
        trip_to_route[t['trip_id']] = t['route_id']
    print(f"  ✅ Loaded {len(trip_to_route)} trips")

    # Stop times -> grouped by route
    raw_stop_times = read_gtfs('stop_times.txt')
    route_stops = defaultdict(list)
    for st in raw_stop_times:
        tid = st['trip_id']
        rid = trip_to_route.get(tid, tid)
        stop_info = stops_lookup.get(st['stop_id'])
        if not stop_info:
            continue
        route_stops[rid].append({
            'seq': int(st['stop_sequence']),
            'stop_id': st['stop_id'],
            'stop_name': stop_info['stop_name'],
            'lat': stop_info['lat'],
            'lon': stop_info['lon'],
            'arrival_time': st['arrival_time'],
            'departure_time': st['departure_time'],
        })
    # Sort each route's stops by sequence
    for rid in route_stops:
        route_stops[rid].sort(key=lambda x: x['seq'])
    print(f"  ✅ Built stop sequences for {len(route_stops)} routes")

    # Build route summaries (origin -> destination)
    route_summaries = {}
    for rid, st_list in route_stops.items():
        if not st_list:
            continue
        route_summaries[rid] = {
            'route_id': rid,
            'source': st_list[0]['stop_name'],
            'destination': st_list[-1]['stop_name'],
            'num_stops': len(st_list),
        }
    print(f"  ✅ Built {len(route_summaries)} route summaries")

    return stops_lookup, route_stops, route_summaries


# ─── 2. Load into SQLite ──────────────────────────────────────────────

def load_sqlite(stops_lookup, route_stops, route_summaries):
    """Insert routes and stops into the local SQLite database."""
    print("\n🗄️  Loading data into SQLite...")

    # Initialize DB (creates tables if needed)
    database.init_db()
    conn = database.get_db_connection()
    cursor = conn.cursor()

    # Clear existing data (user requested: remove mock data, load real dataset)
    cursor.execute("DELETE FROM stops")
    cursor.execute("DELETE FROM routes")
    cursor.execute("DELETE FROM buses")
    conn.commit()
    print("  🧹 Cleared existing routes, stops, and buses from SQLite")

    # Insert routes
    route_id_map = {}  # GTFS route_id -> SQLite auto-increment id
    route_count = 0
    for rid, summary in route_summaries.items():
        route_name = f"{summary['source']} - {summary['destination']}"
        cursor.execute(
            """INSERT INTO routes (route_name, source, destination, operator, service_type, data_source, source_name, source_type, verified_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (route_name, summary['source'], summary['destination'],
             'APSRTC', 'Standard', 'OFFICIAL', 'APSRTC GTFS Open Data', 'Government Transit Feed', '2026-09-04')
        )
        route_id_map[rid] = cursor.lastrowid
        route_count += 1
    conn.commit()
    print(f"  ✅ Inserted {route_count} routes")

    # Insert stops (for each route, insert its ordered stops)
    stop_count = 0
    for rid, st_list in route_stops.items():
        sqlite_route_id = route_id_map.get(rid)
        if not sqlite_route_id:
            continue
        for stop in st_list:
            cursor.execute(
                """INSERT INTO stops (route_id, stop_name, latitude, longitude, stop_order, scheduled_arrival_time, data_source, source_name, source_type, verified_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (sqlite_route_id, stop['stop_name'], stop['lat'], stop['lon'],
                 stop['seq'], stop['arrival_time'],
                 'OFFICIAL', 'APSRTC GTFS Open Data', 'Government Transit Feed', '2026-09-04')
            )
            stop_count += 1
    conn.commit()
    print(f"  ✅ Inserted {stop_count} stops across all routes")

    conn.close()
    return route_id_map


# ─── 3. Load into Supabase ────────────────────────────────────────────

# Test bus and fleet configuration
FLEET = [
    {'bus_number': 'AP 16 Z 2209', 'route_number': '02209', 'route_name': 'VIJAYAWADA - AMALAPURAM', 'bus_type': 'Super Luxury', 'capacity': 45},
    {'bus_number': 'AP 04 Z 1004', 'route_number': '01004', 'route_name': 'NELLORE - TIRUPATHI', 'bus_type': 'Express', 'capacity': 52},
    {'bus_number': 'AP 26 Z 1025', 'route_number': '01025', 'route_name': 'TIRUPATHI - NELLORE', 'bus_type': 'Garuda', 'capacity': 48},
    {'bus_number': 'AP 37 Z 2201', 'route_number': '02201', 'route_name': 'VSP MADDILAPALEM - AMALAPURAM', 'bus_type': 'AC Deluxe', 'capacity': 40},
    {'bus_number': 'AP 39 Z 0000', 'route_number': '00000', 'route_name': 'SADASIVA KONA - PUTTUR', 'bus_type': 'Palle Velugu', 'capacity': 55},
    {'bus_number': 'AP 05 Z 2220', 'route_number': '02220', 'route_name': 'AMALAPURAM - VIJAYAWADA', 'bus_type': 'Standard', 'capacity': 52},
    {'bus_number': 'AP 21 Z 1445', 'route_number': '01445', 'route_name': 'MEHDIPATNAM - AUTONAGAR', 'bus_type': 'Amaravati', 'capacity': 45},
    {'bus_number': 'AP 12 Z 2215', 'route_number': '02215', 'route_name': 'VSP MADDILAPALEM - AMALAPURAM', 'bus_type': 'Express', 'capacity': 50},
]

ACTIVE_TEST_BUS = 'AP 16 Z 2209'  # Vijayawada -> Amalapuram

# Existing driver/conductor IDs from Supabase
DRIVER_ID = 'd1000000-0000-0000-0000-000000000001'   # Ramesh Kumar
CONDUCTOR_ID = 'c1000000-0000-0000-0000-000000000001'  # Srikanth Babu


def load_supabase(route_id_map):
    """Insert buses, assignment, and live location into Supabase."""
    sb = database.get_supabase()
    if not sb:
        print("\n⚠️  Supabase client not available. Skipping Supabase load.")
        return

    print("\n☁️  Loading data into Supabase...")

    # Clear existing buses (user requested clean slate)
    try:
        existing = sb.table('buses').select('id').execute()
        if existing.data:
            for bus in existing.data:
                # Also clean related records
                sb.table('bus_locations').delete().eq('bus_id', bus['id']).execute()
                sb.table('bus_assignments').delete().eq('bus_id', bus['id']).execute()
            sb.table('buses').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        print("  🧹 Cleared existing buses, locations, and assignments from Supabase")
    except Exception as e:
        print(f"  ⚠️  Cleanup warning: {e}")

    # Insert fleet buses
    bus_id_map = {}  # bus_number -> UUID
    for bus_data in FLEET:
        try:
            res = sb.table('buses').insert({
                'bus_number': bus_data['bus_number'],
                'route_number': bus_data['route_number'],
                'route_name': bus_data['route_name'],
                'bus_type': bus_data['bus_type'],
                'capacity': bus_data['capacity'],
                'status': 'Active',
            }).execute()
            if res.data:
                bus_id_map[bus_data['bus_number']] = res.data[0]['id']
                print(f"  🚌 Inserted bus {bus_data['bus_number']} -> {res.data[0]['id']}")
        except Exception as e:
            print(f"  ❌ Failed to insert {bus_data['bus_number']}: {e}")

    # Also insert buses into SQLite for the local fallback
    conn = database.get_db_connection()
    cursor = conn.cursor()
    for bus_data in FLEET:
        sqlite_route_id = route_id_map.get(bus_data['route_number'])
        cursor.execute(
            """INSERT INTO buses (bus_number, bus_name, route_id, current_latitude, current_longitude, status, operator, service_type, data_source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (bus_data['bus_number'], bus_data['route_name'], sqlite_route_id,
             16.5062, 80.6480, 'Active', 'APSRTC', bus_data['bus_type'], 'OFFICIAL')
        )
    conn.commit()
    conn.close()
    print(f"  ✅ Synced {len(FLEET)} buses to SQLite fallback")

    # Set up active test bus
    test_bus_id = bus_id_map.get(ACTIVE_TEST_BUS)
    if not test_bus_id:
        print("  ❌ Active test bus not found in inserted fleet. Skipping assignment.")
        return

    # Create bus assignment (driver + conductor)
    try:
        sb.table('bus_assignments').insert({
            'bus_id': test_bus_id,
            'driver_id': DRIVER_ID,
            'conductor_id': CONDUCTOR_ID,
            'shift': 'Full Day',
            'assigned_date': str(date.today()),
            'status': 'Active',
        }).execute()
        print(f"  👨‍✈️ Assigned Driver Ramesh Kumar + Conductor Srikanth Babu to {ACTIVE_TEST_BUS}")
    except Exception as e:
        print(f"  ❌ Assignment failed: {e}")

    # Create live location (simulate bus at Benz Circle, Vijayawada)
    try:
        sb.table('bus_locations').upsert({
            'bus_id': test_bus_id,
            'latitude': 16.49825,
            'longitude': 80.65427,
            'speed': 42.0,
            'heading': 45.0,
            'current_stop': 'BENZCIRCLE ELR BUS STOP',
            'next_stop': 'RAMAVARAPUPADU RING-VJA',
        }, on_conflict='bus_id').execute()
        print(f"  📍 Live location set: Benz Circle, Vijayawada (16.49825, 80.65427) @ 42 km/h")
    except Exception as e:
        print(f"  ❌ Live location failed: {e}")

    # Update the test bus status to 'Active' in Supabase
    try:
        sb.table('buses').update({'status': 'Active'}).eq('id', test_bus_id).execute()
    except Exception:
        pass

    print(f"\n✅ Active test bus configured: {ACTIVE_TEST_BUS}")
    print(f"   Route: 02209 (VIJAYAWADA -> AMALAPURAM, 13 stops)")
    print(f"   Driver: Ramesh Kumar (DRV-1001)")
    print(f"   Conductor: Srikanth Babu (CND-2001)")
    print(f"   Position: Benz Circle, Vijayawada")


# ─── 4. Main ──────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  APSRTC GTFS Dataset Import")
    print("=" * 60)

    # Verify dataset exists
    if not os.path.isdir(GTFS_DIR):
        print(f"❌ GTFS directory not found: {GTFS_DIR}")
        print("   Please extract apsrtc dataset.zip to dataset/apsrtc/ first.")
        sys.exit(1)

    # Parse
    stops_lookup, route_stops, route_summaries = parse_gtfs()

    # Load SQLite
    route_id_map = load_sqlite(stops_lookup, route_stops, route_summaries)

    # Load Supabase
    load_supabase(route_id_map)

    print("\n" + "=" * 60)
    print("  ✅ APSRTC GTFS import complete!")
    print("=" * 60)
    print(f"\n  Routes:  {len(route_summaries)}")
    print(f"  Stops:   {sum(len(v) for v in route_stops.values())}")
    print(f"  Buses:   {len(FLEET)}")
    print(f"  Test Bus: {ACTIVE_TEST_BUS} (VIJAYAWADA -> AMALAPURAM)")
    print(f"\n  Start the server with: python app.py")
    print(f"  Admin:    http://127.0.0.1:5000/admin/dashboard")
    print(f"  Passenger: http://127.0.0.1:5000/user/dashboard")


if __name__ == '__main__':
    main()
