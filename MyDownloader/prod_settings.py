from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent
# Обязательно нужно поменять секретный код, просто поменяв символы. Чтобы не взломали хуцкеры :/
SECRET_KEY = 'ksdjfaksdj0-q320983234ddsd!%nk_**_+xz9+p)o#^q7w1$(fhw458^frl9b*ghr*9x'

DEBUG = False
ALLOWED_HOSTS = ["127.0.0.1"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # psycopg2 - драйвер для работы бд (библиотека)
        'NAME': 'db',
        'USER': 'ivan',
        'PASSWORD': '1234',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

STATIC_DIR = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [STATIC_DIR]
STATIC_ROOT = BASE_DIR / "static"