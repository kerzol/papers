from datetime import timedelta

DATABASE = 'db/papers.db'
SALT1=b"aiur afaf 34#%3 RANDOM SALT? f44ih ?A?233 3###$ fa 95?"
SALT2='FIXME CHANGME TO REALLY RADOMM STRING'


# Load default config and override config from an environment variable
appc = dict(
    DEBUG=True,
    SECRET_KEY=SALT2,
    PERMANENT_SESSION_LIFETIME=timedelta(days=999),
    UPLOAD_FOLDER = 'static/memory/pdfs',
    PREVIEW_FOLDER = 'static/memory/previews',
)

