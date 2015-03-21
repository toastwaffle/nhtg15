# coding: utf-8
import flask

APP = flask.Flask('nhtg15_webapp')

APP.config.from_pyfile('config.py')
