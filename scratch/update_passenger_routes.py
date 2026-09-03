import re

with open(r'static\js\passenger.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Add renderRouteStops function
render_fn = """
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
"""

if 'window.renderRouteStops = function' not in js:
    js += '\n' + render_fn

# Inject call to renderRouteStops in selectBus
old_select_bus = """        // Handle Data Source
        let sourceText = bus.data_source === 'OFFICIAL' ? `${bus.operator} Official Data` : 'Simulated Data';
        if(bus.gps_source === 'Real') sourceText = 'Real-Time GPS Data';
        document.getElementById('info-data-source').innerText = sourceText;
        
        // Update ETA for real buses, reset for simulated until simulation runs
        if(bus.gps_source === 'Real') {
            updateRealETA(bus);
        } else {
            document.getElementById('info-next-stop').innerText = '--';
            document.getElementById('info-eta').innerText = '--';
            const alertBox = document.getElementById('delay-alert-box');
            if(alertBox) alertBox.style.display = 'none';
        }
    }
}"""
new_select_bus = """        // Handle Data Source
        let sourceText = bus.data_source === 'OFFICIAL' ? `${bus.operator} Official Data` : 'Simulated Data';
        if(bus.gps_source === 'Real') sourceText = 'Real-Time GPS Data';
        document.getElementById('info-data-source').innerText = sourceText;
        
        // Update ETA for real buses, reset for simulated until simulation runs
        if(bus.gps_source === 'Real') {
            updateRealETA(bus);
        } else {
            document.getElementById('info-next-stop').innerText = '--';
            document.getElementById('info-eta').innerText = '--';
            const alertBox = document.getElementById('delay-alert-box');
            if(alertBox) alertBox.style.display = 'none';
        }
        
        // Render Route and Stops list
        renderRouteStops(bus);
    }
}"""
js = js.replace(old_select_bus, new_select_bus)

# Inject call to renderRouteStops inside updateRealETA
old_update_eta = """                alertBox.innerHTML = `
                    <p style="margin: 0 0 5px 0;"><span style="font-weight: bold; color: #721c24;">🟢 ON TIME</span></p>
                    <p style="margin: 0; color: #721c24; font-size: 0.9rem;">
                        The bus is running on schedule.<br>
                        Expected at <b>${nextStop.stop_name}</b> by ${schedStr}.
                    </p>`;
            }
        }
    }
}"""
new_update_eta = """                alertBox.innerHTML = `
                    <p style="margin: 0 0 5px 0;"><span style="font-weight: bold; color: #721c24;">🟢 ON TIME</span></p>
                    <p style="margin: 0; color: #721c24; font-size: 0.9rem;">
                        The bus is running on schedule.<br>
                        Expected at <b>${nextStop.stop_name}</b> by ${schedStr}.
                    </p>`;
            }
        }
        
        // Refresh the stops list to dynamically display ETA and live badges
        renderRouteStops(bus);
    }
}"""
js = js.replace(old_update_eta, new_update_eta)

# Let's also update pollRealGPS to handle the clearing of the previous state
old_poll = """async function pollRealGPS() {
    if(!selectedBusId) return;
    const bus = trackingData.buses.find(b => b.id == selectedBusId);
    if(bus && bus.gps_source === 'Real') {
        const res = await fetch('/api/tracking_data');
        trackingData = await res.json();
        
        const freshBus = trackingData.buses.find(b => b.id == selectedBusId);
        if(freshBus && freshBus.current_latitude) {
            let m = busMarkers[selectedBusId];
            if(m) m.setLatLng([freshBus.current_latitude, freshBus.current_longitude]);
            updateRealETA(freshBus);
        }
    }
}"""
new_poll = """async function pollRealGPS() {
    if(!selectedBusId) return;
    const bus = trackingData.buses.find(b => b.id == selectedBusId);
    if(bus && bus.gps_source === 'Real') {
        const res = await fetch('/api/tracking_data');
        trackingData = await res.json();
        
        const freshBus = trackingData.buses.find(b => b.id == selectedBusId);
        if(freshBus && freshBus.current_latitude) {
            let m = busMarkers[selectedBusId];
            if(m) m.setLatLng([freshBus.current_latitude, freshBus.current_longitude]);
            updateRealETA(freshBus);
        }
    }
}"""

with open(r'static\js\passenger.js', 'w', encoding='utf-8') as f:
    f.write(js)
print("Updated passenger.js with renderRouteStops")
