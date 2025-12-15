import hashlib
import secrets
from psycopg2.extras import RealDictCursor
from datetime import datetime
from db_pool import get_connection

_user_exists_cache = None

def init_users_table():
    with get_connection() as conn:
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
        cur.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        conn.commit()
        cur.close()

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(32)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return password_hash, salt

def create_user(username, password, is_admin=False):
    global _user_exists_cache
    with get_connection() as conn:
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
            _user_exists_cache = True
            return result[0] if result else None
        except Exception:
            conn.rollback()
            return None
        finally:
            cur.close()

def verify_user(username, password):
    with get_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('''
            SELECT id, username, password_hash, salt, is_admin
            FROM users WHERE username = %s
        ''', (username.lower().strip(),))
        user = cur.fetchone()
        
        if user:
            password_hash, _ = hash_password(password, user['salt'])
            if password_hash == user['password_hash']:
                cur.execute('UPDATE users SET last_login = %s WHERE id = %s', (datetime.now(), user['id']))
                conn.commit()
                cur.close()
                return {'id': user['id'], 'username': user['username'], 'is_admin': user['is_admin']}
        cur.close()
        return None

def get_all_users():
    with get_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT id, username, is_admin, created_at, last_login FROM users ORDER BY created_at DESC')
        users = cur.fetchall()
        cur.close()
        return users

def delete_user(user_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM users WHERE id = %s', (user_id,))
        conn.commit()
        cur.close()

def update_user_password(user_id, new_password):
    with get_connection() as conn:
        cur = conn.cursor()
        password_hash, salt = hash_password(new_password)
        cur.execute('UPDATE users SET password_hash = %s, salt = %s WHERE id = %s', (password_hash, salt, user_id))
        conn.commit()
        cur.close()

def toggle_admin(user_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('UPDATE users SET is_admin = NOT is_admin WHERE id = %s', (user_id,))
        conn.commit()
        cur.close()

def count_admins():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM users WHERE is_admin = TRUE')
        count = cur.fetchone()[0]
        cur.close()
        return count

def user_exists():
    global _user_exists_cache
    if _user_exists_cache is not None:
        return _user_exists_cache
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('SELECT EXISTS(SELECT 1 FROM users LIMIT 1)')
        exists = cur.fetchone()[0]
        cur.close()
        _user_exists_cache = exists
        return exists
