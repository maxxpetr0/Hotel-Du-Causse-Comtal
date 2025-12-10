import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_activity_log_table():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            username VARCHAR(100),
            action_type VARCHAR(50) NOT NULL,
            action_details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()

def log_activity(user_id, username, action_type, action_details=None):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute('''
        INSERT INTO activity_logs (user_id, username, action_type, action_details)
        VALUES (%s, %s, %s, %s)
    ''', (user_id, username, action_type, action_details))
    
    conn.commit()
    cur.close()
    conn.close()

def get_activity_logs(limit=100):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute('''
        SELECT id, user_id, username, action_type, action_details, created_at
        FROM activity_logs
        ORDER BY created_at DESC
        LIMIT %s
    ''', (limit,))
    
    logs = cur.fetchall()
    cur.close()
    conn.close()
    return logs

def get_action_label(action_type):
    labels = {
        'login': 'Connexion',
        'logout': 'Déconnexion',
        'ota_helper_open': 'Ouverture OTA Helper',
        'ota_helper_generate': 'Génération résumé OTA',
        'cms_helper_open': 'Ouverture CMS Helper',
        'cms_helper_generate': 'Génération tableau CMS',
        'backoffice_open': 'Ouverture Back Office',
        'user_created': 'Création utilisateur',
        'user_deleted': 'Suppression utilisateur',
        'user_password_changed': 'Modification mot de passe',
        'user_admin_toggled': 'Modification droits admin'
    }
    return labels.get(action_type, action_type)
