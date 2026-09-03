import re

with open(r'templates\admin.html', 'r', encoding='utf-8') as f:
    html = f.read()

import_html = """
        <hr>

        <!-- IMPORT DATA SECTION -->
        <section id="import-section">
            <h2>Import Transport Data (CSV / JSON)</h2>
            <div class="info-box" style="background: #f8f9fa; padding: 15px; border-left: 4px solid #17a2b8; margin-bottom:15px;">
                <p>Upload a CSV or JSON file containing APSRTC / TGSRTC verified data.</p>
                <input type="file" id="import_file" accept=".csv, .json" style="margin-bottom:10px;">
                <button onclick="previewImport()" style="background:#17a2b8; color:white; padding:10px; border:none; cursor:pointer;">Preview Import</button>
            </div>
            
            <div id="import_preview_area" style="display:none;">
                <h3>Import Preview</h3>
                <p><strong>Adds:</strong> <span id="prev_adds">0</span> | <strong>Updates:</strong> <span id="prev_updates">0</span> | <strong>Duplicates:</strong> <span id="prev_dups">0</span> | <strong>Rejected:</strong> <span id="prev_rejs">0</span></p>
                
                <div id="import_errors" style="color:#dc3545; margin-bottom:15px;"></div>
                
                <button onclick="commitImport()" style="background:#28a745; color:white; padding:10px; border:none; cursor:pointer; font-weight:bold;">Confirm & Import</button>
                <button onclick="cancelImport()" style="background:#6c757d; color:white; padding:10px; border:none; cursor:pointer;">Cancel</button>
            </div>
        </section>
"""

html = html.replace("<!-- ROUTES SECTION -->", import_html + "\n        <!-- ROUTES SECTION -->")

with open(r'templates\admin.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated admin.html")
