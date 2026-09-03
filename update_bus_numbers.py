import sqlite3

def update_bus_numbers():
    conn = sqlite3.connect('transport.db')
    buses = conn.execute("SELECT id FROM buses").fetchall()
    
    for i, bus in enumerate(buses):
        new_number = f"B-10{i+1}"
        conn.execute("UPDATE buses SET bus_number=? WHERE id=?", (new_number, bus[0]))
        
    conn.commit()
    conn.close()
    print("Bus numbers updated to B-101, B-102 format.")

if __name__ == '__main__':
    update_bus_numbers()
