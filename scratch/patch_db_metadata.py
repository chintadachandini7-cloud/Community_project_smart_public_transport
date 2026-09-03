with open('database.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Add ALTER TABLE for buses
bus_alters = """
    if 'conductor_id' not in buses_columns:
        cursor.execute("ALTER TABLE buses ADD COLUMN conductor_id INTEGER")
    if 'source_url' not in buses_columns:
        cursor.execute("ALTER TABLE buses ADD COLUMN source_url TEXT")
    if 'source_name' not in buses_columns:
        cursor.execute("ALTER TABLE buses ADD COLUMN source_name TEXT")
    if 'source_type' not in buses_columns:
        cursor.execute("ALTER TABLE buses ADD COLUMN source_type TEXT")
    if 'verified_at' not in buses_columns:
        cursor.execute("ALTER TABLE buses ADD COLUMN verified_at TEXT")
"""
code = code.replace("""    if 'conductor_id' not in buses_columns:
        cursor.execute("ALTER TABLE buses ADD COLUMN conductor_id INTEGER")""", bus_alters)

# Add ALTER TABLE for routes
route_alters = """
    if 'data_source' not in routes_columns:
        cursor.execute("ALTER TABLE routes ADD COLUMN data_source TEXT DEFAULT 'OFFICIAL'")
    if 'source_url' not in routes_columns:
        cursor.execute("ALTER TABLE routes ADD COLUMN source_url TEXT")
    if 'source_name' not in routes_columns:
        cursor.execute("ALTER TABLE routes ADD COLUMN source_name TEXT")
    if 'source_type' not in routes_columns:
        cursor.execute("ALTER TABLE routes ADD COLUMN source_type TEXT")
    if 'verified_at' not in routes_columns:
        cursor.execute("ALTER TABLE routes ADD COLUMN verified_at TEXT")
"""
code = code.replace("""    if 'data_source' not in routes_columns:
        cursor.execute("ALTER TABLE routes ADD COLUMN data_source TEXT DEFAULT 'OFFICIAL'")""", route_alters)

# Add ALTER TABLE for stops
stop_alters = """
    if 'data_source' not in stops_columns:
        cursor.execute("ALTER TABLE stops ADD COLUMN data_source TEXT DEFAULT 'OFFICIAL'")
    if 'source_url' not in stops_columns:
        cursor.execute("ALTER TABLE stops ADD COLUMN source_url TEXT")
    if 'source_name' not in stops_columns:
        cursor.execute("ALTER TABLE stops ADD COLUMN source_name TEXT")
    if 'source_type' not in stops_columns:
        cursor.execute("ALTER TABLE stops ADD COLUMN source_type TEXT")
    if 'verified_at' not in stops_columns:
        cursor.execute("ALTER TABLE stops ADD COLUMN verified_at TEXT")
"""
code = code.replace("""    if 'data_source' not in stops_columns:
        cursor.execute("ALTER TABLE stops ADD COLUMN data_source TEXT DEFAULT 'OFFICIAL'")""", stop_alters)

with open('database.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Patched database.py")
