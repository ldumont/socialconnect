# Django settings for yasn project.
import os, sys

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS


DATABASE_ENGINE = ''           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = ''             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Zurich'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'


SITE_ID = 2
USE_I18N = True
ugettext = lambda s: s
LANGUAGES = (
  ('en', ugettext('English')),
)

MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'media/')
ADMIN_MEDIA_ROOT = os.path.join(os.path.dirname(__file__), '../admin_media/')
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/admin_media/'


# Make this unique, and don't share it with anybody.
SECRET_KEY = 'r#af#^o$&$x(*%348-tx&r)@&+ttufy%q--gne-opnup@*pw1_'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.app_directories.load_template_source',
    'django.template.loaders.filesystem.load_template_source',
#   'django.template.loaders.eggs.load_template_source',
)



MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    #"django.core.context_processors.i18n",
    #"django.core.context_processors.debug",
    "django.core.context_processors.media",
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(os.path.dirname(__file__), "templates"),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django_extensions',    
    'accounts',
    'socialconnect',
    'yasn',
)

CACHE_BACKEND = 'dummy:///'

AUTH_PROFILE_MODULE = 'accounts.UserProfile'

## YASN settings ##
LOGIN_URL = '/login/'

EMAIL_HOST = 'localhost'
EMAIL_PORT = 25

# email sender for password recovering
EMAIL_SENDER = ''

# template id for "writing a story"
TEMPLATE_STORY_ID = ''
# template id for "commenting on a story from someone that does not have an account on Facebook"
TEMPLATE_COMMENT_AUTHOR_ID = ''
# template id for "commenting on a story from someone that has an account on Facebook"
TEMPLATE_COMMENT_TARGET_ID = ''

# Load the local settings
try:
    from settings_local import *
except ImportError:
    pass
