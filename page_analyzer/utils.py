from urllib.parse import urlparse


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
