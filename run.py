#! /usr/bin/env python2
# coding: utf-8

from flask.ext import login

from nhtg15_webapp import app
from nhtg15_webapp import models
from nhtg15_webapp import views

if __name__ == '__main__':
    login_manager = login.LoginManager()

    login_manager.init_app(app.APP)

    @login_manager.user_loader
    def load_user(userid):
        return models.User.get_by_id(userid)

    app.APP.register_blueprint(views.VIEWS)
    app.APP.run()
