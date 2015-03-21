import flask

VIEWS = flask.Blueprint('views')

@VIEWS.route('/')
