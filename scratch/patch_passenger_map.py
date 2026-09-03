import re

with open(r'static\js\passenger.js', 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Add global variables
if 'let currentRoutePolyline = null;' not in js:
    js = js.replace('let simulationInterval = null;', 'let simulationInterval = null;\nlet currentRoutePolyline = null;\nlet routeStopMarkers = [];\nlet lastRenderedNextStopId = null;')

# 2. Add drawRouteMap function
draw_route_map = """
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
"""
if 'function drawRouteMap' not in js:
    js += '\n' + draw_route_map

# 3. Patch applyFilters to branch based on selectedBusId
old_apply = """    drawStops(filteredStops);
    drawBuses(filteredBuses);
    populateBusSelector(filteredBuses);
    
    // Adjust map view if there are markers
    if (filteredStops.length > 0) {
        const group = new L.featureGroup(Object.values(stopMarkers));
        try { map.fitBounds(group.getBounds().pad(0.1)); } catch(e) {}
    }
}"""
new_apply = """    
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
}"""
js = js.replace(old_apply, new_apply)

# 4. Patch selectBus to call applyFilters() when bus changes
old_select_bus = """        // Render Route and Stops list
        renderRouteStops(bus);
    }
}"""
new_select_bus = """        // Render Route and Stops list
        renderRouteStops(bus);
        
        // Trigger map redraw for route
        applyFilters();
    } else {
        // Bus deselected
        applyFilters();
    }
}"""
js = js.replace(old_select_bus, new_select_bus)

# 5. Patch pollRealGPS and updateRealETA to handle next_stop_id changes
# pollRealGPS doesn't redraw the route map, it just sets LatLng and calls updateRealETA.
# Inside updateRealETA, we can check if `lastRenderedNextStopId != bus.next_stop_id`. If so, redraw route map!
old_update_eta = """        // Refresh the stops list to dynamically display ETA and live badges
        renderRouteStops(bus);
    }
}"""
new_update_eta = """        // Refresh the stops list to dynamically display ETA and live badges
        renderRouteStops(bus);
        
        // If the bus advanced to a new stop, redraw the route map markers to update colors
        if(bus.next_stop_id != lastRenderedNextStopId) {
            drawRouteMap(bus);
        }
    }
}"""
js = js.replace(old_update_eta, new_update_eta)


with open(r'static\js\passenger.js', 'w', encoding='utf-8') as f:
    f.write(js)
print("Patched passenger.js for map routes")
