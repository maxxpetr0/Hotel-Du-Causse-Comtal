import os
import hashlib
import secrets
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_users_table():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(256) NOT NULL,
            salt VARCHAR(64) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    columns_to_add = [
        ("salt", "VARCHAR(64)", "''"),
        ("is_admin", "BOOLEAN", "FALSE"),
        ("last_login", "TIMESTAMP", "NULL")
    ]
    
    for col_name, col_type, default_val in columns_to_add:
        try:
            cur.execute(f'''
                ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type} DEFAULT {default_val}
            ''')
        except Exception:
            pass
    
    conn.commit()
    cur.close()
    conn.close()

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(32)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return password_hash, salt

def create_user(username, password, is_admin=False):
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        password_hash, salt = hash_password(password)
        cur.execute('''
            INSERT INTO users (username, password_hash, salt, is_admin)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        ''', (username.lower().strip(), password_hash, salt, is_admin))
        
        result = cur.fetchone()
        conn.commit()
        return result[0] if result else None
    except psycopg2.IntegrityError:
        conn.rollback()
        return None
    finally:
        cur.close()
        conn.close()

def verify_user(username, password):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute('''
        SELECT id, username, password_hash, salt, is_admin
        FROM users WHERE username = %s
    ''', (username.lower().strip(),))
    
    user = cur.fetchone()
    
    if user:
        password_hash, _ = hash_password(password, user['salt'])
        if password_hash == user['password_hash']:
            cur.execute('''
                UPDATE users SET last_login = %s WHERE id = %s
            ''', (datetime.now(), user['id']))
            conn.commit()
            cur.close()
            conn.close()
            return {
                'id': user['id'],
                'username': user['username'],
                'is_admin': user['is_admin']
            }
    
    cur.close()
    conn.close()
    return None

def get_all_users():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute('''
        SELECT id, username, is_admin, created_at, last_login
        FROM users ORDER BY created_at DESC
    ''')
    
    users = cur.fetchall()
    cur.close()
    conn.close()
    return users

def delete_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute('DELETE FROM users WHERE id = %s', (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def update_user_password(user_id, new_password):
    conn = get_connection()
    cur = conn.cursor()
    
    password_hash, salt = hash_password(new_password)
    cur.execute('''
        UPDATE users SET password_hash = %s, salt = %s WHERE id = %s
    ''', (password_hash, salt, user_id))
    
    conn.commit()
    cur.close()
    conn.close()

def toggle_admin(user_id):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute('''
        UPDATE users SET is_admin = NOT is_admin WHERE id = %s
    ''', (user_id,))
    
    conn.commit()
    cur.close()
    conn.close()

def count_admins():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) FROM users WHERE is_admin = TRUE')
    count = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    return count

def user_exists():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) FROM users')
    count = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    return count > 0
