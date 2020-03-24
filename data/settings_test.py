# @formatter:off
from .settings import *
# @formatter:on

DEBUG = False

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'alice.middleware.SignatureRejectionMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'sso.middleware.saml2.SSOAuthenticationMiddleware',
    'sso.middleware.permission_denied.Metadata403',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.RequestLoggerMiddleware',
]

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}

HAWK_RECEIVER_CREDENTIALS = {
    'activity-stream-id': {
        'key': 'activity-stream-key',
        'scopes': (HawkScope.activity_stream, ),
    },
    'data-flow-id': {
        'key': 'data-flow-key',
        'scopes': (HawkScope.data_flow_api, ),
    },
    'mulit-scope-id': {
        'key': 'mulit-scope-key',
        'scopes': (HawkScope.activity_stream, HawkScope.data_flow_api, ),
    },
    'no-scope-id': {
        'key': 'no-scope-key',
        'scopes': (),
    },
}