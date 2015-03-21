#!/usr/bin/env python2
# coding: utf-8

from nhtg15_webapp import database
from nhtg15_webapp import models

database.DB.drop_all()
database.DB.create_all()

database.DB.session.add_all(models.ALLERGENS)
database.DB.session.commit()
