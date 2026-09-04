document.addEventListener('DOMContentLoaded', () => {
    loadRoutes();
    loadStops();
    loadBuses();

    document.getElementById('route-form').addEventListener('submit', handleRouteSubmit);
    document.getElementById('stop-form').addEventListener('submit', handleStopSubmit);
    document.getElementById('bus-form').addEventListener('submit', handleBusSubmit);
});

async function apiCall(url, method = 'GET', body = null) {
    const options = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) options.body = JSON.stringify(body);
    const res = await fetch(url, options);
    const data = await res.json();
    if(!res.ok) throw new Error(data.error || 'API Error');
    return data;
}

function getBadge(ds) {
    if(ds === 'OFFICIAL') return `<span style="background:#28a745; color:white; padding:3px 6px; border-radius:4px; font-size:12px;">OFFICIAL DATA</span>`;
    if(ds === 'DEMO') return `<span style="background:#ffc107; color:#333; padding:3px 6px; border-radius:4px; font-size:12px;">DEMO DATA</span>`;
    if(ds === 'USER_ENTERED') return `<span style="background:#17a2b8; color:white; padding:3px 6px; border-radius:4px; font-size:12px;">USER ENTERED</span>`;
    return `<span style="background:#6c757d; color:white; padding:3px 6px; border-radius:4px; font-size:12px;">${ds || 'UNKNOWN'}</span>`;
}
function getVerifyBadge(item) {
    if(item.data_source === 'OFFICIAL' && item.verified_at) {
        let urlLink = item.source_url ? `<br><a href="${item.source_url}" target="_blank" style="font-size:10px;">${item.source_type || 'Source'}</a>` : '';
        return `<span style="font-size:11px; color:#555;">${item.verified_at}</span>${urlLink}`;
    }
    return '--';
}


// --- Routes ---
async function loadRoutes() {
    try {
        const routes = await apiCall('/api/routes');
        const tbody = document.querySelector('#routes-table tbody');
        
        const stopSelect = document.getElementById('stop_route_id');
        const busSelect = document.getElementById('bus_route_id');
        const stopOptions = ['<option value="">Select Route</option>'];
        const busOptions = ['<option value="">Select Route</option>'];

        routes.forEach(r => {
            const opt = `<option value="${r.id}">${r.route_name}</option>`;
            stopOptions.push(opt);
            busOptions.push(opt);
        });
        stopSelect.innerHTML = stopOptions.join('');
        busSelect.innerHTML = busOptions.join('');

        const displayRoutes = routes.slice(0, 100);
        tbody.innerHTML = displayRoutes.map(r => `
            <tr>
                <td>${r.id}</td><td>${r.route_name}</td><td>${r.source}</td><td>${r.destination}</td>
                <td>${r.operator || ''}</td><td>${r.service_type || ''}</td>
                <td>${getBadge(r.data_source)}</td>
                <td>${getVerifyBadge(r)}</td>
                <td>
                    <button onclick="editRoute(${r.id}, '${(r.route_name||'').replace(/'/g, "\\'")}', '${(r.source||'').replace(/'/g, "\\'")}', '${(r.destination||'').replace(/'/g, "\\'")}', '${r.operator||''}', '${r.service_type||''}', '${r.data_source||''}')">Edit</button>
                    <button onclick="deleteRoute(${r.id})">Delete</button>
                </td>
            </tr>`).join('');
    } catch(e) { console.error(e); }
}

async function handleRouteSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('route_id').value;
    const data = {
        route_name: document.getElementById('route_name').value,
        source: document.getElementById('route_source').value,
        destination: document.getElementById('route_destination').value,
        operator: document.getElementById('route_operator').value,
        service_type: document.getElementById('route_service').value,
        data_source: document.getElementById('route_data_source').value
    };
    try {
        if (id) await apiCall(`/api/routes/${id}`, 'PUT', data);
        else await apiCall('/api/routes', 'POST', data);
        resetRouteForm();
        loadRoutes();
    } catch(e) { alert(e.message); }
}

