function computeETA(lat1, lon1, lat2, lon2) {
    const R = 6371; // Radius of earth in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    const distanceKm = R * c;
    const speedKmh = 30;
    const timeHours = distanceKm / speedKmh;
    const timeMinutes = Math.ceil(timeHours * 60);
    return { distance: distanceKm.toFixed(1), minutes: timeMinutes };
}

let currentBusId = null;

async function lookupBus() {
    const rawBusNo = document.getElementById('bus_number_input').value.trim();
    if(!rawBusNo) return;
    
    const errDiv = document.getElementById('search-error');
    errDiv.style.display = 'none';
    const cleanBusNo = rawBusNo.replace(/\s+/g, '');
    
    try {
        const res = await fetch(`/api/bus/by-number/${encodeURIComponent(cleanBusNo)}`);
        const data = await res.json();
        
        if(res.ok) {
            currentBusId = data.bus_id;
            document.getElementById('conf_bus_no').innerText = data.bus_number;
            document.getElementById('conf_bus_name').innerText = data.bus_name || 'N/A';
            document.getElementById('conf_op').innerText = data.operator || 'N/A';
            document.getElementById('conf_svc').innerText = data.service_type || 'N/A';
            document.getElementById('conf_area').innerText = data.area_type || 'N/A';
            document.getElementById('conf_route').innerText = data.route_name || 'N/A';
            document.getElementById('conf_src').innerText = data.source || 'N/A';
            document.getElementById('conf_dst').innerText = data.destination || 'N/A';
            
            document.getElementById('bus-search-section').style.display = 'none';
            document.getElementById('bus-confirm-section').style.display = 'block';
        } else {
            errDiv.innerText = data.error;
            errDiv.style.display = 'block';
        }
    } catch(e) {
        errDiv.innerText = "Network error. Try again.";
        errDiv.style.display = 'block';
    }
}

function cancelLookup() {
    currentBusId = null;
    document.getElementById('bus_number_input').value = '';
    document.getElementById('bus-search-section').style.display = 'block';
    document.getElementById('bus-confirm-section').style.display = 'none';
}

async function joinTrip() {
    if(!currentBusId) return;
    try {
        const res = await fetch('/api/conductor/join-trip', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({bus_id: currentBusId})
        });
        const data = await res.json();
        if(res.ok) {
            window.location.reload();
        } else {
            alert(data.error);
        }
    } catch(e) {
        alert('Network error. Try again.');
    }
}

async function leaveTrip() {
    if(confirm('Are you sure you want to leave this trip?')) {
        try {
            const res = await fetch('/api/conductor/leave-trip', { method: 'POST' });
            if(res.ok) {
                window.location.reload();
            }
        } catch(e) {
            alert('Network error. Try again.');
        }
    }
}

// Polling loop for active trip
let trackingInterval = null;

async function pollTrackingData() {
    const busIdEl = document.getElementById('active_bus_id');
    if(!busIdEl) return;
    
    const busId = parseInt(busIdEl.value);
    
    try {
        const res = await fetch('/api/tracking_data');
        const data = await res.json();
        
        // We reuse trackingData from passenger.js scope for computeETA
        window.trackingData = data; 
        
        const bus = data.buses.find(b => b.id === busId);
        if(bus) {
            // Update UI
            if(bus.delay_status === 'DELAYED') {
                document.getElementById('cond-delay').innerHTML = `<span style="color:#dc3545;">🔴 DELAYED (${bus.delay_minutes} min)</span>`;
            } else if (bus.delay_status === 'ON TIME') {
                document.getElementById('cond-delay').innerHTML = `<span style="color:#28a745;">🟢 ON TIME</span>`;
            } else {
                document.getElementById('cond-delay').innerText = bus.delay_status || 'N/A';
            }
            
            if(bus.next_stop_id) {
                const nextStop = data.stops.find(s => s.id == bus.next_stop_id);
                if(nextStop) {
                    document.getElementById('cond-next-stop').innerText = nextStop.stop_name;
                    
                    if(bus.current_latitude && bus.current_longitude) {
                        const result = computeETA(bus.current_latitude, bus.current_longitude, nextStop.latitude, nextStop.longitude);
                        let etaText = 'Due';
                        if(result.minutes > 0) etaText = `${result.minutes} min (${result.distance} km)`;
                        else etaText = `Due (${result.distance} km)`;
                        document.getElementById('cond-eta').innerText = etaText;
                    }
                }
            }
        }
    } catch(e) {
        console.error("Polling error", e);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if(document.getElementById('active_bus_id')) {
        pollTrackingData();
        trackingInterval = setInterval(pollTrackingData, 3000);
    }
});
