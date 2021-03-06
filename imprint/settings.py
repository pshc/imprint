
DEBUG = True
TEMPLATE_DEBUG = DEBUG

APPEND_SLASH = True

LOGIN_URL = '/accounts/signin/'
LOGOUT_URL = '/accounts/signout/'

DATE_FORMAT = 'F j, Y'

CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    #'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'utils.middleware.Firefox2HTML5Workaround',
    #'django.contrib.csrf.middleware.CsrfMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'utils.middleware.ThreadLocals',
    'django.middleware.doc.XViewMiddleware',
    'django_authopenid.middleware.OpenIDMiddleware',
    #'django.middleware.cache.FetchFromCacheMiddleware',
    'django.contrib.redirects.middleware.RedirectFallbackMiddleware',
    'kiwi.middleware.KiwiNameFormatMiddleware',
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
    'kiwi.context_processors.kiwi_info',
)

FILE_UPLOAD_HANDLERS = (
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
)
DEFAULT_FILE_STORAGE = 'utils.FileSystemStorage'

ROOT_URLCONF = 'imprint.urls'

COMMENTS_APP = 'imprint.nested_comments'
COMMENTS_HIDE_REMOVED = False

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'imprint.nested_comments',
    'django.contrib.comments',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.redirects',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django_extensions',
    'imprint.advertising',
    'imprint.archive',
    'imprint.content',
    'imprint.issues',
    'imprint.kiwi',
    'imprint.people',
    'imprint.static',
    'imprint.utils',
    'imprint.feds',
    'imprint.marchmadness',
)

from local_settings import *
