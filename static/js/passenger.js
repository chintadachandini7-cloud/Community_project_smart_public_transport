let map;
let busMarkers = {};
let stopMarkers = {};
let trackingData = {};
let selectedBusId = null;
let simulationInterval = null;
let currentRoutePolyline = null;
let routeStopMarkers = [];
let lastRenderedNextStopId = null;

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    fetchTrackingData();
    
    // Start real GPS polling
    setInterval(pollRealGPS, 3000);
    
    document.getElementById('bus-selector').addEventListener('change', (e) => {
        selectBus(e.target.value);
    });
});

function initMap() {
    // Center roughly between Vijayawada and Hyderabad
    map = L.map('map').setView([16.8, 79.5], 8);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
}

async function fetchTrackingData() {
    try {
        const res = await fetch('/api/tracking_data');
        trackingData = await res.json();
        applyFilters(); // This will draw stops and buses based on default "All" filters
        populateUpdates();
    } catch (e) {
        console.error("Failed to load tracking data:", e);
    }
}

// Draw Bus Stops with styling based on area type
function drawStops(filteredStops) {
    // Clear existing markers
    Object.values(stopMarkers).forEach(m => map.removeLayer(m));
    stopMarkers = {};

    filteredStops.forEach(s => {
        if(s.latitude && s.longitude) {
            let color = '#007bff'; // default blue
            let radius = 6;
            
            if (s.area_type === 'VILLAGE') { color = '#28a745'; radius = 4; } // Green, smaller
            else if (s.area_type === 'TOWN') { color = '#ffc107'; radius = 6; } // Yellow, medium
            else if (s.area_type === 'CITY') { color = '#dc3545'; radius = 8; } // Red, larger

            const stopIcon = L.divIcon({
                className: 'custom-div-icon',
                html: `<div style='background-color:${color}; width:${radius*2}px; height:${radius*2}px; border-radius:50%; border:2px solid white;'></div>`,
                iconSize: [radius*2+4, radius*2+4],
                iconAnchor: [radius+2, radius+2]
            });

            const marker = L.marker([s.latitude, s.longitude], {icon: stopIcon}).addTo(map);
            marker.bindPopup(`<b>${s.stop_name}</b><br>Type: ${s.area_type || 'Unknown'}`);
            stopMarkers[s.id] = marker;
        }
    });
}

function drawBuses(filteredBuses) {
    // Clear existing
    Object.values(busMarkers).forEach(m => map.removeLayer(m));
    busMarkers = {};

    const busIcon = L.divIcon({
        className: 'custom-div-icon',
        html: "<div style='background-color:#343a40; width:20px; height:20px; border-radius:5px; border:2px solid white; display:flex; justify-content:center; align-items:center;'><span style='color:white; font-size:10px; font-weight:bold;'>B</span></div>",
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });

    filteredBuses.forEach(b => {
        if(b.current_latitude && b.current_longitude) {
            const marker = L.marker([b.current_latitude, b.current_longitude], {icon: busIcon, zIndexOffset: 1000}).addTo(map);
            const gpsText = b.gps_source === 'Real' ? '<span style="color:green; font-weight:bold;">GPS: LIVE</span>' : '<span style="color:red;">GPS: SIMULATED</span>';
            marker.bindPopup(`<b>${b.operator || 'Bus'} - ${b.bus_number}</b><br>Service: ${b.service_type || 'Standard'}<br>${gpsText}`);
            busMarkers[b.id] = marker;
        }
    });
}

