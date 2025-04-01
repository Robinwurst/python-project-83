from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from .messages import URL_REQUIRED, URL_TOO_LONG, URL_INVALID


def normalize_url(url):
    url = url.strip().lower()
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def validate_url(url):
    if not url or not url.strip():
        return URL_REQUIRED, 400

    if len(url) > 255:
        return URL_TOO_LONG, 400

    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return URL_INVALID, 422
        if parsed.scheme not in ('http', 'https'):
            return URL_INVALID, 422
    except ValueError:
        return URL_INVALID, 422

    return None, 200


def get_page_data(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        h1 = soup.h1.text.strip() if soup.h1 else ''
        title = soup.title.text.strip() if soup.title else ''
        description_tag = soup.find('meta', attrs={'name': 'description'})
        description = description_tag['content'].strip() \
            if description_tag else ''

        return {
            'h1': h1[:255],
            'title': title[:255],
            'description': description[:255],
            'status_code': response.status_code
        }

    except requests.RequestException:
        return None
