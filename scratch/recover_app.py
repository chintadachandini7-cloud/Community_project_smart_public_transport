import json
import re

app_lines = {}

with open('scratch/view_file_history.txt', 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        # the response might be in content, or in tool_responses
        # let's just use a regex to find all "<number>: <code line>"
        # in the whole serialized JSON string
        txt = json.dumps(data)
        # However, it's heavily escaped. Let's just find "Showing lines" in the string and extract the lines.
        # It's better to recursively find string values and regex them.
        def extract_strings(obj):
            if isinstance(obj, str):
                matches = re.findall(r'^(\d+):\s(.*)$', obj, flags=re.MULTILINE)
                for num_str, code_line in matches:
                    app_lines[int(num_str)] = code_line
            elif isinstance(obj, dict):
                for v in obj.values(): extract_strings(v)
            elif isinstance(obj, list):
                for v in obj: extract_strings(v)
                
        extract_strings(data)

# Reconstruct app.py
if not app_lines:
    print("No lines found!")
    exit(1)

max_line = max(app_lines.keys())
missing = []
with open('app_recovered.py', 'w', encoding='utf-8') as f:
    for i in range(1, max_line + 1):
        if i in app_lines:
            f.write(app_lines[i] + '\n')
        else:
            missing.append(i)
            f.write(f'# MISSING LINE {i}\n')

print(f"Recovered {len(app_lines)} lines out of {max_line}. Missing: {missing}")
