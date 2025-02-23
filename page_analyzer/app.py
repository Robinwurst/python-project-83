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
import psycopg2
from urllib.parse import urlparse
import logging
import requests
from bs4 import BeautifulSoup
from page_analyzer.database import db

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates")
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.jinja_env.filters['truncate'] = lambda s, length: (s[:length - 3] + '...') if s and len(s) > length else s


def get_db_connection():
    """Создает и возвращает соединение с базой данных."""
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


def is_valid_url(url):
    """Проверяет, является ли URL валидным."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


@app.route('/')
def index():
    """Главная страница."""
    return render_template('index.html')


@app.route('/add_url', methods=['POST'])
def add_url():
    """Добавляет новый URL в базу данных."""
    url = request.form.get('url', '').strip()
    logger.debug(f"Получен URL: {url}")

    # Проверка валидности URL
    if not url or len(url) > 255 or not is_valid_url(url):
        flash('Некорректный URL', 'danger')
        logger.debug("URL не прошел валидацию")
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Попытка добавить URL в базу
        cur.execute("""
            INSERT INTO urls (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING
            RETURNING id
        """, (url,))
        url_id = cur.fetchone()
        conn.commit()

        if url_id:
            # Если URL добавлен
            flash('Страница успешно добавлена', 'success')
            logger.debug(f"URL добавлен, ID: {url_id[0]}")
            return redirect(url_for('show_url', id=url_id[0]))
        else:
            # Если URL уже существует
            cur.execute("SELECT id FROM urls WHERE name = %s", (url,))
            existing_url_id = cur.fetchone()[0]
            flash('Страница уже существует', 'info')
            logger.debug(f"URL уже существует, ID: {existing_url_id}")
            return redirect(url_for('show_url', id=existing_url_id))
    except Exception as e:
        # Обработка ошибок
        conn.rollback()
        flash('Ошибка при добавлении URL', 'danger')
        logger.error(f"Ошибка при добавлении URL: {str(e)}")
    finally:
        # Закрытие соединения с базой
        cur.close()
        conn.close()

    return redirect(url_for('index'))


@app.get('/urls/<int:id>')
def show_url(id):
    """Отображает страницу с информацией о URL."""
    url = db.get_url_by_id(id)
    if not url:
        flash('Сайт не найден', 'danger')
        return redirect(url_for('show_urls'))

    checks = db.get_url_checks(id)
    return render_template('url.html', url=url, checks=checks)


@app.post('/urls/<int:id>/checks')
def check_url(id):
    """Проверяет URL и добавляет результат в базу."""
    url_data = db.get_url_by_id(id)
    if not url_data:
        flash('Сайт не найден', 'danger')
        return redirect(url_for('show_urls'))

    try:
        # Запрос к сайту
        response = requests.get(url_data['name'], timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Извлечение данных
        h1 = soup.h1.text.strip() if soup.h1 else None
        title = soup.title.text.strip() if soup.title else None
        description_tag = soup.find('meta', attrs={'name': 'description'})
        description = description_tag['content'].strip() if description_tag else None

        # Добавление проверки в базу
        db.create_url_check({
            'url_id': id,
            'status_code': response.status_code,
            'h1': h1,
            'title': title,
            'description': description
        })
        flash('Страница успешно проверена', 'success')
    except requests.exceptions.RequestException as e:
        # Обработка ошибок запроса
        flash('Произошла ошибка при проверке', 'danger')
        logger.error(f"Ошибка при проверке URL: {str(e)}")
    except Exception as e:
        # Обработка других ошибок
        flash('Непредвиденная ошибка', 'danger')
        logger.error(f"Непредвиденная ошибка: {str(e)}")

    return redirect(url_for('show_url', id=id))


@app.get('/urls')
def show_urls():
    """Отображает список всех URL."""
    urls = db.get_urls()
    return render_template('urls.html', urls=urls)


if __name__ == '__main__':
    app.run(debug=True)