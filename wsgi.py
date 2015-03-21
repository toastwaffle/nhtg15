# coding: utf-8
import site, os, sys
site.addsitedir('/srv/http_nhtg15/lib/python2.7/site-packages/')
sys.path.append(os.path.realpath(__file__).replace('/wsgi.py',''))

from flask.ext import login

from nhtg15_webapp import app
from nhtg15_webapp import models
from nhtg15_webapp import views

def application(req_environ, start_response):
    login_manager = login.LoginManager()

    login_manager.init_app(app.APP)

    @login_manager.user_loader
    def load_user(userid):
        return models.User.get_by_id(userid)

    app.APP.register_blueprint(views.VIEWS)

    return app(req_environ, start_response)
