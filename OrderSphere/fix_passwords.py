"""
fix_passwords.py
Optional repair script to regenerate demo-user Werkzeug hashes after setup_db.sql.

Usage:
    python fix_passwords.py
"""
import mysql.connector
from werkzeug.security import generate_password_hash

CREDENTIALS = {
    'admin':       'Admin@123',
    'agent_raj':   'Agent@123',
    'agent_priya': 'Agent@123',
    'john_doe':    'User@123',
}

conn = mysql.connector.connect(
    host='localhost', user='root', password='123456', database='ordersphere_db'
)
cur = conn.cursor()

for username, plain_pw in CREDENTIALS.items():
    hashed = generate_password_hash(plain_pw)
    cur.execute(
        "UPDATE users SET password=%s WHERE username=%s",
        (hashed, username)
    )
    print(f"  ✅  {username} → password hash updated")

conn.commit()
cur.close()
conn.close()
print("\nAll passwords fixed! You can now log in.")
