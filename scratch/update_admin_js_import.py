with open(r'static\js\admin.js', 'r', encoding='utf-8') as f:
    js = f.read()

import_js = """
// --- IMPORT LOGIC ---
let pendingImportData = null;

function csvJSON(csv) {
    const lines = csv.split('\\n');
    const result = [];
    const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
    
    for(let i = 1; i < lines.length; i++) {
        if(!lines[i].trim()) continue;
        const obj = {};
        // Simple split (does not handle commas inside quotes well, but good enough for test)
        const currentline = lines[i].split(',');
        for(let j = 0; j < headers.length; j++) {
            obj[headers[j]] = currentline[j] ? currentline[j].trim().replace(/^"|"$/g, '') : '';
        }
        result.push(obj);
    }
    return result;
}

window.previewImport = async function() {
    const fileInput = document.getElementById('import_file');
    if(!fileInput.files.length) return alert("Please select a file.");
    
    const file = fileInput.files[0];
    const reader = new FileReader();
    
    reader.onload = async function(e) {
        let records = [];
        try {
            if(file.name.endsWith('.json')) {
                records = JSON.parse(e.target.result);
            } else if (file.name.endsWith('.csv')) {
                records = csvJSON(e.target.result);
            } else {
                return alert("Unsupported file format.");
            }
            
            const res = await fetch('/api/import/preview', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({records: records})
            });
            const data = await res.json();
            
            pendingImportData = data;
            
            document.getElementById('import_preview_area').style.display = 'block';
            document.getElementById('prev_adds').innerText = data.adds.length;
            document.getElementById('prev_updates').innerText = data.updates.length;
            document.getElementById('prev_dups').innerText = data.duplicates.length;
            document.getElementById('prev_rejs').innerText = data.rejected.length;
            
            let errHtml = '';
            if(data.rejected.length > 0) {
                errHtml += '<h4>Errors:</h4><ul>';
                data.rejected.slice(0, 10).forEach(r => {
                    errHtml += `<li>Row [${r.row.Type || 'Unknown'}]: ${r.error}</li>`;
                });
                if(data.rejected.length > 10) errHtml += '<li>...and more</li>';
                errHtml += '</ul>';
            }
            document.getElementById('import_errors').innerHTML = errHtml;
            
        } catch(err) {
            alert("Error parsing file: " + err.message);
        }
    };
    reader.readAsText(file);
}

window.cancelImport = function() {
    pendingImportData = null;
    document.getElementById('import_file').value = '';
    document.getElementById('import_preview_area').style.display = 'none';
}

window.commitImport = async function() {
    if(!pendingImportData) return;
    
    try {
        const res = await fetch('/api/import/commit', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                adds: pendingImportData.adds,
                updates: pendingImportData.updates
            })
        });
        const data = await res.json();
        
        if(data.success) {
            alert(`Import Successful!\\nRoutes: ${data.stats.routes}\\nBuses: ${data.stats.buses}\\nStops: ${data.stats.stops}`);
            cancelImport();
            loadRoutes();
            loadStops();
            loadBuses();
        } else {
            alert("Error during import.");
        }
    } catch(err) {
        alert("Network error.");
    }
}
"""

js += "\n" + import_js

with open(r'static\js\admin.js', 'w', encoding='utf-8') as f:
    f.write(js)
print("Updated admin.js")
