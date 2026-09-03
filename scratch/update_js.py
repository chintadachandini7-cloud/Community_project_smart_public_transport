import re

with open(r'static\js\passenger.js', 'r', encoding='utf-8') as f:
    code = f.read()

old_block = """function updateRealETA(bus) {
    if(!bus.current_latitude || !bus.current_longitude || !bus.next_stop_id) {
        document.getElementById('info-next-stop').innerText = '--';
        document.getElementById('info-eta').innerText = '--';
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
    } else {
        document.getElementById('info-next-stop').innerText = '--';
        document.getElementById('info-eta').innerText = '--';
    }
}"""

new_block = """function updateRealETA(bus) {
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
}"""

if old_block in code:
    code = code.replace(old_block, new_block)
    with open(r'static\js\passenger.js', 'w', encoding='utf-8') as f:
        f.write(code)
    print("Success")
else:
    print("Failed to find block!")
