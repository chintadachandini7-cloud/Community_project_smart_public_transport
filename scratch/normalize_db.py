import sqlite3
conn = sqlite3.connect('transport.db')
conn.execute("UPDATE buses SET data_source='DEMO'")
conn.execute("UPDATE routes SET data_source='DEMO'")
conn.execute("UPDATE stops SET data_source='DEMO'")
conn.commit()
conn.close()
print("Updated all mock records to DEMO.")
