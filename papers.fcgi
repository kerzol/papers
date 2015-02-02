#!/usr/bin/python3

# pip install flup6 
from flup.server.fcgi import WSGIServer
import logging
from papersite import app

if not app.debug:
    from logging import FileHandler
    file_handler = FileHandler('./logs/flask.log')
    file_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)

if __name__ == '__main__':
    WSGIServer(app).run()

