
DEBUG = True
TEMPLATE_DEBUG = DEBUG

APPEND_SLASH = True

LOGIN_URL = '/accounts/signin/'
LOGOUT_URL = '/accounts/signout/'

DATE_FORMAT = 'F j, Y'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    #'django.contrib.csrf.middleware.CsrfMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django_authopenid.middleware.OpenIDMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django_authopenid.context_processors.authopenid',
    'utils.context_processors.current_site',
    'issues.context_processors.latest_issue',
)

FILE_UPLOAD_HANDLERS = (
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
)

ROOT_URLCONF = 'imprint.urls'

COMMENTS_APP = 'imprint.nested_comments'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'imprint.nested_comments',
    'django.contrib.comments',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django_authopenid',
    'django_extensions',
    'imprint.advertising',
    'imprint.content',
    'imprint.issues',
    'imprint.people',
    'imprint.utils',
    'registration',
)

from local_settings import *
