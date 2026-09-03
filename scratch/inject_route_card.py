import re

with open(r'templates\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# I will inject the Route & Stops card right after the eta-info card
route_stops_html = """
            <div class="card" id="route-stops-card" style="display:none; max-height: 400px; overflow-y: auto;">
                <h2>Route & Stops</h2>
                <div id="route-stops-container"></div>
            </div>
"""
if 'id="route-stops-card"' not in html:
    html = html.replace('</div>\n        </section>', '</div>\n' + route_stops_html + '\n        </section>')
    with open(r'templates\index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Updated index.html")
else:
    print("Already updated index.html")
