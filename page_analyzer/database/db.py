import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def get_url_by_id(url_id):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM urls WHERE id = %s",
                (url_id,)
            )
            return cursor.fetchone()


def create_url_check(data):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO url_checks 
                (url_id, status_code, created_at)
                VALUES (%s, %s, NOW()) RETURNING id""",
                (data['url_id'], data.get('status_code'))
            )
            check_id = cursor.fetchone()[0]
            conn.commit()
            return check_id

def get_url_checks(url_id):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, url_id, status_code, h1, title, created_at "
                "FROM url_checks WHERE url_id = %s ORDER BY id DESC",
                (url_id,)
            )
            return cursor.fetchall()


def get_urls():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    u.id, 
                    u.name, 
                    u.created_at, 
                    MAX(uc.created_at),
                    MAX(uc.status_code)
                FROM urls u
                LEFT JOIN url_checks uc ON u.id = uc.url_id
                GROUP BY u.id
                ORDER BY u.id DESC
            """)
            return cursor.fetchall()