// -----------------------------------------
// FILTERING LOGIC
// -----------------------------------------
window.applyFilters = function() {
    const searchFilter = (document.getElementById('filter-search').value || '').toLowerCase();
    const operatorFilter = document.getElementById('filter-operator').value;
    const areaFilter = document.getElementById('filter-area').value;
    const serviceFilter = document.getElementById('filter-service').value;
    const statusFilter = document.getElementById('filter-status').value;
    
    // Filter Routes
    let validRoutes = trackingData.routes.filter(r => {
        let opMatch = operatorFilter === 'All' || r.operator === operatorFilter;
        let srvMatch = serviceFilter === 'All' || (r.service_type && r.service_type.includes(serviceFilter));
        let searchMatch = searchFilter === '' || 
                          (r.route_name || '').toLowerCase().includes(searchFilter) ||
                          (r.operator || '').toLowerCase().includes(searchFilter);
        return opMatch && srvMatch && searchMatch;
    });
    let validRouteIds = validRoutes.map(r => r.id);

    // Filter Stops
    let filteredStops = trackingData.stops.filter(s => {
        let opMatch = validRouteIds.includes(s.route_id);
        let areaMatch = areaFilter === 'All' || (s.area_type && s.area_type.toUpperCase() === areaFilter.toUpperCase());
        let searchMatch = searchFilter === '' || 
                          (s.stop_name || '').toLowerCase().includes(searchFilter);
        
        // If the stop matches the search directly, we include it even if the route didn't natively match the search (but it must still match operator/area rules).
        // For simplicity, let's just say a stop is valid if its route is valid OR its name matches the search (and operator/area matches)
        let baseMatch = opMatch && areaMatch;
        return baseMatch; 
    });
    
    // If search text is present, also allow buses that match the search directly
    let filteredBuses = trackingData.buses.filter(b => {
        let opMatch = operatorFilter === 'All' || b.operator === operatorFilter;
        let srvMatch = serviceFilter === 'All' || (b.service_type && b.service_type.includes(serviceFilter));
        
        let statMatch = true;
        if(statusFilter === 'Live') statMatch = b.status === 'Active Trip';
        else if(statusFilter === 'Delayed') statMatch = b.delay_status === 'DELAYED';
        else if(statusFilter === 'On Time') statMatch = b.delay_status === 'ON TIME';
        
        let searchMatch = searchFilter === '' || 
                          (b.bus_number || '').toLowerCase().includes(searchFilter) ||
                          (b.bus_name || '').toLowerCase().includes(searchFilter) ||
                          validRouteIds.includes(b.route_id); // includes buses on searched routes
                          
        return opMatch && srvMatch && statMatch && searchMatch;
    });

    
    if (selectedBusId) {
        const bus = trackingData.buses.find(b => b.id == selectedBusId);
        if (bus) {
            drawRouteMap(bus);
            drawBuses(filteredBuses);
            populateBusSelector(filteredBuses);
            document.getElementById('bus-selector').value = selectedBusId;
            return;
        }
    }

    // Default: No bus selected
    if(currentRoutePolyline) { map.removeLayer(currentRoutePolyline); currentRoutePolyline = null; }
    routeStopMarkers.forEach(m => map.removeLayer(m));
    routeStopMarkers = [];
    
    drawStops(filteredStops);
    drawBuses(filteredBuses);
    populateBusSelector(filteredBuses);
    
    // Adjust map view if there are markers
    if (filteredStops.length > 0) {
        const group = new L.featureGroup(Object.values(stopMarkers));
        try { map.fitBounds(group.getBounds().pad(0.1)); } catch(e) {}
    }
}

function populateBusSelector(filteredBuses) {
    const sel = document.getElementById('bus-selector');
    sel.innerHTML = '<option value="">-- Choose a Bus to Track --</option>';
    filteredBuses.forEach(b => {
        sel.innerHTML += `<option value="${b.id}">${b.operator || ''} ${b.bus_number} - ${b.bus_name}</option>`;
    });
}

function populateUpdates() {
    const list = document.getElementById('updates-list');
    list.innerHTML = '';
    if(trackingData.updates.length === 0) {
        list.innerHTML = '<li>No active updates.</li>';
        return;
    }
    trackingData.updates.forEach(u => {
        list.innerHTML += `<li style="margin-bottom:10px; border-bottom:1px solid #eee; padding-bottom:5px;">
            <strong>${u.title}</strong><br>
            <small>${u.message}</small>
        </li>`;
    });
}