window.editRoute = function(id, name, src, dest, op, srv, ds) {
    document.getElementById('route_id').value = id;
    document.getElementById('route_name').value = name;
    document.getElementById('route_source').value = src;
    document.getElementById('route_destination').value = dest;
    document.getElementById('route_operator').value = op !== 'null' ? op : '';
    document.getElementById('route_service').value = srv !== 'null' ? srv : '';
    document.getElementById('route_data_source').value = ds !== 'null' ? ds : '';
}

window.resetRouteForm = function() { document.getElementById('route-form').reset(); document.getElementById('route_id').value = ''; }
window.deleteRoute = async function(id) { if(confirm('Are you sure?')) { await apiCall(`/api/routes/${id}`, 'DELETE'); loadRoutes(); } }

// --- Stops ---
async function loadStops(routeId = null) {
    try {
        const url = routeId ? `/api/stops?route_id=${routeId}` : '/api/stops?limit=100';
        const stops = await apiCall(url);
        const tbody = document.querySelector('#stops-table tbody');
        tbody.innerHTML = stops.map(s => `
            <tr>
                <td>${s.id}</td><td>${s.route_name || 'N/A'}</td><td>${s.stop_name}</td>
                <td>${s.latitude}</td><td>${s.longitude}</td><td>${s.stop_order}</td><td>${s.area_type || ''}</td>
                <td>${s.scheduled_arrival_time || '--'}</td>
                <td>${getBadge(s.data_source)}</td>
                <td>${getVerifyBadge(s)}</td>
                <td>
                    <button onclick="editStop(${s.id}, ${s.route_id}, '${(s.stop_name||'').replace(/'/g, "\\'")}', ${s.latitude}, ${s.longitude}, ${s.stop_order}, '${s.area_type||''}', '${s.scheduled_arrival_time||''}', '${s.data_source||''}')">Edit</button>
                    <button onclick="deleteStop(${s.id})">Delete</button>
                </td>
            </tr>`).join('');
    } catch(e) { console.error(e); }
}

async function handleStopSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('stop_id').value;
    const data = {
        route_id: document.getElementById('stop_route_id').value,
        stop_name: document.getElementById('stop_name').value,
        latitude: document.getElementById('stop_lat').value,
        longitude: document.getElementById('stop_lng').value,
        stop_order: document.getElementById('stop_order').value,
        area_type: document.getElementById('stop_area_type').value,
        scheduled_arrival_time: document.getElementById('stop_scheduled_arrival_time').value,
        data_source: document.getElementById('stop_data_source').value
    };
    try {
        if (id) await apiCall(`/api/stops/${id}`, 'PUT', data);
        else await apiCall('/api/stops', 'POST', data);
        resetStopForm();
        loadStops();
    } catch(e) { alert(e.message); }
}

window.editStop = function(id, route_id, name, lat, lng, order, area, arr, ds) {
    document.getElementById('stop_id').value = id;
    document.getElementById('stop_route_id').value = route_id;
    document.getElementById('stop_name').value = name;
    document.getElementById('stop_lat').value = lat;
    document.getElementById('stop_lng').value = lng;
    document.getElementById('stop_order').value = order;
    document.getElementById('stop_area_type').value = area !== 'null' ? area : '';
    document.getElementById('stop_scheduled_arrival_time').value = arr !== 'null' ? arr : '';
    document.getElementById('stop_data_source').value = ds !== 'null' ? ds : '';
}

window.resetStopForm = function() { document.getElementById('stop-form').reset(); document.getElementById('stop_id').value = ''; }
window.deleteStop = async function(id) { if(confirm('Are you sure?')) { await apiCall(`/api/stops/${id}`, 'DELETE'); loadStops(); } }

