import re
from psycopg2.extras import RealDictCursor
from db_pool import get_connection

def sanitize_card_numbers(text):
    if not text:
        return text
    patterns = [r'\b(?:\d{4}[-\s]?){3}\d{4}\b', r'\b\d{15,16}\b', r'\b(?:\d{4}[-\s]?){2}\d{4,6}\b']
    sanitized = text
    for pattern in patterns:
        sanitized = re.sub(pattern, '[CARTE MASQUÉE]', sanitized)
    return sanitized

def init_db():
    with get_connection() as conn:
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
        cur.execute('CREATE INDEX IF NOT EXISTS idx_summaries_created_at ON summaries(created_at DESC)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_summaries_platform ON summaries(platform)')
        conn.commit()
        cur.close()

def save_summary(data, summary_text, receptionist_name, email_raw):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO summaries (platform, receptionist_name, guest_name, reservation_id,
                tarif, vad, commission, date_arrivee, date_depart, sejour_details, summary_text, email_raw)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        ''', (
            data.get('platform'), receptionist_name, data.get('guest_name'), data.get('reservation_id'),
            data.get('tarif'), data.get('vad'), data.get('commission'), data.get('dates_arrivee'),
            data.get('dates_depart'), sanitize_card_numbers(data.get('sejour_details')),
            sanitize_card_numbers(summary_text), sanitize_card_numbers(email_raw)
        ))
        result = cur.fetchone()
        conn.commit()
        cur.close()
        return result[0] if result else None

def get_summaries(limit=50, search_query=None, platform_filter=None):
    with get_connection() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = '''SELECT id, created_at, platform, receptionist_name, guest_name, reservation_id,
                   tarif, vad, commission, date_arrivee, date_depart, sejour_details, summary_text
                   FROM summaries WHERE 1=1'''
        params = []
        if search_query:
            query += ' AND (guest_name ILIKE %s OR reservation_id ILIKE %s)'
            search_pattern = f'%{search_query}%'
            params.extend([search_pattern, search_pattern])
        if platform_filter and platform_filter != 'all':
            query += ' AND platform = %s'
            params.append(platform_filter)
        query += ' ORDER BY created_at DESC LIMIT %s'
        params.append(limit)
        cur.execute(query, params)
        results = cur.fetchall()
        cur.close()
        return results
