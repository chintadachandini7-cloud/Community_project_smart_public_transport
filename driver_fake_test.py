import requests
import time
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.post('https://127.0.0.1:5000/driver/login', data={'phone': '1234567890', 'password': 'password123'})

print("Starting trip for bus_id=4 (B-101)...")
res = s.post('https://127.0.0.1:5000/api/driver/start-trip', json={'bus_id': 4})
trip_id = res.json().get('trip_id')
print(f"Trip ID: {trip_id}")

print("Posting location 1: 18.369781, 83.809272")
s.post('https://127.0.0.1:5000/api/driver/location', json={
    'trip_id': trip_id,
    'bus_id': 4,
    'latitude': 18.369781,
    'longitude': 83.809272,
    'accuracy': 5
})

time.sleep(5)

print("Posting location 2: 18.369900, 83.809500")
s.post('https://127.0.0.1:5000/api/driver/location', json={
    'trip_id': trip_id,
    'bus_id': 4,
    'latitude': 18.369900,
    'longitude': 83.809500,
    'accuracy': 5
})
