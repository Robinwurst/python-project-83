from flask import Flask, render_template, request, redirect, url_for, flash
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
from logger import logger
import requests
from bs4 import BeautifulSoup
from utils import normalize_url, is_valid_url
from page_analyzer.database import db

load_dotenv()


app = Flask(__name__, template_folder="templates")
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')





@app.route('/')
def index():
    return render_template('index.html')


@app.post('/urls')
def add_url():
    raw_url = request.form.get('url', '').strip()

    # Валидация URL
    if not raw_url:
        flash('URL обязателен', 'danger')
        return render_template('index.html'), 400

    if len(raw_url) > 255:
        flash('URL превышает 255 символов', 'danger')
        return render_template('index.html'), 400

    parsed = urlparse(raw_url)
    if not is_valid_url(raw_url):
        flash('Некорректный URL', 'danger')
        return render_template('index.html'), 422




    # Нормализация и проверка дубликатов
    normalized_url = normalize_url(raw_url)

    try:
        existing_id = db.get_url_id_by_name(normalized_url)
        if existing_id:
            flash('Страница уже существует', 'info')
            return redirect(url_for('show_url', id=existing_id))

        new_id = db.insert_url(normalized_url)
        flash('Страница успешно добавлена', 'success')
        return redirect(url_for('show_url', id=new_id))

    except Exception as e:
        logger.error(f"Ошибка базы данных: {str(e)}")
        flash('Ошибка при обработке запроса', 'danger')
        return render_template('index.html'), 500


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
        flash('Непредвиденная ошибка', 'danger')
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
        description = (
            description_tag['content'].strip()
            if description_tag
            else None
        )

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
