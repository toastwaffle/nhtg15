# coding: utf-8

import random

from flask.ext.bcrypt import Bcrypt
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext import whooshalchemy
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

alert_area_link = DB.Table(
    'alert_area_link',
    DB.Model.metadata,
    DB.Column('alert_id',
        DB.Integer,
        DB.ForeignKey('alert.id')
    ),
    DB.Column('area_id',
        DB.Integer,
        DB.ForeignKey('area.id')
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
    Allergen('almonds'),
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
    fullname = DB.column_property(firstname + ' ' + surname)
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
    email_verification_key = DB.Column(
        DB.String(6),
        nullable=True
    )
    sms_verification_key = DB.Column(
        DB.String(6),
        nullable=True
    )
    email_verified = DB.Column(
        DB.Boolean(),
        nullable=False
    )
    sms_verified = DB.Column(
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

    location_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('location.id'),
        nullable=False
    )
    location = DB.relationship(
        'Location',
        backref=DB.backref(
            'users',
            lazy='dynamic'
        ),
        foreign_keys=[location_id]
    )

    def __init__(self, email, password, firstname, surname, phone, location):
        self.email = email
        self.set_password(password)
        self.firstname = firstname
        self.surname = surname
        self.phone = phone
        self.send_email_alerts = False
        self.send_sms_alerts = False
        self.email_verification_key = str(random.randint(100000, 999999))
        self.sms_verification_key = str(random.randint(100000, 999999))
        self.email_verified = False
        self.sms_verified = False

        if hasattr(location, 'id'):
            self.location_id = location.id
        else:
            self.location_id = location

    def __repr__(self):
        return "<User({0}): {1}>".format(self.id, self.fullname)

    def check_password(self, candidate):
        return BCRYPT.check_password_hash(self.passhash, candidate)

    def set_password(self, password):
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
        if alert.areas:
            area = self.location.area
            area_ids = [a.id for a in alert.areas.all()]
            print area_ids
            print repr(area)

            while area is not None and area.id not in area_ids:
                print repr(area)
                area = area.parent

            if area is None:
                return

        if self.email_verified and self.send_email_alerts:
            emailer.EMAILER.send_template(
                self.email,
                '{} in {} {}'.format(
                    alert.allergen.name.title(),
                    alert.brand,
                    alert.product
                ),
                'allergy_alert.email',
                alert=alert,
                user=self
            )

        if self.sms_verified and self.send_sms_alerts:
            texter.TEXTER.send_template(
                self.phone,
                'allergy_alert.sms',
                alert=alert
            )

    def send_email_verification(self):
        emailer.EMAILER.send_template(
            self.email,
            'Verify Email Address',
            'verify.email',
            user=self
        )

    def send_sms_verification(self):
        texter.TEXTER.send_template(
            self.phone,
            'verify.sms',
            user=self
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

    areas = DB.relationship(
        'Area',
        secondary=alert_area_link,
        backref=DB.backref(
            'alerts',
            lazy='dynamic'
        ),
        lazy='dynamic'
    )

    def __init__(self, brand, product, location, datetime, allergen, url):
        self.brand = brand
        self.product = product
        self.location = location
        self.datetime = datetime
        self.long_url = url
        self.short_url = shortener.shorten(url)

        if hasattr(allergen, 'id'):
            self.allergen_id = allergen.id
        else:
            self.allergen_id = allergen

        area_query = Area.query.whoosh_search(location)

        for area_type in ['COUNTRY', 'COUNTY', 'DISTRICT', 'WARD']:
            areas = area_query.filter(Area.area_type == area_type).all()

            if areas:
                for area in areas:
                    self.areas.append(area)

                break

    def __repr__(self):
        return '<Alert({}): {}/{}>'.format(self.id, self.brand, self.product)

    @staticmethod
    def get_by_id(id):
        alert = Alert.query.filter(Alert.id==int(id)).first()

        if not alert:
            return None

        return alert

    def send_alerts(self):
        for user in self.allergen.users:
            user.send_alert(self)


class Location(DB.Model):
    id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
    postcode_outward = DB.Column(
        DB.String(4),
        nullable=False
    )
    postcode_inward = DB.Column(
        DB.String(3),
        nullable=False
    )
    postcode = DB.column_property(postcode_outward + ' ' + postcode_inward)
    eastings = DB.Column(
        DB.Integer(),
        nullable=False
    )
    northings = DB.Column(
        DB.Integer(),
        nullable=False
    )

    area_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('area.id'),
        nullable=True
    )
    area = DB.relationship(
        'Area',
        backref=DB.backref(
            'locations',
            lazy='dynamic'
        ),
        foreign_keys=[area_id]
    )

    def __init__(self, postcode, eastings, northings):
        self.postcode_inward = postcode[-3:]
        self.postcode_outward = postcode[:-3].strip()
        self.eastings = eastings
        self.northings = northings

    def __repr__(self):
        return '<Location({}): {}>'.format(self.id, self.postcode)


    @staticmethod
    def get_by_id(id):
        location = Location.query.filter(Location.id==int(id)).first()

        if not location:
            return None

        return location

    @staticmethod
    def get_by_postcode(postcode):
        location = Location.query.filter(
            Location.postcode_outward == postcode[:-3].strip()
        ).filter(
            Location.postcode_inward == postcode[-3:]
        ).first()

        if not location:
            return None

        return location


class Area(DB.Model):
    __searchable__ = ['name']

    id = DB.Column(
        DB.Integer(),
        primary_key=True,
        nullable=False
    )
    code = DB.Column(
        DB.String(9),
        nullable=False
    )
    name = DB.Column(
        DB.String(50),
        nullable=False
    )
    area_type = DB.Column(
        DB.Enum(
            'COUNTRY',
            'COUNTY',
            'DISTRICT',
            'WARD'
        ),
        nullable=False
    )

    parent_id = DB.Column(
        DB.Integer,
        DB.ForeignKey('area.id'),
        nullable=True
    )
    parent = DB.relationship(
        'Area',
        backref=DB.backref(
            'children',
            lazy='dynamic'
        ),
        foreign_keys=[parent_id],
        remote_side=[id]
    )

    def __init__(self, name, area_type, code=None):
        self.code = code
        self.name = name
        self.area_type = area_type

    def __repr__(self):
        return '<Area({}): {}{}>'.format(
            self.id,
            '{}/'.format(self.code) if self.code is not None else '',
            self.name
        )

    @staticmethod
    def get_by_id(id):
        area = Area.query.filter(Area.id==int(id)).first()

        if not area:
            return None

        return area

    @staticmethod
    def get_by_code(code):
        area = Area.query.filter(Area.code==code).first()

        if not area:
            return None

        return area

    @staticmethod
    def get_by_name(name):
        area = Area.query.filter(Area.name==name).first()

        if not area:
            return None

        return area

    def get_locations():
        for location in self.locations:
            yield location

        for child in self.children:
            for location in child.get_locations:
                yield location


whooshalchemy.whoosh_index(app.APP, Area)