function selectBus(busId) {
    selectedBusId = busId;
    const simBtn = document.getElementById('simulate-btn');
    
    if(!busId) {
        document.getElementById('bus-info').style.display = 'none';
        document.getElementById('eta-info').style.display = 'none';
        simBtn.style.display = 'none';
        if(simulationInterval) toggleSimulation();
        return;
    }

    const bus = trackingData.buses.find(b => b.id == busId);
    if(bus) {
        document.getElementById('bus-info').style.display = 'block';
        document.getElementById('eta-info').style.display = 'block';
        
        // Hide simulation button if it's a real live GPS trip
        if(bus.gps_source === 'Real') {
            simBtn.style.display = 'none';
            if(simulationInterval) toggleSimulation();
        } else {
            simBtn.style.display = 'block';
        }
        
        document.getElementById('info-bus-number').innerText = bus.bus_number;
        document.getElementById('info-bus-name').innerText = bus.bus_name;
        document.getElementById('info-bus-operator').innerText = bus.operator || 'Unknown';
        document.getElementById('info-bus-service').innerText = bus.service_type || 'Unknown';
        
        // Handle Data Source
        let sourceText = bus.data_source === 'OFFICIAL' ? `${bus.operator} Official Data` : 'Simulated Data';
        if(bus.gps_source === 'Real') sourceText = 'Real-Time GPS Data';
        document.getElementById('info-data-source').innerText = sourceText;
        
        // Update ETA for real buses, reset for simulated until simulation runs
        if(bus.gps_source === 'Real') {
            updateRealETA(bus);
        } else {
            document.getElementById('info-next-stop').innerText = '--';
            document.getElementById('info-eta').innerText = '--';
        }
        
        // Handle GPS Source
        const gpsStatusLabel = document.getElementById('info-gps-status');
        const gpsSourceLabel = document.getElementById('info-gps-source');
        const box = document.getElementById('data-warning-box');
        
        if(bus.gps_source === 'Real') {
            gpsStatusLabel.innerText = 'GPS: LIVE';
            gpsStatusLabel.style.color = '#155724';
            gpsSourceLabel.innerText = 'Driver Mobile GPS';
            box.style.backgroundColor = '#d4edda';
            box.style.borderLeftColor = '#28a745';
            box.querySelectorAll('p').forEach(p => p.style.color = '#155724');
        } else {
            gpsStatusLabel.innerText = 'GPS: SIMULATED';
            gpsStatusLabel.style.color = '#856404';
            gpsSourceLabel.innerText = 'Development/Demo Fallback';
            box.style.backgroundColor = '#fff3cd';
            box.style.borderLeftColor = '#ffc107';
            box.querySelectorAll('p').forEach(p => p.style.color = '#856404');
        }
        
        if(bus.current_latitude && bus.current_longitude) {
            map.setView([bus.current_latitude, bus.current_longitude], 13);
            if(busMarkers[bus.id]) busMarkers[bus.id].openPopup();
        }
        updateATAInfo(busId);
    }
}

