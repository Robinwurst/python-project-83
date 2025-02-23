# from flask import Flask, render_template, request, redirect, url_for, flash
# import os
# from dotenv import load_dotenv
# import psycopg2
# from page_analyzer.database import db
# import requests
# from bs4 import BeautifulSoup
# from urllib.parse import urlparse
#
# load_dotenv()
#
# app = Flask(__name__, template_folder="templates")
# app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
# app.jinja_env.filters['truncate'] = lambda s, length: (s[:length - 3] + '...') if s and len(s) > length else s
#
#
# def get_db_connection():
#     db_url = os.getenv('DATABASE_URL')
#     parsed_url = urlparse(db_url)
#     conn_params = {
#         'dbname': parsed_url.path[1:],
#         'user': parsed_url.username,
#         'password': parsed_url.password,
#         'host': parsed_url.hostname,
#         'port': parsed_url.port,
#     }
#     return psycopg2.connect(**conn_params)
#
#
# @app.route('/')
# def index():
#     return render_template('index.html')
#
#
# @app.route('/add_url', methods=['POST'])
# def add_url():
#     url = request.form.get('url', '').strip()
#     if not url or len(url) > 255:
#         flash('Некорректный URL', 'danger')
#         return redirect(url_for('index'))
#
#     conn = get_db_connection()
#     cur = conn.cursor()
#     try:
#         cur.execute("""
#             INSERT INTO urls (name)
#             VALUES (%s)
#             ON CONFLICT (name) DO NOTHING
#             RETURNING id
#         """, (url,))
#         url_id = cur.fetchone()
#         conn.commit()
#         if url_id:
#             flash('Страница успешно добавлена', 'success')
#             return redirect(url_for('show_url', id=url_id[0]))
#         else:
#             # Если URL уже существует, находим его ID
#             cur.execute("SELECT id FROM urls WHERE name = %s", (url,))
#             existing_url_id = cur.fetchone()[0]
#             flash('Страница уже существует', 'info')
#             return redirect(url_for('show_url', id=existing_url_id))
#     except Exception as e:
#         conn.rollback()
#         flash('Ошибка при добавлении URL', 'danger')
#         app.logger.error(f"Ошибка: {str(e)}")
#     finally:
#         cur.close()
#         conn.close()
#     return redirect(url_for('index'))
#
#
# @app.get('/urls/<int:id>')
# def show_url(id):
#     url = db.get_url_by_id(id)
#     if not url:
#         flash('Сайт не найден', 'danger')
#         return redirect(url_for('show_urls'))
#
#     checks = db.get_url_checks(id)
#     return render_template('url.html', url=url, checks=checks)
#
#
# @app.post('/urls/<int:id>/checks')
# def check_url(id):
#     url_data = db.get_url_by_id(id)
#     if not url_data:
#         flash('Сайт не найден', 'danger')
#         return redirect(url_for('show_urls'))
#
#     try:
#         response = requests.get(url_data['name'], timeout=5)
#         response.raise_for_status()
#         soup = BeautifulSoup(response.text, 'html.parser')
#
#         h1 = soup.h1.text.strip() if soup.h1 else None
#         title = soup.title.text.strip() if soup.title else None
#         description_tag = soup.find('meta', attrs={'name': 'description'})
#         description = description_tag['content'].strip() if description_tag else None
#
#         db.create_url_check({
#             'url_id': id,
#             'status_code': response.status_code,
#             'h1': h1,
#             'title': title,
#             'description': description
#         })
#         flash('Страница успешно проверена', 'success')
#     except requests.exceptions.RequestException:
#         flash('Произошла ошибка при проверке', 'danger')
#     except Exception as e:
#         flash('Непредвиденная ошибка', 'danger')
#         app.logger.error(f"Ошибка проверки: {str(e)}")
#     return redirect(url_for('show_url', id=id))
#
#
# @app.get('/urls')
# def show_urls():
#     urls = db.get_urls()
#     return render_template('urls.html', urls=urls)
#


from flask import Flask, render_template, request, redirect, url_for, flash
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
import logging
import requests
from bs4 import BeautifulSoup
from page_analyzer.database import db

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates")
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.jinja_env.filters['truncate'] = lambda s, length: (s[:length - 3] + '...') if s and len(s) > length else s


def normalize_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}".lower().rstrip('/')


def is_valid_url(url):
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False
        return result.scheme in ['http', 'https']
    except ValueError:
        return False


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/add_url', methods=['POST'])
def add_url():
    raw_url = request.form.get('url', '').strip()

    if not raw_url:
        flash('URL обязателен', 'danger')
        return redirect(url_for('index'))

    if len(raw_url) > 255:
        flash('URL превышает 255 символов', 'danger')
        return redirect(url_for('index'))

    if not is_valid_url(raw_url):
        flash('Некорректный URL', 'danger')
        return redirect(url_for('index'))

    try:
        normalized_url = normalize_url(raw_url)
        existing_id = db.get_url_id_by_name(normalized_url)

        if existing_id:
            flash('Страница уже существует', 'info')
            return redirect(url_for('show_url', id=existing_id))

        new_id = db.insert_url(normalized_url)
        flash('Страница успешно добавлена', 'success')
        return redirect(url_for('show_url', id=new_id))

    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        flash('Ошибка при обработке запроса', 'danger')
        return redirect(url_for('index'))


@app.get('/urls/<int:id>')
def show_url(id):
    try:
        url = db.get_url_by_id(id)
        if not url:
            flash('Сайт не найден', 'danger')
            return redirect(url_for('show_urls'))

        checks = db.get_url_checks(id)
        return render_template('url.html', url=url, checks=checks)

    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        flash('Ошибка базы данных', 'danger')
        return redirect(url_for('index'))


@app.post('/urls/<int:id>/checks')
def check_url(id):
    try:
        url_data = db.get_url_by_id(id)
        if not url_data:
            flash('Сайт не найден', 'danger')
            return redirect(url_for('show_urls'))

        response = requests.get(url_data['name'], timeout=5)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        h1 = soup.h1.text.strip() if soup.h1 else None
        title = soup.title.text.strip() if soup.title else None
        description_tag = soup.find('meta', attrs={'name': 'description'})
        description = description_tag['content'].strip() if description_tag else None

        db.insert_url_check({
            'url_id': id,
            'status_code': response.status_code,
            'h1': h1,
            'title': title,
            'description': description
        })
        flash('Страница успешно проверена', 'success')

    except requests.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        flash('Произошла ошибка при проверке', 'danger')
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        flash('Непредвиденная ошибка', 'danger')

    return redirect(url_for('show_url', id=id))


@app.get('/urls')
def show_urls():
    try:
        urls = db.get_all_urls_with_checks()
        return render_template('urls.html', urls=urls)
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        flash('Ошибка базы данных', 'danger')
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)