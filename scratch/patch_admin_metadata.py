import re

with open(r'templates\admin.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ROUTES
html = html.replace('<th>Data Source</th><th>Actions</th>', '<th>Data Source</th><th>Verified</th><th>Actions</th>')

# STOPS
html = html.replace('<th>Data Source</th><th>Actions</th>', '<th>Data Source</th><th>Verified</th><th>Actions</th>')

# BUSES
html = html.replace('<th>Data Source</th><th>Actions</th>', '<th>Data Source</th><th>Verified</th><th>Actions</th>')

with open(r'templates\admin.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Patched admin.html")

with open(r'static\js\admin.js', 'r', encoding='utf-8') as f:
    js = f.read()

badge_code = """function getBadge(ds) {
    if(ds === 'OFFICIAL') return `<span style="background:#28a745; color:white; padding:3px 6px; border-radius:4px; font-size:12px;">OFFICIAL DATA</span>`;
    if(ds === 'DEMO') return `<span style="background:#ffc107; color:#333; padding:3px 6px; border-radius:4px; font-size:12px;">DEMO DATA</span>`;
    if(ds === 'USER_ENTERED') return `<span style="background:#17a2b8; color:white; padding:3px 6px; border-radius:4px; font-size:12px;">USER ENTERED</span>`;
    return `<span style="background:#6c757d; color:white; padding:3px 6px; border-radius:4px; font-size:12px;">${ds || 'UNKNOWN'}</span>`;
}"""

verify_badge_code = badge_code + """
function getVerifyBadge(item) {
    if(item.data_source === 'OFFICIAL' && item.verified_at) {
        let urlLink = item.source_url ? `<br><a href="${item.source_url}" target="_blank" style="font-size:10px;">${item.source_type || 'Source'}</a>` : '';
        return `<span style="font-size:11px; color:#555;">${item.verified_at}</span>${urlLink}`;
    }
    return '--';
}
"""
js = js.replace(badge_code, verify_badge_code)

# Routes rendering
js = js.replace("""<td>${getBadge(r.data_source)}</td>
                    <td>
                        <button onclick="editRoute(${r.id}""", """<td>${getBadge(r.data_source)}</td>
                    <td>${getVerifyBadge(r)}</td>
                    <td>
                        <button onclick="editRoute(${r.id}""")

# Stops rendering
js = js.replace("""<td>${getBadge(s.data_source)}</td>
                    <td>
                        <button onclick="editStop(${s.id}""", """<td>${getBadge(s.data_source)}</td>
                    <td>${getVerifyBadge(s)}</td>
                    <td>
                        <button onclick="editStop(${s.id}""")

# Buses rendering
js = js.replace("""<td>${getBadge(b.data_source)}</td>
                    <td>
                        <button onclick="editBus(${b.id}""", """<td>${getBadge(b.data_source)}</td>
                    <td>${getVerifyBadge(b)}</td>
                    <td>
                        <button onclick="editBus(${b.id}""")

with open(r'static\js\admin.js', 'w', encoding='utf-8') as f:
    f.write(js)
print("Patched admin.js")
