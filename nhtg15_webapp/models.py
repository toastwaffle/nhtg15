# coding: utf-8

from flask.ext.bcrypt import Bcrypt
from flask.ext.sqlalchemy import SQLAlchemy
import flask

from nhtg15_webapp import app
from nhtg15_webapp import database
from nhtg15_webapp import emailer
from nhtg15_webapp import shortener
from nhtg15_webapp import texter

class Error(Exception):
    pass

class NotPersistedYetError(Error):
    pass

DB = database.DB

user_allergen_link = DB.Table(
    'user_allergen_link',
    DB.Model.metadata,
    DB.Column('user_id',
        DB.Integer,
        DB.ForeignKey('user.id')
    ),
    DB.Column('allergen_id',
        DB.Integer,
        DB.ForeignKey('allergen.id')
    )
)

class Allergen(DB.Model):
    id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
    name = DB.Column(
        DB.String(25),
        nullable=False
    )

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Allergen({}): {}>'.format(self.id, self.name)

    @staticmethod
    def get_by_id(id):
        allergen = Allergen.query.filter(Allergen.id==int(id)).first()

        if not allergen:
            return None

        return allergen

    @staticmethod
    def get_by_name(name):
        allergen = Allergen.query.filter(Allergen.name==name).first()

        if not allergen:
            return None

        return allergen

    @property
    def nicename(self):
        return self.name.title()


ALLERGENS = [
    Allergen('celery'),
    Allergen('gluten'),
    Allergen('nuts'),
    Allergen('crustaceans'),
    Allergen('eggs'),
    Allergen('fish'),
    Allergen('lupin'),
    Allergen('milk'),
    Allergen('molluscs'),
    Allergen('mustard'),
    Allergen('nuts'),
    Allergen('peanuts'),
    Allergen('sesame seeds'),
    Allergen('soya'),
    Allergen('sulphur dioxide'),
]


BCRYPT = Bcrypt(app.APP)


class User(DB.Model):
    id = DB.Column(
        DB.Integer,
        primary_key=True,
        nullable=False
    )
    email = DB.Column(
        DB.String(120),
        unique=True,
        nullable=False
    )
    passhash = DB.Column(
        DB.BINARY(60),
        nullable=False
    )
    firstname = DB.Column(
        DB.String(120),
        nullable=False
    )
    surname = DB.Column(
        DB.String(120),
        nullable=False
    )
    fullname = DB.column_property(firstname + " " + surname)
    phone = DB.Column(
        DB.String(20),
        nullable=False
    )
    send_email_alerts = DB.Column(
        DB.Boolean(),
        nullable=False
    )
    send_sms_alerts = DB.Column(
        DB.Boolean(),
        nullable=False
    )

    allergens = DB.relationship(
        'Allergen',
        secondary=user_allergen_link,
        backref=DB.backref(
            'users',
            lazy='dynamic'
        ),
        lazy='dynamic'
    )

    def __init__(self, email, password, firstname, surname, phone, college, affiliation):
        self.email = email
        self.passhash = bcrypt.generate_password_hash(password)
        self.firstname = firstname
        self.surname = surname
        self.phone = phone
        self.send_email_alerts = False
        self.send_sms_alerts = False

    def __repr__(self):
        return "<User({0}): {1}>".format(self.id, self.fullname)

    def checkPassword(self, candidate):
        return BCRYPT.check_password_hash(self.passhash, candidate)

    def setPassword(self, password):
        self.passhash = BCRYPT.generate_password_hash(password)

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    @staticmethod
    def get_by_id(id):
        user = User.query.filter(User.id==int(id)).first()

        if not user:
            return None

        return user

    @staticmethod
    def get_by_email(email):
        user = User.query.filter(User.email==email).first()

        if not user:
            return None

        return user

    def send_alert(self, alert):
        if self.send_email_alerts:
            emailer.EMAILER.send_template(
                self.email,
                'Allergy Alert: {} in {} {}'.format(
                    alert.allergen.name.title(),
                    alert.brand,
                    alert.product
                ),
                'allergy_alert.email',
                alert=alert,
                user=self
            )

        if self.send_sms_alerts:
            texter.TEXTER.send_template(
                self.phone,
                'allergy_alert.sms',
                alert=alert
            )


class Alert(DB.Model):
    id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
    brand = DB.Column(
        DB.String(50),
        nullable=False
    )
    product = DB.Column(
        DB.String(50),
        nullable=False
    )
    location = DB.Column(
        DB.String(50),
        nullable=False
    )
    datetime = DB.Column(
        DB.DateTime(),
        nullable=False
    )
    long_url = DB.Column(
        DB.String(100),
        nullable=True
    )
    short_url = DB.Column(
        DB.String(100),
        nullable=True
    )

    allergen_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('allergen.id'),
        nullable=False
    )
    allergen = DB.relationship(
        'Allergen',
        backref=DB.backref(
            'alerts',
            lazy='dynamic',
            order_by='Alert.datetime'
        ),
        foreign_keys=[allergen_id]
    )

    def __init__(self, brand, product, location, datetime, allergen):
        self.brand = brand
        self.product = product
        self.location = location
        self.datetime = datetime

        if hasattr(allergen, 'id'):
            self.allergen_id = allergen.id
        else:
            self.allergen_id = allergen

    def __repr__(self):
        return '<Alert({}): {}/{}>'.format(self.id, self.brand, self.product)

    @staticmethod
    def get_by_id(id):
        alert = Alert.query.filter(Alert.id==int(id)).first()

        if not alert:
            return None

        return alert

    def update_urls(self):
        if self.id is None:
            raise NotPersistedYetError('{} has not been persisted'.format(self))

        self.long_url = '{}/alert/{}/'.format(
            app.APP.config['SITE_URL'],
            self.id
        )
        self.short_url = shortener.shorten(self.long_url)

        DB.session.commit()

    def send_alerts(self):
        for user in self.allergen.users:
            user.send_alert(self)
