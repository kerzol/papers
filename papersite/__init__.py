import papersite.config
from flask import Flask
from libs.flask_simple_captcha.flask_simple_captcha import CAPTCHA
CAPTCHA = CAPTCHA(config=papersite.config.CAPTCHA_CONFIG)

app = Flask(__name__,
            static_folder='../static',
            template_folder='../templates')
app = CAPTCHA.init_app(app)
app.config.update(papersite.config.appc)

import papersite.db
import papersite.user
import papersite.main_list_of_papers
import papersite.onepaper
import papersite.catalog
import papersite.pseudostatic
import papersite.dump
