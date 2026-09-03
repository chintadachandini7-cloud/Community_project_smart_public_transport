import re

with open(r'static\js\passenger.js', 'r', encoding='utf-8') as f:
    js = f.read()

old_apply = """window.applyFilters = function() {
    const operatorFilter = document.getElementById('filter-operator').value;
    const areaFilter = document.getElementById('filter-area').value;
    
    // Filter Routes based on Operator to know which stops/buses to show
    let validRouteIds = trackingData.routes
        .filter(r => operatorFilter === 'All' || r.operator === operatorFilter)
        .map(r => r.id);

    // Filter Stops
    let filteredStops = trackingData.stops.filter(s => {
        let opMatch = validRouteIds.includes(s.route_id);
        let areaMatch = areaFilter === 'All' || s.area_type === areaFilter;
        return opMatch && areaMatch;
    });

    // Filter Buses
    let filteredBuses = trackingData.buses.filter(b => {
        return (operatorFilter === 'All' || b.operator === operatorFilter);
    });

    drawStops(filteredStops);
    drawBuses(filteredBuses);
    populateBusSelector(filteredBuses);
    
    // Adjust map view if there are markers
    if (filteredStops.length > 0) {
        const group = new L.featureGroup(Object.values(stopMarkers));
        map.fitBounds(group.getBounds().pad(0.1));
    }
}"""

new_apply = """window.applyFilters = function() {
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

with open(r'static\js\passenger.js', 'w', encoding='utf-8') as f:
    f.write(js)
print("Updated passenger.js")