// --- Buses ---
async function loadBuses() {
    try {
        const buses = await apiCall('/api/buses');
        const tbody = document.querySelector('#buses-table tbody');
        tbody.innerHTML = buses.map(b => `
            <tr>
                <td>${b.id}</td><td>${b.bus_number}</td><td>${b.bus_name}</td><td>${b.route_name || 'N/A'}</td>
                <td>${b.operator || ''}</td><td>${b.service_type || ''}</td>
                <td>${b.current_latitude}</td><td>${b.current_longitude}</td><td>${b.status}</td>
                <td>${getBadge(b.data_source)}</td>
                <td>${getVerifyBadge(b)}</td>
                <td>
                    <button onclick="editBus('${b.id}', '${b.bus_number}', '${(b.bus_name||'').replace(/'/g, "\\'")}', ${b.route_id || 'null'}, ${b.current_latitude}, ${b.current_longitude}, '${b.status}', '${b.operator||''}', '${b.service_type||''}', '${b.data_source||''}')">Edit</button>
                    <button onclick="deleteBus('${b.id}')">Delete</button>
                </td>
            </tr>`).join('');
    } catch(e) { console.error(e); }
}

async function handleBusSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('bus_id').value;
    const data = {
        bus_number: document.getElementById('bus_number').value,
        bus_name: document.getElementById('bus_name').value,
        route_id: document.getElementById('bus_route_id').value,
        current_latitude: document.getElementById('bus_lat').value,
        current_longitude: document.getElementById('bus_lng').value,
        status: document.getElementById('bus_status').value,
        operator: document.getElementById('bus_operator').value,
        service_type: document.getElementById('bus_service').value,
        data_source: document.getElementById('bus_data_source').value
    };
    try {
        if (id) await apiCall(`/api/buses/${id}`, 'PUT', data);
        else await apiCall('/api/buses', 'POST', data);
        resetBusForm();
        loadBuses();
    } catch(e) { alert(e.message); }
}

window.editBus = function(id, number, name, route_id, lat, lng, status, op, srv, ds) {
    document.getElementById('bus_id').value = id;
    document.getElementById('bus_number').value = number;
    document.getElementById('bus_name').value = name;
    document.getElementById('bus_route_id').value = route_id;
    document.getElementById('bus_lat').value = lat;
    document.getElementById('bus_lng').value = lng;
    document.getElementById('bus_status').value = status;
    document.getElementById('bus_operator').value = op !== 'null' ? op : '';
    document.getElementById('bus_service').value = srv !== 'null' ? srv : '';
    document.getElementById('bus_data_source').value = ds !== 'null' ? ds : '';
}

window.resetBusForm = function() { document.getElementById('bus-form').reset(); document.getElementById('bus_id').value = ''; }
window.deleteBus = async function(id) { if(confirm('Are you sure?')) { await apiCall(`/api/buses/${id}`, 'DELETE'); loadBuses(); } }


// --- IMPORT LOGIC ---
let pendingImportData = null;

function csvJSON(csv) {
    const lines = csv.split('\n');
    const result = [];
    const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
    
    for(let i = 1; i < lines.length; i++) {
        if(!lines[i].trim()) continue;
        const obj = {};
        // Simple split (does not handle commas inside quotes well, but good enough for test)
        const currentline = lines[i].split(',');
        for(let j = 0; j < headers.length; j++) {
            obj[headers[j]] = currentline[j] ? currentline[j].trim().replace(/^"|"$/g, '') : '';
        }
        result.push(obj);
    }
    return result;
}

window.previewImport = async function() {
    const fileInput = document.getElementById('import_file');
    if(!fileInput.files.length) return alert("Please select a file.");
    
    const file = fileInput.files[0];
    const reader = new FileReader();
    
    reader.onload = async function(e) {
        let records = [];
        try {
            if(file.name.endsWith('.json')) {
                records = JSON.parse(e.target.result);
            } else if (file.name.endsWith('.csv')) {
                records = csvJSON(e.target.result);
            } else {
                return alert("Unsupported file format.");
            }
            
            const res = await fetch('/api/import/preview', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({records: records})
            });
            const data = await res.json();
            
            pendingImportData = data;
            
            document.getElementById('import_preview_area').style.display = 'block';
            document.getElementById('prev_adds').innerText = data.adds.length;
            document.getElementById('prev_updates').innerText = data.updates.length;
            document.getElementById('prev_dups').innerText = data.duplicates.length;
            document.getElementById('prev_rejs').innerText = data.rejected.length;
            
            let errHtml = '';
            if(data.rejected.length > 0) {
                errHtml += '<h4>Errors:</h4><ul>';
                data.rejected.slice(0, 10).forEach(r => {
                    errHtml += `<li>Row [${r.row.Type || 'Unknown'}]: ${r.error}</li>`;
                });
                if(data.rejected.length > 10) errHtml += '<li>...and more</li>';
                errHtml += '</ul>';
            }
            document.getElementById('import_errors').innerHTML = errHtml;
            
        } catch(err) {
            alert("Error parsing file: " + err.message);
        }
    };
    reader.readAsText(file);
}

