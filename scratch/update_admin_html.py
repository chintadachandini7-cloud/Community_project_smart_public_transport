import re

with open(r'templates\admin.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ROUTES Section
html = html.replace('<input type="text" id="route_service" placeholder="Service Type (e.g. Pallevelugu)">',
"""<input type="text" id="route_service" placeholder="Service Type (e.g. Pallevelugu)">
                <select id="route_data_source" required>
                    <option value="">Select Data Source</option>
                    <option value="OFFICIAL">OFFICIAL</option>
                    <option value="DEMO">DEMO</option>
                    <option value="USER_ENTERED">USER ENTERED</option>
                </select>""")
html = html.replace('<th>Source</th><th>Destination</th><th>Operator</th><th>Service</th><th>Actions</th>',
'<th>Source</th><th>Destination</th><th>Operator</th><th>Service</th><th>Data Source</th><th>Actions</th>')


# STOPS Section
html = html.replace('<select id="stop_area_type">',
"""<input type="time" id="stop_scheduled_arrival_time" placeholder="Scheduled Arrival Time">
                <select id="stop_data_source" required>
                    <option value="">Select Data Source</option>
                    <option value="OFFICIAL">OFFICIAL</option>
                    <option value="DEMO">DEMO</option>
                    <option value="USER_ENTERED">USER ENTERED</option>
                </select>
                <select id="stop_area_type">""")
html = html.replace('<th>Area Type</th><th>Actions</th>',
'<th>Area Type</th><th>Scheduled Arrival</th><th>Data Source</th><th>Actions</th>')

# BUSES Section
html = html.replace('<input type="text" id="bus_service" placeholder="Service Type (e.g. Pallevelugu)">',
"""<input type="text" id="bus_service" placeholder="Service Type (e.g. Pallevelugu)">
                <select id="bus_data_source" required>
                    <option value="">Select Data Source</option>
                    <option value="OFFICIAL">OFFICIAL</option>
                    <option value="DEMO">DEMO</option>
                    <option value="USER_ENTERED">USER ENTERED</option>
                </select>""")
html = html.replace('<th>Status</th><th>Actions</th>',
'<th>Status</th><th>Data Source</th><th>Actions</th>')

with open(r'templates\admin.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated admin.html")
