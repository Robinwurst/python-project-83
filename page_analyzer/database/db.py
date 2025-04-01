from psycopg2.extras import DictCursor


def get_url_id_by_name(conn, url):
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT id FROM urls WHERE name = %s", (url,))
        result = cur.fetchone()
        return result['id'] if result else None


def insert_url(conn, url):
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute(
            "INSERT INTO urls (name) VALUES (%s) RETURNING id",
            (url,)
        )
        return cur.fetchone()['id']


def get_url_by_id(conn, url_id):
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT * FROM urls WHERE id = %s", (url_id,))
        result = cur.fetchone()
        return dict(result) if result else None


def insert_url_check(conn, check_data):
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("""
            INSERT INTO url_checks (
                url_id,
                status_code,
                h1,
                title,
                description
            ) VALUES (%s, %s, %s, %s, %s)
        """, (
            check_data['url_id'],
            check_data['status_code'],
            check_data.get('h1', ''),
            check_data.get('title', ''),
            check_data.get('description', '')
        ))
        conn.commit()


def get_url_checks(conn, url_id):
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("""
            SELECT id, status_code, h1, title, description, created_at
            FROM url_checks
            WHERE url_id = %s
            ORDER BY created_at DESC
        """, (url_id,))
        return [{
            'id': row['id'],
            'status_code': row['status_code'],
            'h1': row['h1'] or '',
            'title': row['title'] or '',
            'description': row['description'] or '',
            'created_at': row['created_at']
        } for row in cur.fetchall()]


def get_all_urls(conn):
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("SELECT id, name, created_at FROM urls ORDER BY id DESC")
        return [dict(row) for row in cur.fetchall()]


def get_latest_checks(conn):
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("""
            SELECT
                url_id,
                MAX(created_at) AS last_check,
                MAX(status_code) AS last_status
            FROM url_checks
            GROUP BY url_id
        """)
        return {
            row['url_id']: {
                'last_check': row['last_check'],
                'last_status': row['last_status']
            } for row in cur.fetchall()
        }


def get_all_urls_with_checks(conn):
    urls = get_all_urls(conn)
    checks = get_latest_checks(conn)

    return [{
        'id': url['id'],
        'name': url['name'],
        'last_check': checks.get(url['id'], {}).get('last_check'),
        'last_status': checks.get(url['id'], {}).get('last_status')
    } for url in urls]
