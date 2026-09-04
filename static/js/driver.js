let watchId = null;
let foundBusId = null;

document.addEventListener('DOMContentLoaded', () => {
    const activeTripId = document.getElementById('active_trip_id')?.value;
    if (activeTripId) {
        startGPS(activeTripId);
    }
});

function selectFleetBus(busNo) {
    const input = document.getElementById('bus_number_input');
    if (input) {
        input.value = busNo;
        lookupBus();
    }
}

async function lookupBus() {
    const rawBusNo = document.getElementById('bus_number_input').value.trim();
    if(!rawBusNo) return;
    
    document.getElementById('search-error').style.display = 'none';
    const cleanBusNo = rawBusNo.replace(/\s+/g, '');
    
    try {
        const res = await fetch(`/api/bus/by-number/${encodeURIComponent(cleanBusNo)}`);
        const data = await res.json();
        
        if(res.ok) {
            foundBusId = data.bus_id;
            
            document.getElementById('bus-search-section').style.display = 'none';
            document.getElementById('bus-confirm-section').style.display = 'block';
            
            document.getElementById('conf_bus_no').innerText = data.bus_number;
            document.getElementById('conf_bus_name').innerText = data.bus_name || 'N/A';
            document.getElementById('conf_op').innerText = data.operator;
            document.getElementById('conf_svc').innerText = data.service_type;
            document.getElementById('conf_area').innerText = data.area_type || 'N/A';
            document.getElementById('conf_route').innerText = data.route_name;
            document.getElementById('conf_src').innerText = data.source;
            document.getElementById('conf_dst').innerText = data.destination;
        } else {
            document.getElementById('search-error').innerText = data.error || 'Bus not found.';
            document.getElementById('search-error').style.display = 'block';
        }
    } catch (e) {
        document.getElementById('search-error').innerText = 'Connection error.';
        document.getElementById('search-error').style.display = 'block';
    }
}

function cancelLookup() {
    foundBusId = null;
    document.getElementById('bus-search-section').style.display = 'block';
    document.getElementById('bus-confirm-section').style.display = 'none';
    document.getElementById('bus_number_input').value = '';
}

async function confirmAndStartTrip() {
    if(!foundBusId) return;
    
    try {
        const res = await fetch('/api/driver/start-trip', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({bus_id: foundBusId})
        });
        const data = await res.json();
        
        if(res.ok && data.trip_id) {
            // Reload page to enter active trip mode
            location.reload();
        } else {
            alert(data.error || "Failed to start trip");
        }
    } catch(e) {
        console.error("Failed to start trip", e);
        alert("Failed to start trip");
    }
}

async function endTrip(tripId) {
    if(confirm('Are you sure you want to end this trip and stop GPS tracking?')) {
        if(watchId) {
            navigator.geolocation.clearWatch(watchId);
            watchId = null;
        }
        
        try {
            await fetch('/api/driver/end-trip', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({trip_id: tripId})
            });
            location.reload();
        } catch(e) {
            console.error(e);
        }
    }
}

function startGPS(tripId) {
    if (!navigator.geolocation) {
        document.getElementById('gps-status').innerText = 'Geolocation not supported by browser.';
        document.getElementById('gps-status').style.color = 'red';
        return;
    }

    document.getElementById('gps-status').innerText = 'Requesting Permission...';
    
    watchId = navigator.geolocation.watchPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            const acc = position.coords.accuracy;
            
            document.getElementById('gps-status').innerText = 'LIVE STREAMING';
            document.getElementById('gps-status').style.color = 'green';
            document.getElementById('gps-lat').innerText = lat.toFixed(6);
            document.getElementById('gps-lng').innerText = lng.toFixed(6);
            document.getElementById('gps-acc').innerText = acc.toFixed(1) + ' meters';
            document.getElementById('gps-time').innerText = new Date().toLocaleTimeString();
            
            sendLocationToBackend(tripId, lat, lng, acc);
        },
        (error) => {
            document.getElementById('gps-status').innerText = 'Error: ' + error.message;
            document.getElementById('gps-status').style.color = 'red';
        },
        { enableHighAccuracy: true, maximumAge: 0, timeout: 5000 }
    );
}

function sendLocationToBackend(tripId, lat, lng, acc) {
    const busId = document.getElementById('assigned_bus_id').value;
    fetch('/api/driver/location', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            trip_id: tripId,
            bus_id: busId,
            latitude: lat,
            longitude: lng,
            accuracy: acc
        })
    }).catch(console.error);
}