function updateATAInfo(busId) {
    const bus = trackingData.buses.find(b => b.id == busId);
    if(bus && bus.gps_source === 'Real') {
        document.getElementById('info-last-stop').innerText = 'No real arrival recorded yet';
        document.getElementById('info-ata').innerText = '--';
        document.getElementById('info-delay').innerText = '--';
        document.getElementById('info-delay').className = 'badge';
        return;
    }

    const arrival = trackingData.latest_arrivals[busId];
    if(arrival) {
        document.getElementById('info-last-stop').innerText = arrival.stop_name;
        document.getElementById('info-ata').innerText = arrival.ata;
        
        const delayBadge = document.getElementById('info-delay');
        if(arrival.delay_minutes > 0) {
            delayBadge.innerText = `Delayed (${arrival.delay_minutes} min)`;
            delayBadge.className = 'badge delayed';
        } else if(arrival.delay_minutes < 0) {
            delayBadge.innerText = `Early (${Math.abs(arrival.delay_minutes)} min)`;
            delayBadge.className = 'badge early';
        } else {
            delayBadge.innerText = 'On Time';
            delayBadge.className = 'badge on-time';
        }
    } else {
        document.getElementById('info-last-stop').innerText = 'No arrivals yet';
        document.getElementById('info-ata').innerText = '--';
        document.getElementById('info-delay').innerText = '--';
        document.getElementById('info-delay').className = 'badge';
    }
}

window.toggleSimulation = function() {
    const btn = document.getElementById('simulate-btn');
    if(simulationInterval) {
        clearInterval(simulationInterval);
        simulationInterval = null;
        btn.innerText = 'Start Simulation';
        btn.classList.remove('active');
        document.getElementById('info-eta').innerText = '--';
        document.getElementById('info-next-stop').innerText = '--';
    } else {
        if(!selectedBusId) return alert('Select a bus first');
        btn.innerText = 'Stop Simulation';
        btn.classList.add('active');
        simulationInterval = setInterval(tickSimulation, 1000);
    }
}

async function tickSimulation() {
    if(!selectedBusId) return;
    try {
        const res = await fetch(`/api/simulate/move/${selectedBusId}`, { method: 'POST' });
        const data = await res.json();
        
        if(data.error) {
            console.error(data.error);
            toggleSimulation();
            return;
        }
        
        if(busMarkers[selectedBusId]) {
            busMarkers[selectedBusId].setLatLng([data.new_lat, data.new_lon]);
            map.panTo([data.new_lat, data.new_lon], {animate: true, duration: 1});
        }
        
        document.getElementById('info-next-stop').innerText = data.target_stop_name;
        document.getElementById('info-eta').innerText = data.eta;
        
        if(data.arrived) {
            // Bus reached the stop! Temporarily store the filters
            const opFilter = document.getElementById('filter-operator').value;
            const areaFilter = document.getElementById('filter-area').value;
            
            await fetchTrackingData();
            
            // Restore filters
            document.getElementById('filter-operator').value = opFilter;
            document.getElementById('filter-area').value = areaFilter;
            
            updateATAInfo(selectedBusId);
        }
        
    } catch (e) {
        console.error("Simulation error", e);
    }
}

function computeETA(lat1, lon1, lat2, lon2) {
    const R = 6371; // Radius of earth in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    const distanceKm = R * c;
    
    // Assume average speed 30 km/h
    const speedKmh = 30;
    const timeHours = distanceKm / speedKmh;
    const timeMinutes = Math.ceil(timeHours * 60);
    return { distance: distanceKm.toFixed(1), minutes: timeMinutes };
}

