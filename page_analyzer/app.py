from flask import Flask, render_template, request, redirect, url_for, flash
import os
from dotenv import load_dotenv
from logger import logger
from utils import normalize_url, is_valid_url, get_page_data
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
    validation_errors, status_code = is_valid_url(raw_url)
    if validation_errors:
        for field, message in validation_errors.items():
            flash(message, 'danger')
        return render_template('index.html'), status_code

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

        # Получаем данные со страницы
        page_data = get_page_data(url_data['name'])
        if page_data:
            # Сохраняем данные в БД
            db.insert_url_check({
                'url_id': id,
                'status_code': page_data['status_code'],
                'h1': page_data['h1'],
                'title': page_data['title'],
                'description': page_data['description']
            })
            flash('Страница успешно проверена', 'success')
        else:
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
