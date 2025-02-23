from flask import Flask, render_template, request, redirect, url_for, flash
import os
from urllib.parse import urlparse
from dotenv import load_dotenv
import psycopg2
from page_analyzer.database import db
import requests
from bs4 import BeautifulSoup


load_dotenv()

app = Flask(__name__, template_folder="templates")
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.jinja_env.filters['truncate'] = lambda s, length: (s[:length-3] + '...') if s and len(s) > length else s

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
    # ... валидация URL ...

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO urls (name) 
            VALUES (%s) 
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name 
            RETURNING id
        """, (url,))
        url_id = cur.fetchone()[0]
        conn.commit()
        flash('Страница успешно добавлена', 'success')
        return redirect(url_for('show_url', id=url_id))
    except Exception as e:
        conn.rollback()
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
    url_data = db.get_url_by_id(id)
    if not url_data:
        flash('Сайт не найден', 'danger')
        return redirect(url_for('show_urls'))

    try:
        response = requests.get(url_data[1], timeout=5)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')


        h1 = soup.h1.text.strip() if soup.h1 else None
        title = soup.title.text.strip() if soup.title else None
        description_tag = soup.find('meta', attrs={'name': 'description'})
        description = description_tag['content'].strip() if description_tag else None

        db.create_url_check({
            'url_id': id,
            'status_code': response.status_code,
            'h1': h1,
            'title': title,
            'description': description
        })
        flash('Страница успешно проверена', 'success')
    except requests.exceptions.RequestException:
        flash('Произошла ошибка при проверке', 'danger')
    except Exception as e:
        flash('Непредвиденная ошибка', 'danger')

    return redirect(url_for('show_url', id=id))



@app.get('/urls')
def show_urls():
    urls = db.get_urls()
    return render_template('urls.html', urls=urls)