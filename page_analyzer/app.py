from flask import Flask, render_template, request, redirect, url_for, flash
import os
from urllib.parse import urlparse
from dotenv import load_dotenv
import psycopg2
from database import db

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


def get_db_connection():

    db_url = os.getenv('DATABASE_URL')


    parsed_url = urlparse(db_url)


    conn_params = {
        'dbname': parsed_url.path[1:],
        'user': parsed_url.username,
        'password': parsed_url.password,
        'host': parsed_url.hostname,
        'port': parsed_url.port,
    }

    conn = psycopg2.connect(**conn_params)
    return conn



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_url', methods=['POST'])
def add_url():
    url = request.form['url']
    if not url or len(url) > 255:
        flash('Некорректный URL', 'error')
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO urls (name) VALUES (%s) ON CONFLICT (name) DO NOTHING RETURNING id", (url,))
        url_id = cur.fetchone()
        conn.commit()
        if url_id:
            flash('Страница успешно добавлена', 'success')
        else:
            flash('Страница уже существует', 'info')
    except Exception as e:
        flash('Ошибка при добавлении URL', 'error')
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('index'))


@app.get('/urls/<int:id>')
def show_url(id):
    url = db.get_url_by_id(id)
    if not url:
        flash('Сайт не найден', 'danger')
        return redirect(url_for('show_urls'))


    checks = db.get_url_checks(id)

    return render_template('url.html', url=url, checks=checks)



@app.post('/urls/<int:id>/checks')
def check_url(id):
    url = db.get_url_by_id(id)
    if not url:
        flash('Сайт не найден', 'danger')
        return redirect(url_for('show_urls'))

    try:
        # Пока создаем "пустую" проверку (остальные поля будут на след. шаге)
        db.create_url_check({
            'url_id': id,
            # status_code, h1 и др. пока NULL
        })
        flash('Страница успешно проверена', 'success')
    except Exception as e:
        flash('Ошибка при проверке', 'danger')

    return redirect(url_for('show_url', id=id))



@app.get('/urls')
def show_urls():
    urls = db.get_urls()  # Используем новую функцию из db.py
    return render_template('urls.html', urls=urls)