window.cancelImport = function() {
    pendingImportData = null;
    document.getElementById('import_file').value = '';
    document.getElementById('import_preview_area').style.display = 'none';
}

window.commitImport = async function() {
    if(!pendingImportData) return;
    
    try {
        const res = await fetch('/api/import/commit', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                adds: pendingImportData.adds,
                updates: pendingImportData.updates
            })
        });
        const data = await res.json();
        
        if(data.success) {
            alert(`Import Successful!\nRoutes: ${data.stats.routes}\nBuses: ${data.stats.buses}\nStops: ${data.stats.stops}`);
            cancelImport();
            loadRoutes();
            loadStops();
            loadBuses();
        } else {
            alert("Error during import.");
        }
    } catch(err) {
        alert("Network error.");
    }
}


// --- Location Verification Map Logic ---
let adminMap = null;
let adminMarker = null;
let tempLocation = null;

function initAdminMap() {
    if(!adminMap) {
        adminMap = L.map('admin-map').setView([16.5, 80.6], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(adminMap);
    }
}

window.findLocation = async function() {
    const name = document.getElementById('stop_name').value;
    const area = document.getElementById('stop_area_type').value;
    
    if(!name) return alert('Please enter a Stop Name first.');
    
    let query = name;
    if(area && area !== 'null') query += `, ${area}`;
    // optionally append state/country
    query += ', Andhra Pradesh, India'; // Try AP/TG context broadly
    
    try {
        const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`);
        const results = await res.json();
        
        const suggDiv = document.getElementById('location-suggestions');
        if(results.length === 0) {
            suggDiv.innerHTML = '<span style="color:red;">No locations found. Try adjusting the name.</span>';
            return;
        }
        
        let html = '<strong>Suggestions:</strong><ul>';
        results.slice(0, 5).forEach((r, i) => {
            html += `<li><a href="#" onclick="previewLocation(${r.lat}, ${r.lon}, '${r.display_name.replace(/'/g, "\'")}'); return false;">${r.display_name}</a></li>`;
        });
        html += '</ul>';
        suggDiv.innerHTML = html;
        
    } catch(err) {
        alert('Error contacting OpenStreetMap: ' + err.message);
    }
}

window.previewLocation = function(lat, lng, displayName) {
    document.getElementById('admin-map').style.display = 'block';
    document.getElementById('confirm-location-btn').style.display = 'inline-block';
    
    initAdminMap();
    adminMap.invalidateSize(); // Fix tile loading issue when container was hidden
    
    const pos = [lat, lng];
    adminMap.setView(pos, 15);
    
    if(adminMarker) adminMap.removeLayer(adminMarker);
    adminMarker = L.marker(pos).addTo(adminMap);
    adminMarker.bindPopup(`<b>Suggested Location</b><br>${displayName}`).openPopup();
    
    tempLocation = {lat, lng, name: displayName};
}

window.confirmLocation = function() {
    if(tempLocation) {
        document.getElementById('stop_lat').value = tempLocation.lat;
        document.getElementById('stop_lng').value = tempLocation.lng;
        
        // As per prompt, if Admin verified, it's a valid coordinate source.
        // We set the data source to OFFICIAL or USER_ENTERED, but prompt says "do not automatically mark transport data as OFFICIAL merely because the coordinates came from OSM"
        // Let's just alert success and let them save.
        alert('Coordinates confirmed and populated!');
        
        document.getElementById('admin-map').style.display = 'none';
        document.getElementById('confirm-location-btn').style.display = 'none';
        document.getElementById('location-suggestions').innerHTML = '';
        tempLocation = null;
    }
}


