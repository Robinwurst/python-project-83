import psycopg2
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()


def get_connection():
    db_url = os.getenv('DATABASE_URL')
    parsed_url = urlparse(db_url)
    conn_params = {
        'dbname': parsed_url.path[1:],
        'user': parsed_url.username,
        'password': parsed_url.password,
        'host': parsed_url.hostname,
        'port': parsed_url.port,
    }
    return psycopg2.connect(**conn_params)


def get_url_id_by_name(url):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM urls WHERE name = %s", (url,))
            result = cur.fetchone()
            return result[0] if result else None


def insert_url(url):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO urls (name) VALUES (%s) RETURNING id",
                (url,)
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            return new_id


def get_url_by_id(url_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM urls WHERE id = %s", (url_id,))
            result = cur.fetchone()
            return {
                'id': result[0],
                'name': result[1],
                'created_at': result[2]
            } if result else None


def insert_url_check(check_data):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO url_checks (
                    url_id,
                    status_code,
                    h1,
                    title,
                    description
                ) VALUES (%s, %s, %s, %s, %s)
                RETURNING id, created_at
            """, (
                check_data['url_id'],
                check_data['status_code'],
                check_data.get('h1'),
                check_data.get('title'),
                check_data.get('description')
            ))
            conn.commit()


def get_url_checks(url_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, status_code, h1, title, description, created_at
                FROM url_checks
                WHERE url_id = %s
                ORDER BY created_at DESC
            """, (url_id,))
            return [{
                'id': row[0],
                'status_code': row[1],
                'h1': row[2],
                'title': row[3],
                'description': row[4],
                'created_at': row[5]
            } for row in cur.fetchall()]


def get_all_urls_with_checks():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    u.id,
                    u.name,
                    MAX(uc.created_at) AS last_check_date,
                    MAX(uc.status_code) AS last_check_status
                FROM urls u
                LEFT JOIN url_checks uc ON u.id = uc.url_id
                GROUP BY u.id
                ORDER BY u.id DESC
            """)
            return [{
                'id': row[0],
                'name': row[1],
                'last_check': row[2],
                'last_status': row[3]
            } for row in cur.fetchall()]
