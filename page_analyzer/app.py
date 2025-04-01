from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from psycopg2.extras import DictCursor
import os
from dotenv import load_dotenv
from .logger import logger
from .utils import normalize_url, validate_url, get_page_data
from .database import (
    get_url_id_by_name,
    insert_url,
    get_url_by_id,
    insert_url_check,
    get_url_checks,
    get_all_urls_with_checks
)
from .messages import (
    PAGE_EXISTS, PAGE_ADDED, DB_ERROR,
    UNEXPECTED_ERROR, SITE_NOT_FOUND,
    CHECK_SUCCESS, CHECK_FAILED,
    ALERT_SUCCESS, ALERT_DANGER, ALERT_INFO
)

load_dotenv()

app = Flask(__name__, template_folder="templates")
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')


def get_db_connection():
    return psycopg2.connect(
        app.config['DATABASE_URL'],
        cursor_factory=DictCursor
    )


@app.route('/')
def index():
    return render_template('index.html')


@app.post('/urls')
def add_url():
    conn = get_db_connection()
    try:
        raw_url = request.form.get('url', '').strip()

        error_message, status_code = validate_url(raw_url)
        if error_message:
            flash(error_message, ALERT_DANGER)
            return render_template('index.html'), status_code

        normalized_url = normalize_url(raw_url)
        existing_id = get_url_id_by_name(conn, normalized_url)
        if existing_id:
            flash(PAGE_EXISTS, ALERT_INFO)
            return render_template('index.html'), 200

        new_id = insert_url(conn, normalized_url)
        flash(PAGE_ADDED, ALERT_SUCCESS)
        return render_template('index.html'), 200

    except Exception as e:
        conn.rollback()
        logger.error(f"Ошибка базы данных: {str(e)}")
        flash(DB_ERROR, ALERT_DANGER)
        return render_template('index.html'), 500
    finally:
        conn.close()


@app.get('/urls/<int:id>')
def show_url(id):
    conn = get_db_connection()
    try:
        url = get_url_by_id(conn, id)
        if not url:
            flash(SITE_NOT_FOUND, ALERT_DANGER)
            return redirect(url_for('show_urls'))

        checks = get_url_checks(conn, id)
        return render_template('url.html', url=url, checks=checks)

    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        flash(UNEXPECTED_ERROR, ALERT_DANGER)
        return redirect(url_for('index'))
    finally:
        conn.close()


@app.post('/urls/<int:id>/checks')
def check_url(id):
    conn = get_db_connection()
    try:
        url_data = get_url_by_id(conn, id)
        if not url_data:
            flash(SITE_NOT_FOUND, ALERT_DANGER)
            return redirect(url_for('show_urls'))

        page_data = get_page_data(url_data['name'])
        if page_data:
            insert_url_check(conn, {
                'url_id': id,
                'status_code': page_data['status_code'],
                'h1': page_data['h1'],
                'title': page_data['title'],
                'description': page_data['description']
            })
            flash(CHECK_SUCCESS, ALERT_SUCCESS)
        else:
            flash(CHECK_FAILED, ALERT_DANGER)

        checks = get_url_checks(conn, id)
        return render_template('url.html', url=url_data, checks=checks)

    except Exception as e:
        conn.rollback()
        logger.error(f"General error: {str(e)}")
        flash(UNEXPECTED_ERROR, ALERT_DANGER)
        return redirect(url_for('show_url', id=id))
    finally:
        conn.close()


@app.get('/urls')
def show_urls():
    conn = get_db_connection()
    try:
        urls = get_all_urls_with_checks(conn)
        return render_template('urls.html', urls=urls)
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        flash(DB_ERROR, ALERT_DANGER)
        return redirect(url_for('index'))
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)