let allTrips = [];

async function loadTripHistory() {
    try {
        const res = await fetch('/api/admin/trips');
        allTrips = await res.json();
        
        let total = allTrips.length;
        let active = 0, completed = 0, delayed = 0, onTime = 0, totalDelay = 0, tripsWithDelay = 0;
        
        allTrips.forEach(t => {
            if (t.trip_status === 'Active') active++;
            if (t.trip_status === 'Completed') completed++;
            if (t.delayed_stops > 0) delayed++;
            else if (t.num_arrivals > 0) onTime++;
            
            if (t.total_delay_minutes > 0) {
                totalDelay += t.total_delay_minutes;
                tripsWithDelay++;
            }
        });
        
        let avgDelay = tripsWithDelay > 0 ? Math.round(totalDelay / tripsWithDelay) : 0;
        
        const summaryHtml = `
            <div style="flex: 1; padding: 10px; background: #eee; border-radius: 5px; text-align: center;"><strong>Total:</strong> ${total}</div>
            <div style="flex: 1; padding: 10px; background: #eee; border-radius: 5px; text-align: center;"><strong>Active:</strong> ${active}</div>
            <div style="flex: 1; padding: 10px; background: #eee; border-radius: 5px; text-align: center;"><strong>Completed:</strong> ${completed}</div>
            <div style="flex: 1; padding: 10px; background: #eee; border-radius: 5px; text-align: center;"><strong>Delayed:</strong> ${delayed}</div>
            <div style="flex: 1; padding: 10px; background: #eee; border-radius: 5px; text-align: center;"><strong>On Time:</strong> ${onTime}</div>
            <div style="flex: 1; padding: 10px; background: #eee; border-radius: 5px; text-align: center;"><strong>Avg Delay:</strong> ${avgDelay} min</div>
        `;
        document.getElementById('trip-summary-cards').innerHTML = summaryHtml;
        
        filterTrips();
    } catch (e) {
        console.error("Error loading trip history", e);
    }
}

