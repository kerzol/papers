import logging
from papersite import app

if not app.debug:
    from logging import FileHandler
    file_handler = FileHandler('./logs/flask.log')
    file_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)

logger = logging.getLogger('werkzeug')
handler = logging.FileHandler('./logs/access.log')
logger.addHandler(handler)

app.config.update(SERVER_NAME='localhost:5000')
app.run(host='0.0.0.0', debug=True)