function updateRealETA(bus) {
    const alertBox = document.getElementById('delay-alert-box');
    
    if(!bus.current_latitude || !bus.current_longitude || !bus.next_stop_id) {
        document.getElementById('info-next-stop').innerText = '--';
        document.getElementById('info-eta').innerText = '--';
        if(alertBox) alertBox.style.display = 'none';
        return;
    }
    
    const nextStop = trackingData.stops.find(s => s.id == bus.next_stop_id);
    if(nextStop) {
        const result = computeETA(bus.current_latitude, bus.current_longitude, nextStop.latitude, nextStop.longitude);
        document.getElementById('info-next-stop').innerText = nextStop.stop_name;
        
        let etaText = 'Due';
        if(result.minutes > 0) etaText = `${result.minutes} min (${result.distance} km)`;
        else etaText = `Due (${result.distance} km)`;
        document.getElementById('info-eta').innerText = etaText;
        
        // Handle Delay UI
        if(alertBox) {
            if(bus.delay_status === 'DELAYED') {
                // Parse server time to display format
                let parsedServer = new Date(trackingData.server_time.replace(/-/g, '/'));
                let currentStr = trackingData.server_time; // Fallback
                if(!isNaN(parsedServer)) {
                    currentStr = parsedServer.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                }
                
                // Parse schedule time
                let schedStr = nextStop.scheduled_arrival_time || 'N/A';
                if(schedStr !== 'N/A') {
                    let parts = schedStr.split(':');
                    let d = new Date(); d.setHours(parts[0], parts[1]);
                    schedStr = d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                }
                
                alertBox.style.display = 'block';
                alertBox.style.backgroundColor = '#f8d7da';
                alertBox.style.border = '1px solid #f5c6cb';
                alertBox.style.color = '#721c24';
                alertBox.innerHTML = `
                    <h3 style="margin-top:0; color: #dc3545;">🔴 BUS DELAYED</h3>
                    <p style="margin: 5px 0; font-weight: bold;">${bus.bus_number}</p>
                    <p style="margin: 5px 0;"><strong>Next Stop:</strong> ${nextStop.stop_name}</p>
                    <p style="margin: 5px 0;"><strong>Scheduled Arrival:</strong> ${schedStr}</p>
                    <p style="margin: 5px 0;"><strong>Current Time:</strong> ${currentStr}</p>
                    <p style="margin: 0; font-weight: bold; color: #dc3545;">Delay: ${bus.delay_minutes} minutes</p>
                `;
            } else if (bus.delay_status === 'ON TIME') {
                alertBox.style.display = 'block';
                alertBox.style.backgroundColor = '#d4edda';
                alertBox.style.border = '1px solid #c3e6cb';
                alertBox.style.color = '#155724';
                alertBox.innerHTML = `
                    <h3 style="margin-top:0; color: #28a745;">🟢 ON TIME</h3>
                    <p style="margin: 5px 0; font-weight: bold;">${bus.bus_number}</p>
                `;
            } else {
                alertBox.style.display = 'none';
            }
        }

    } else {
        document.getElementById('info-next-stop').innerText = '--';
        document.getElementById('info-eta').innerText = '--';
        if(alertBox) alertBox.style.display = 'none';
    }
}

async function pollRealGPS() {
    if(!selectedBusId) return;
    try {
        const res = await fetch('/api/tracking_data');
        const data = await res.json();
        
        trackingData = data; // Update global state
        
        // Find selected bus
        const bus = trackingData.buses.find(b => b.id == selectedBusId);
        if(bus && bus.gps_source === 'Real') {
            // Stop simulation
            if(simulationInterval) {
                toggleSimulation();
            }
            
            // Calculate ETA
            let nextStopName = '--';
            let etaText = '--';
            if(bus.next_stop_id) {
                const nextStop = trackingData.stops.find(s => s.id == bus.next_stop_id);
                if(nextStop) {
                    nextStopName = nextStop.stop_name;
                    const result = computeETA(bus.current_latitude, bus.current_longitude, nextStop.latitude, nextStop.longitude);
                    etaText = result.minutes > 0 ? `${result.minutes} min (${result.distance} km)` : `Due (${result.distance} km)`;
                }
            }
            
            console.log(`[LIVE GPS] Bus ${bus.bus_number}\nLatitude: ${bus.current_latitude}\nLongitude: ${bus.current_longitude}\nNext Stop: ${nextStopName}\nETA: ${etaText}\nGPS Source: Real`);
            
            // Move marker without clearing map
            if(bus.current_latitude && bus.current_longitude && busMarkers[selectedBusId]) {
                busMarkers[selectedBusId].setLatLng([
                    Number(bus.current_latitude), 
                    Number(bus.current_longitude)
                ]);
                console.log("Marker updated to:", busMarkers[selectedBusId].getLatLng());
                
                // Update popup
                const gpsText = '<span style="color:green; font-weight:bold;">GPS: LIVE</span><br>Source: Driver Mobile GPS';
                busMarkers[selectedBusId].getPopup().setContent(`<b>${bus.operator || 'Bus'} - ${bus.bus_number}</b><br>Service: ${bus.service_type || 'Standard'}<br>${gpsText}`);
                
                // Update Bus Information card
                const gpsStatusLabel = document.getElementById('info-gps-status');
                if(gpsStatusLabel) {
                    gpsStatusLabel.innerText = 'GPS: LIVE';
                    gpsStatusLabel.style.color = '#155724';
                    document.getElementById('info-gps-source').innerText = 'Driver Mobile GPS';
                    document.getElementById('info-data-source').innerText = 'Real-Time GPS Data';
                    const box = document.getElementById('data-warning-box');
                    box.style.backgroundColor = '#d4edda';
                    box.style.borderLeftColor = '#28a745';
                    box.querySelectorAll('p').forEach(p => p.style.color = '#155724');
                }
                
                // Update ETA in UI
                updateRealETA(bus);
            }
        }
    } catch (e) {
        console.error("Polling error", e);
    }
}


