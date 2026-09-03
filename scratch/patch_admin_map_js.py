with open(r'static\js\admin.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Add Admin Map logic
map_logic = """
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
            html += `<li><a href="#" onclick="previewLocation(${r.lat}, ${r.lon}, '${r.display_name.replace(/'/g, "\\'")}'); return false;">${r.display_name}</a></li>`;
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
"""

js += "\n" + map_logic

with open(r'static\js\admin.js', 'w', encoding='utf-8') as f:
    f.write(js)
print("Patched admin.js with map logic")
