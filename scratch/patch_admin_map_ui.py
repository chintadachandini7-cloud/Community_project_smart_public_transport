import re

with open(r'templates\admin.html', 'r', encoding='utf-8') as f:
    html = f.read()

leaflet_head = """    <link rel="stylesheet" href="{{ url_for('static', filename='css/admin.css') }}">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>"""
html = html.replace("""    <link rel="stylesheet" href="{{ url_for('static', filename='css/admin.css') }}">""", leaflet_head)

# Stops section map UI injection
stops_ui_old = """                <input type="number" step="any" id="stop_lat" placeholder="Latitude" required>
                <input type="number" step="any" id="stop_lng" placeholder="Longitude" required>"""

stops_ui_new = """                <div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; background: #f8f9fa;">
                    <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 10px;">
                        <input type="number" step="any" id="stop_lat" placeholder="Latitude" required style="margin:0;">
                        <input type="number" step="any" id="stop_lng" placeholder="Longitude" required style="margin:0;">
                        <button type="button" onclick="findLocation()" style="background:#007bff; color:white; padding:8px; border:none; cursor:pointer;">Find Location (OSM)</button>
                    </div>
                    
                    <div id="location-suggestions" style="margin-bottom: 10px;"></div>
                    
                    <div id="admin-map" style="height: 200px; width: 100%; display:none; margin-bottom:10px;"></div>
                    
                    <button type="button" id="confirm-location-btn" onclick="confirmLocation()" style="display:none; background:#28a745; color:white; padding:8px; border:none; cursor:pointer;">Confirm Location</button>
                </div>"""

html = html.replace(stops_ui_old, stops_ui_new)

with open(r'templates\admin.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Patched admin.html")