window.renderRouteStops = function(bus) {
    const card = document.getElementById('route-stops-card');
    const container = document.getElementById('route-stops-container');
    
    if(!bus || !bus.route_id) {
        if(card) card.style.display = 'none';
        return;
    }
    if(card) card.style.display = 'block';
    
    let routeStops = trackingData.stops.filter(s => s.route_id == bus.route_id).sort((a,b) => a.stop_order - b.stop_order);
    let nextStopId = bus.next_stop_id;
    let nextStopIndex = routeStops.findIndex(s => s.id == nextStopId);
    if(nextStopIndex === -1 && routeStops.length > 0) nextStopIndex = 0; 
    
    let html = '<ul style="list-style:none; padding:0; margin:0;">';
    
    for(let i = 0; i < routeStops.length; i++) {
        let s = routeStops[i];
        let statusBadge = '';
        let timeInfo = '';
        let delayBadge = '';
        let schedStr = s.scheduled_arrival_time ? s.scheduled_arrival_time : 'N/A';
        
        let arrivalRecord = trackingData.latest_arrivals && trackingData.latest_arrivals[bus.id];
        let ata = '';
        if(arrivalRecord && arrivalRecord.stop_id == s.id && arrivalRecord.ata) {
            let ad = new Date(arrivalRecord.ata.replace(/-/g, '/'));
            if(!isNaN(ad)) ata = ad.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        }
        
        let state = 'upcoming'; 
        if(i < nextStopIndex) {
            state = 'passed';
            statusBadge = '<span style="color:gray; font-size:12px; font-weight:bold;">✓ PASSED</span>';
            if(ata) timeInfo = `ATA: ${ata}`;
        } else if (i === nextStopIndex) {
            if(ata) {
                state = 'arrived';
                statusBadge = '<span style="color:#28a745; font-size:12px; font-weight:bold;">✓ ARRIVED</span>';
                timeInfo = `ATA: ${ata}`;
            } else {
                state = 'next';
                statusBadge = '<span style="color:#007bff; font-size:12px; font-weight:bold;">🟢 NEXT STOP</span>';
                
                if(bus.gps_source === 'Real' && bus.current_latitude && bus.current_longitude) {
                    const result = computeETA(bus.current_latitude, bus.current_longitude, s.latitude, s.longitude);
                    let etaDate = new Date((trackingData.server_time || '').replace(/-/g, '/'));
                    if(isNaN(etaDate)) etaDate = new Date();
                    etaDate.setMinutes(etaDate.getMinutes() + result.minutes);
                    timeInfo = `ETA: ${etaDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
                }
                
                if(bus.delay_status === 'DELAYED') {
                    delayBadge = '&nbsp;&nbsp;<span style="color:#dc3545; font-size:12px; font-weight:bold;">🔴 DELAYED</span>';
                } else if(bus.delay_status === 'ON TIME') {
                    delayBadge = '&nbsp;&nbsp;<span style="color:#28a745; font-size:12px; font-weight:bold;">🟢 ON TIME</span>';
                }
            }
        } else {
            state = 'upcoming';
            statusBadge = '<span style="color:orange; font-size:12px; font-weight:bold;">○ UPCOMING</span>';
        }
        
        let liStyle = "padding:10px; border-bottom:1px solid #eee; margin-bottom:5px;";
        if(state === 'next') liStyle += " background:#e9f7fe; border-left:4px solid #007bff;";
        else if(state === 'passed') liStyle += " opacity:0.6;";
        
        html += `
            <li style="${liStyle}">
                <div style="font-weight:bold;">${s.stop_order}. ${s.stop_name} <span style="font-size:12px; font-weight:normal; color:#666;">(${s.area_type || 'Unknown'})</span></div>
                <div style="font-size:13px; margin-top:4px;">
                    Scheduled: ${schedStr} <br>
                    ${timeInfo ? timeInfo + '<br>' : ''}
                    ${statusBadge}${delayBadge}
                </div>
            </li>
        `;
    }
    html += '</ul>';
    if(container) container.innerHTML = html;
}


function drawRouteMap(bus) {
    // Clear generic stop markers
    Object.values(stopMarkers).forEach(m => map.removeLayer(m));
    stopMarkers = {};
    
    // Clear previous route stops
    routeStopMarkers.forEach(m => map.removeLayer(m));
    routeStopMarkers = [];
    
    if(currentRoutePolyline) {
        map.removeLayer(currentRoutePolyline);
        currentRoutePolyline = null;
    }
    
    if(!bus || !bus.route_id) return;
    
    let routeStops = trackingData.stops.filter(s => s.route_id == bus.route_id).sort((a,b) => a.stop_order - b.stop_order);
    
    let latlngs = [];
    let nextStopIndex = routeStops.findIndex(s => s.id == bus.next_stop_id);
    if(nextStopIndex === -1 && routeStops.length > 0) nextStopIndex = 0;
    
    lastRenderedNextStopId = bus.next_stop_id;
    
    routeStops.forEach((s, i) => {
        if(s.latitude && s.longitude) {
            latlngs.push([s.latitude, s.longitude]);
            
            let color, radius, border, iconText;
            
            if(i < nextStopIndex) {
                // Passed
                color = '#6c757d'; // gray
                radius = 5;
                border = 'white';
                iconText = '';
            } else if (i === nextStopIndex) {
                // Next Stop
                color = '#28a745'; // green
                radius = 8;
                border = '#333'; // dark border
                iconText = '';
            } else {
                // Upcoming
                color = '#ffc107'; // yellow
                radius = 5;
                border = 'white';
                iconText = '';
            }
            
            const stopIcon = L.divIcon({
                className: 'custom-div-icon',
                html: `<div style='background-color:${color}; width:${radius*2}px; height:${radius*2}px; border-radius:50%; border:2px solid ${border};'></div>`,
                iconSize: [radius*2+4, radius*2+4],
                iconAnchor: [radius+2, radius+2]
            });

            const marker = L.marker([s.latitude, s.longitude], {icon: stopIcon}).addTo(map);
            marker.bindPopup(`<b>${s.stop_name}</b><br>Order: ${s.stop_order}`);
            routeStopMarkers.push(marker);
        }
    });
    
    if(latlngs.length > 0) {
        currentRoutePolyline = L.polyline(latlngs, {color: '#007bff', weight: 4, opacity: 0.7}).addTo(map);
        try { map.fitBounds(currentRoutePolyline.getBounds().pad(0.1)); } catch(e) {}
    }
}


async function fetchPassengerAlerts() {
    const busId = document.getElementById('bus-selector').value;
    if (!busId) {
        document.getElementById('passenger-alert-center').style.display = 'none';
        return;
    }
    
    try {
        const res = await fetch('/api/notifications?bus_id=' + busId);
        const alerts = await res.json();
        
        if (alerts.length > 0) {
            document.getElementById('passenger-alert-center').style.display = 'block';
            let html = '';
            alerts.forEach(a => {
                html += `
                    <div style="padding: 10px; border-bottom: 1px solid #ffcccc;">
                        <strong style="color:#d9534f;">${a.title}</strong><br>
                        <span style="font-size: 0.9em;">${a.message}</span><br>
                        <small style="color:#666;">Generated: ${a.created_at} | Status: ${a.status}</small>
                    </div>
                `;
            });
            document.getElementById('passenger-alerts-list').innerHTML = html;
        } else {
            document.getElementById('passenger-alert-center').style.display = 'none';
        }
    } catch(e) {
        console.error("Failed to fetch passenger alerts", e);
    }
}

// Check alerts every 5 seconds
setInterval(fetchPassengerAlerts, 5000);

// Also hook into bus selection
document.getElementById('bus-selector').addEventListener('change', fetchPassengerAlerts);


async function loadMyComplaints() {
    try {
        const res = await fetch('/api/complaints/my');
        const data = await res.json();
        const tbody = document.getElementById('my-complaints-body');
        tbody.innerHTML = '';
        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No complaints found.</td></tr>';
            return;
        }
        
        data.forEach(c => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="padding:8px;">${c.id}</td>
                <td>${c.category}<br><small>Bus: ${c.bus_number || '-'} | Route: ${c.route_name || '-'}</small></td>
                <td><strong>${c.status}</strong></td>
                <td><small>${c.created_at}</small></td>
                <td>${c.admin_response || '-'}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch(e) {
        console.error("Failed to load complaints", e);
    }
}

async function submitComplaint(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    const msg = document.getElementById('complaint-msg');
    btn.disabled = true;
    msg.innerText = "Submitting...";
    msg.style.color = 'black';
    
    const payload = {
        bus_id: document.getElementById('complaint-bus').value || null,
        route_id: document.getElementById('complaint-route').value || null,
        category: document.getElementById('complaint-category').value,
        description: document.getElementById('complaint-description').value
    };
    
    try {
        const res = await fetch('/api/complaints', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        if (data.success) {
            msg.innerText = "Complaint submitted successfully! ID: " + data.complaint_id;
            msg.style.color = 'green';
            e.target.reset();
            loadMyComplaints();
        } else {
            msg.innerText = "Error: " + data.error;
            msg.style.color = 'red';
        }
    } catch(err) {
        msg.innerText = "Submission failed.";
        msg.style.color = 'red';
    }
    btn.disabled = false;
}

// Populate complaints dropdowns when tracking data loads
function populateComplaintDropdowns() {
    if (!window.latestTrackingData) return;
    
    const busSel = document.getElementById('complaint-bus');
    if (busSel.options.length <= 1) {
        window.latestTrackingData.buses.forEach(b => {
            const opt = document.createElement('option');
            opt.value = b.id;
            opt.innerText = b.bus_number + (b.bus_name ? ' ('+b.bus_name+')' : '');
            busSel.appendChild(opt);
        });
    }
    
    const routeSel = document.getElementById('complaint-route');
    if (routeSel.options.length <= 1) {
        window.latestTrackingData.routes.forEach(r => {
            const opt = document.createElement('option');
            opt.value = r.id;
            opt.innerText = r.route_name;
            routeSel.appendChild(opt);
        });
    }
}

// Hook into existing tracking data loop to populate dropdowns once
let initialComplaintsLoaded = false;
setInterval(() => {
    if (window.latestTrackingData && !initialComplaintsLoaded) {
        populateComplaintDropdowns();
        loadMyComplaints();
        initialComplaintsLoaded = true;
    }
}, 1000);
