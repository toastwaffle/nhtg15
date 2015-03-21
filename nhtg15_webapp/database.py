# coding: utf-8

from flask.ext.sqlalchemy import SQLAlchemy

import app

DB = SQLAlchemy(app.APP)
