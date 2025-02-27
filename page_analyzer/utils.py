from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup


def normalize_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}".lower().rstrip('/')


def is_valid_url(url):
    errors = {}

    if not url:
        errors['url'] = 'URL обязателен'
        status_code = 400
    elif len(url) > 255:
        errors['url'] = 'URL превышает 255 символов'
        status_code = 400
    else:
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]) or parsed.scheme not in ['http', 'https']:
                errors['url'] = 'Некорректный URL'
                status_code = 422
        except ValueError:
            errors['url'] = 'Некорректный URL'
            status_code = 422

    return errors, status_code


def get_page_data(url):

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        h1 = soup.h1.text.strip() if soup.h1 else ''
        title = soup.title.text.strip() if soup.title else ''
        description_tag = soup.find('meta', attrs={'name': 'description'})
        description = description_tag['content'].strip() if description_tag else ''

        h1 = h1[:255]
        title = title[:255]
        description = description[:255]

        return {
            'h1': h1,
            'title': title,
            'description': description,
            'status_code': response.status_code
        }

    except requests.RequestException:
        return None
