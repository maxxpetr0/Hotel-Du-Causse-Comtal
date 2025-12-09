import os
import re
import hashlib
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime


def sanitize_card_numbers(text):
    """Remove credit card numbers from text to protect sensitive data."""
    if not text:
        return text
    
    patterns = [
        r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        r'\b\d{15,16}\b',
        r'\b(?:\d{4}[-\s]?){2}\d{4,6}\b',
    ]
    
    sanitized = text
    for pattern in patterns:
        sanitized = re.sub(pattern, '[CARTE MASQUÉE]', sanitized)
    
    return sanitized

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_connection():
    """Get database connection."""
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """Initialize the database tables."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS summaries (
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            platform VARCHAR(100),
            receptionist_name VARCHAR(200),
            guest_name VARCHAR(200),
            reservation_id VARCHAR(100),
            tarif DECIMAL(10, 2),
            vad DECIMAL(10, 2),
            commission DECIMAL(10, 2),
            date_arrivee VARCHAR(50),
            date_depart VARCHAR(50),
            sejour_details TEXT,
            summary_text TEXT,
            email_raw TEXT
        )
    ''')
    
    cur.execute('''
        CREATE INDEX IF NOT EXISTS idx_summaries_created_at 
        ON summaries(created_at DESC)
    ''')
    
    cur.execute('''
        CREATE INDEX IF NOT EXISTS idx_summaries_platform 
        ON summaries(platform)
    ''')
    
    cur.execute('''
        CREATE INDEX IF NOT EXISTS idx_summaries_guest_name 
        ON summaries(guest_name)
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(256) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()


def hash_password(password, salt=None):
    """Hash a password using SHA-256 with salt for security."""
    if salt is None:
        salt = os.environ.get('SESSION_SECRET', 'default_salt_ota_helper')
    salted_password = f"{salt}{password}{salt}"
    return hashlib.sha256(salted_password.encode()).hexdigest()


def register_user(username, password):
    """Register a new user. Returns True if successful, False if username exists."""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            INSERT INTO users (username, password_hash)
            VALUES (%s, %s)
        ''', (username.strip().lower(), hash_password(password)))
        conn.commit()
        success = True
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        success = False
    
    cur.close()
    conn.close()
    return success


def authenticate_user(username, password):
    """Authenticate a user. Returns user dict if valid, None otherwise."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute('''
        SELECT id, username, is_active FROM users
        WHERE username = %s AND password_hash = %s AND is_active = TRUE
    ''', (username.strip().lower(), hash_password(password)))
    
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    return user


def get_user_count():
    """Get the number of registered users."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) FROM users')
    count = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    return count

def save_summary(data, summary_text, receptionist_name, email_raw):
    """Save a summary to the database. Card numbers are automatically sanitized."""
    conn = get_connection()
    cur = conn.cursor()
    
    safe_email_raw = sanitize_card_numbers(email_raw)
    safe_summary_text = sanitize_card_numbers(summary_text)
    safe_sejour_details = sanitize_card_numbers(data.get('sejour_details'))
    
    cur.execute('''
        INSERT INTO summaries (
            platform, receptionist_name, guest_name, reservation_id,
            tarif, vad, commission, date_arrivee, date_depart,
            sejour_details, summary_text, email_raw
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    ''', (
        data.get('platform'),
        receptionist_name,
        data.get('guest_name'),
        data.get('reservation_id'),
        data.get('tarif'),
        data.get('vad'),
        data.get('commission'),
        data.get('dates_arrivee'),
        data.get('dates_depart'),
        safe_sejour_details,
        safe_summary_text,
        safe_email_raw
    ))
    
    result = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    return result[0] if result else None

def get_summaries(limit=50, search_query=None, platform_filter=None):
    """Get summaries from the database with optional filtering."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    query = '''
        SELECT id, created_at, platform, receptionist_name, guest_name,
               reservation_id, tarif, vad, commission, date_arrivee, 
               date_depart, sejour_details, summary_text
        FROM summaries
        WHERE 1=1
    '''
    params = []
    
    if search_query:
        query += ''' AND (
            guest_name ILIKE %s OR
            reservation_id ILIKE %s OR
            receptionist_name ILIKE %s OR
            summary_text ILIKE %s
        )'''
        search_pattern = f'%{search_query}%'
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
    
    if platform_filter and platform_filter != 'all':
        query += ' AND platform = %s'
        params.append(platform_filter)
    
    query += ' ORDER BY created_at DESC LIMIT %s'
    params.append(limit)
    
    cur.execute(query, params)
    results = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return results

def get_summary_by_id(summary_id):
    """Get a single summary by ID."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute('''
        SELECT * FROM summaries WHERE id = %s
    ''', (summary_id,))
    
    result = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return result

def delete_summary(summary_id):
    """Delete a summary by ID."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute('DELETE FROM summaries WHERE id = %s', (summary_id,))
    
    conn.commit()
    cur.close()
    conn.close()

def get_stats():
    """Get summary statistics."""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute('''
        SELECT 
            COUNT(*) as total_summaries,
            COUNT(DISTINCT platform) as platforms_used,
            COALESCE(SUM(tarif), 0) as total_tarif,
            COALESCE(SUM(commission), 0) as total_commission
        FROM summaries
    ''')
    
    result = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return result