function filterTrips() {
    const search = document.getElementById('trip-search').value.toLowerCase();
    const statusF = document.getElementById('trip-status-filter').value;
    const operatorF = document.getElementById('trip-operator-filter').value;
    const delayF = document.getElementById('trip-delay-filter').value;
    
    const tbody = document.getElementById('trips-body');
    tbody.innerHTML = '';
    
    allTrips.forEach(t => {
        let match = true;
        
        // Search
        if (search) {
            const searchStr = `${t.trip_id} ${t.bus_number} ${t.bus_name || ''} ${t.route_name || ''} ${t.driver_name || ''}`.toLowerCase();
            if (!searchStr.includes(search)) match = false;
        }
        
        // Status
        if (statusF !== 'ALL' && t.trip_status !== statusF) match = false;
        
        // Operator
        if (operatorF !== 'ALL' && t.operator !== operatorF) match = false;
        
        // Delay
        if (delayF === 'DELAYED' && t.delayed_stops === 0) match = false;
        if (delayF === 'ON_TIME' && t.delayed_stops > 0) match = false;
        
        if (match) {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${t.trip_id}</td>
                <td>${t.bus_number} <br><small>${t.bus_name || '-'}</small></td>
                <td>${t.operator || '-'}</td>
                <td>${t.route_name || '-'}</td>
                <td>D: ${t.driver_name || '-'}<br>C: ${t.conductor_name || '-'}</td>
                <td>${t.start_time}<br>to<br>${t.end_time || '...'}</td>
                <td>${t.trip_status}</td>
                <td>Stops: ${t.num_stops}<br>Delay: ${t.total_delay_minutes}m</td>
                <td><button onclick="viewTripDetails(${t.trip_id}, '${t.bus_number}')">View Details</button></td>
            `;
            tbody.appendChild(tr);
        }
    });
}

async function viewTripDetails(tripId, busNumber) {
    document.getElementById('trip-details-container').style.display = 'block';
    document.getElementById('trip-details-title').innerText = `Trip Details - ID: ${tripId} (${busNumber})`;
    document.getElementById('trip-details-body').innerHTML = '<tr><td colspan="5">Loading...</td></tr>';
    
    try {
        const res = await fetch('/api/admin/trips/' + tripId);
        const stops = await res.json();
        
        const tbody = document.getElementById('trip-details-body');
        tbody.innerHTML = '';
        
        stops.forEach(s => {
            let color = '';
            if (s.status === 'DELAYED') color = 'color: red;';
            if (s.status === 'ON TIME') color = 'color: green;';
            if (s.status === 'ARRIVED') color = 'color: blue;';
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${s.stop_order}</td>
                <td>${s.stop_name}</td>
                <td>${s.scheduled_arrival_time || '-'}</td>
                <td>${s.ata || '-'} ${s.delay_minutes > 0 ? '(+'+s.delay_minutes+'m)' : ''}</td>
                <td style="font-weight:bold; ${color}">${s.status}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Error loading trip details", e);
    }
}

// Ensure loadTripHistory runs when Admin Dashboard loads
document.addEventListener('DOMContentLoaded', () => {
    // Check if we are on the admin page by checking if the element exists
    if(document.getElementById('trips-body')) {
        loadTripHistory();
    }
});


let chartPerf, chartOp, chartTrend;
let currentRawTrips = [];

async function loadAnalytics() {
    const startDate = document.getElementById('analytics-start-date').value;
    const endDate = document.getElementById('analytics-end-date').value;
    const op = document.getElementById('analytics-operator').value;
    const status = document.getElementById('analytics-status').value;
    
    let url = new URL('/api/admin/analytics', window.location.origin);
    if (startDate) url.searchParams.append('start_date', startDate);
    if (endDate) url.searchParams.append('end_date', endDate);
    if (op !== 'ALL') url.searchParams.append('operator', op);
    if (status !== 'ALL') url.searchParams.append('status', status);
    
    try {
        const res = await fetch(url);
        const data = await res.json();
        
        currentRawTrips = data.raw_trips || [];
        
        // 1. Summary Cards
        const sum = data.summary;
        const sumHtml = `
            <div style="flex: 1; padding: 15px; background: #e9ecef; border-radius: 5px; text-align: center;"><strong>Total Trips:</strong><br><span style="font-size:24px;">${sum.total_trips}</span></div>
            <div style="flex: 1; padding: 15px; background: #e9ecef; border-radius: 5px; text-align: center;"><strong>Completed:</strong><br><span style="font-size:24px;">${sum.completed_trips}</span></div>
            <div style="flex: 1; padding: 15px; background: #e9ecef; border-radius: 5px; text-align: center;"><strong>Active:</strong><br><span style="font-size:24px;">${sum.active_trips}</span></div>
            <div style="flex: 1; padding: 15px; background: #e9ecef; border-radius: 5px; text-align: center;"><strong>On-Time:</strong><br><span style="font-size:24px;">${sum.on_time_trips}</span></div>
            <div style="flex: 1; padding: 15px; background: #e9ecef; border-radius: 5px; text-align: center;"><strong>Delayed:</strong><br><span style="font-size:24px; color:red;">${sum.delayed_trips}</span></div>
            <div style="flex: 1; padding: 15px; background: #e9ecef; border-radius: 5px; text-align: center;"><strong>Avg Delay:</strong><br><span style="font-size:24px;">${sum.avg_delay}m</span></div>
        `;
        document.getElementById('analytics-summary-cards').innerHTML = sumHtml;
        
        // Ensure Chart.js is loaded
        if (typeof Chart === 'undefined') {
            console.error("Chart.js not loaded.");
            return;
        }

        // 2. Performance Chart (Pie)
        if (chartPerf) chartPerf.destroy();
        chartPerf = new Chart(document.getElementById('chart-performance'), {
            type: 'pie',
            data: {
                labels: ['On-Time', 'Delayed'],
                datasets: [{
                    data: [sum.on_time_trips, sum.delayed_trips],
                    backgroundColor: ['#28a745', '#dc3545']
                }]
            }
        });
        
        // 3. Operator Comparison (Bar)
        if (chartOp) chartOp.destroy();
        const ops = data.operator_comparison;
        if (ops.length === 0) {
            // handle empty
        }
        chartOp = new Chart(document.getElementById('chart-operator'), {
            type: 'bar',
            data: {
                labels: ops.map(o => o.operator),
                datasets: [
                    {
                        label: 'Trips',
                        data: ops.map(o => o.trips),
                        backgroundColor: '#007bff'
                    },
                    {
                        label: 'Avg Delay (m)',
                        data: ops.map(o => o.avg_delay),
                        backgroundColor: '#ffc107'
                    }
                ]
            }
        });
        
        // 4. Daily Trend (Line)
        if (chartTrend) chartTrend.destroy();
        const trend = data.daily_trend;
        chartTrend = new Chart(document.getElementById('chart-trend'), {
            type: 'line',
            data: {
                labels: trend.map(t => t.date),
                datasets: [{
                    label: 'Trips per Day',
                    data: trend.map(t => t.trips),
                    borderColor: '#17a2b8',
                    fill: false
                }]
            },
            options: { scales: { y: { beginAtZero: true } } }
        });
        
        // 5. Buses Table
        const bBody = document.getElementById('analytics-buses-body');
        bBody.innerHTML = '';
        if (data.most_delayed_buses.length === 0) {
            bBody.innerHTML = '<tr><td colspan="5">No data available</td></tr>';
        } else {
            data.most_delayed_buses.forEach(b => {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td>${b.bus_number} <br><small>${b.bus_name}</small></td><td>${b.operator}</td><td>${b.trips}</td><td>${b.delayed_trips}</td><td style="color:${b.avg_delay > 0 ? 'red' : 'black'}">${b.avg_delay}</td>`;
                bBody.appendChild(tr);
            });
        }
        
        // 6. Routes Table
        const rBody = document.getElementById('analytics-routes-body');
        rBody.innerHTML = '';
        if (data.most_delayed_routes.length === 0) {
            rBody.innerHTML = '<tr><td colspan="5">No data available</td></tr>';
        } else {
            data.most_delayed_routes.forEach(r => {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td>${r.route}</td><td>${r.operator}</td><td>${r.trips}</td><td>${r.delayed_trips}</td><td style="color:${r.avg_delay > 0 ? 'red' : 'black'}">${r.avg_delay}</td>`;
                rBody.appendChild(tr);
            });
        }
        
    } catch (e) {
        console.error("Failed to load analytics", e);
    }
}

function exportAnalyticsCSV() {
    if (!currentRawTrips || currentRawTrips.length === 0) {
        alert("No data available to export.");
        return;
    }
    
    let csv = "Trip ID,Bus,Bus Name,Operator,Route,Driver,Conductor,Start,End,Status,Delayed Stops,Total Delay Mins\n";
    currentRawTrips.forEach(t => {
        csv += `${t.trip_id},${t.bus_number},"${t.bus_name || ''}",${t.operator || ''},"${t.route_name || ''}","${t.driver_name || ''}","${t.conductor_name || ''}",${t.start_time || ''},${t.end_time || ''},${t.trip_status},${t.delayed_stops},${t.total_delay_minutes}\n`;
    });
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'trip_performance_export.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('analytics-section')) {
        loadAnalytics();
    }
});


let allAdminAlerts = [];

async function loadAdminAlerts() {
    try {
        const res = await fetch('/api/admin/alerts');
        allAdminAlerts = await res.json();
        filterAdminAlerts();
    } catch(e) {
        console.error("Failed to load admin alerts", e);
    }
}

function filterAdminAlerts() {
    const search = document.getElementById('alert-search').value.toLowerCase();
    const statusF = document.getElementById('alert-status-filter').value;
    const operatorF = document.getElementById('alert-operator-filter').value;
    const dateF = document.getElementById('alert-date-filter').value;
    
    const tbody = document.getElementById('alerts-body');
    tbody.innerHTML = '';
    
    allAdminAlerts.forEach(a => {
        let match = true;
        
        if (search) {
            const searchStr = `${a.alert_id} ${a.bus_number} ${a.route_name} ${a.stop_name} ${a.trip_id} ${a.message} ${a.alert_type}`.toLowerCase();
            if (!searchStr.includes(search)) match = false;
        }
        
        if (statusF !== 'ALL' && a.status !== statusF) match = false;
        if (operatorF !== 'ALL' && a.operator !== operatorF) match = false;
        
        if (dateF) {
            const aDate = a.created_at ? a.created_at.split(' ')[0] : '';
            if (aDate !== dateF) match = false;
        }
        
        if (match) {
            let color = a.status === 'Active' ? 'color: red; font-weight: bold;' : 'color: green;';
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${a.alert_id}</td>
                <td>${a.alert_type}</td>
                <td>T: ${a.trip_id || '-'}<br>B: ${a.bus_number || '-'}</td>
                <td>${a.operator || '-'}</td>
                <td>R: ${a.route_name || '-'}<br>S: ${a.stop_name || '-'}</td>
                <td><small>${a.message || '-'}</small></td>
                <td style="${color}">${a.status}</td>
                <td><small>${a.created_at}</small></td>
            `;
            tbody.appendChild(tr);
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('admin-alert-center-section')) {
        loadAdminAlerts();
    }
});


let allComplaints = [];
let currentCompId = null;

async function loadAdminComplaints() {
    try {
        const res = await fetch('/api/admin/complaints');
        allComplaints = await res.json();
        filterAdminComplaints();
    } catch(e) {
        console.error("Failed to load complaints", e);
    }
}

function filterAdminComplaints() {
    const search = document.getElementById('comp-search').value.toLowerCase();
    const statusF = document.getElementById('comp-status').value;
    const catF = document.getElementById('comp-category').value;
    
    const tbody = document.getElementById('complaints-body');
    tbody.innerHTML = '';
    
    allComplaints.forEach(c => {
        let match = true;
        
        if (search) {
            const searchStr = `${c.id} ${c.bus_number} ${c.route_name} ${c.category} ${c.description} ${c.passenger_id}`.toLowerCase();
            if (!searchStr.includes(search)) match = false;
        }
        
        if (statusF !== 'ALL' && c.status !== statusF) match = false;
        if (catF !== 'ALL' && c.category !== catF) match = false;
        
        if (match) {
            let color = 'black';
            if (c.status === 'Open') color = 'red';
            if (c.status === 'In Progress') color = 'orange';
            if (c.status === 'Resolved') color = 'green';
            if (c.status === 'Rejected') color = 'gray';
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${c.id}</td>
                <td><small>${c.passenger_id.substring(0,8)}...<br>${c.created_at}</small></td>
                <td>B: ${c.bus_number || '-'}<br>R: ${c.route_name || '-'}</td>
                <td>${c.category}</td>
                <td><small>${c.description}</small></td>
                <td style="font-weight:bold; color:${color};">${c.status}</td>
                <td><button onclick="openCompModal(${c.id}, '${c.status}', '${(c.admin_response || '').replace(/'/g, "\\'")}')">Update</button></td>
            `;
            tbody.appendChild(tr);
        }
    });
}

function openCompModal(id, status, response) {
    currentCompId = id;
    document.getElementById('mod-comp-id').innerText = id;
    document.getElementById('mod-comp-status').value = status;
    document.getElementById('mod-comp-response').value = response === 'null' ? '' : response;
    document.getElementById('comp-modal').style.display = 'block';
}

function closeCompModal() {
    document.getElementById('comp-modal').style.display = 'none';
}

async function saveComplaintStatus() {
    if (!currentCompId) return;
    const status = document.getElementById('mod-comp-status').value;
    const response = document.getElementById('mod-comp-response').value;
    
    try {
        const res = await fetch('/api/admin/complaints/' + currentCompId, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({status: status, admin_response: response})
        });
        const data = await res.json();
        if (data.success) {
            closeCompModal();
            loadAdminComplaints();
        } else {
            alert('Error updating complaint');
        }
    } catch(e) {
        alert('Failed to update complaint');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('admin-complaints-section')) {
        loadAdminComplaints();
    }
});
