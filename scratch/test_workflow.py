import requests

import urllib3
urllib3.disable_warnings()

BASE_URL = 'https://127.0.0.1:5000'

s = requests.Session()
s.verify = False

# 1. Login
res = s.post(f"{BASE_URL}/driver/login", data={'phone': '9999999991', 'password': 'password123'})
print("Login status:", res.status_code)

# 2. Lookup B-101
res = s.get(f"{BASE_URL}/api/bus/by-number/B-101")
print("Lookup B-101 status:", res.status_code)
bus_data = res.json()
bus_id = bus_data.get('bus_id')
print("Bus Data:", bus_data)

# 3. Start Trip
res = s.post(f"{BASE_URL}/api/driver/start-trip", json={'bus_id': bus_id})
print("Start Trip status:", res.status_code)
start_data = res.json()
print("Start Trip response:", start_data)
trip_id = start_data.get('trip_id')

if res.status_code == 400 and 'already have an active trip' in start_data.get('error', ''):
    # Try ending the active trip to proceed with testing
    print("Trying to end existing trip...")
    # we need the active trip ID. Let's find it.
    import sqlite3
    conn = sqlite3.connect('transport.db')
    active_trip = conn.execute("SELECT id FROM trips WHERE driver_id=1 AND status='Active'").fetchone()
    if active_trip:
        trip_id = active_trip[0]
        end_res = s.post(f"{BASE_URL}/api/driver/end-trip", json={'trip_id': trip_id})
        print("End existing trip status:", end_res.status_code)
        
        # Start Trip again
        res = s.post(f"{BASE_URL}/api/driver/start-trip", json={'bus_id': bus_id})
        start_data = res.json()
        print("Start Trip (Retry) response:", start_data)
        trip_id = start_data.get('trip_id')

# 4. Check if second Start Trip for same bus fails (Rule 14)
# (Needs another driver session to test, but we can just test if THIS driver can start another bus)
res2 = s.get(f"{BASE_URL}/api/bus/by-number/B-102")
bus_id2 = res2.json().get('bus_id')
res3 = s.post(f"{BASE_URL}/api/driver/start-trip", json={'bus_id': bus_id2})
print("Start Trip 2 (should fail):", res3.status_code, res3.json())

# 5. End Trip
res = s.post(f"{BASE_URL}/api/driver/end-trip", json={'trip_id': trip_id})
print("End Trip status:", res.status_code)
print("End Trip response:", res.json())
