import re

with open(r'templates\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace the Filter Panel
old_filters = """            <div class="card filter-card">
                <h2>Filter Network</h2>
                <label>Operator:</label>
                <select id="filter-operator" onchange="applyFilters()">
                    <option value="All">All Operators</option>
                    <option value="APSRTC">APSRTC</option>
                    <option value="TGSRTC">TGSRTC</option>
                </select>
                
                <label>Area Type:</label>
                <select id="filter-area" onchange="applyFilters()">
                    <option value="All">All Areas</option>
                    <option value="CITY">City</option>
                    <option value="TOWN">Town</option>
                    <option value="VILLAGE">Village / Rural</option>
                </select>
            </div>"""

new_filters = """            <div class="card filter-card">
                <h2>🔎 Search Network</h2>
                <input type="text" id="filter-search" placeholder="Search buses, routes, or stops..." onkeyup="applyFilters()" style="width: 100%; padding: 10px; margin-bottom: 15px; border-radius: 4px; border: 1px solid #ccc; box-sizing: border-box;">
                
                <label>Operator:</label>
                <select id="filter-operator" onchange="applyFilters()">
                    <option value="All">All Operators</option>
                    <option value="APSRTC">APSRTC</option>
                    <option value="TGSRTC">TGSRTC</option>
                </select>
                
                <label>Area:</label>
                <select id="filter-area" onchange="applyFilters()">
                    <option value="All">All Areas</option>
                    <option value="CITY">City</option>
                    <option value="TOWN">Town</option>
                    <option value="VILLAGE">Village / Rural</option>
                </select>
                
                <label>Service:</label>
                <select id="filter-service" onchange="applyFilters()">
                    <option value="All">All Services</option>
                    <option value="Pallevelugu">Pallevelugu</option>
                    <option value="Express">Express</option>
                    <option value="Super Luxury">Super Luxury</option>
                </select>
                
                <label>Status:</label>
                <select id="filter-status" onchange="applyFilters()">
                    <option value="All">All Statuses</option>
                    <option value="Live">Live (Active Trip)</option>
                    <option value="Delayed">Delayed</option>
                    <option value="On Time">On Time</option>
                </select>
            </div>"""

html = html.replace(old_filters, new_filters)

# Also rename "Select Bus to Track" to "Available Buses"
html = html.replace('<h2>Select Bus to Track</h2>', '<h2 style="text-align: center;">↓<br><br>Available Buses</h2>')

with open(r'templates\index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated index.html")
