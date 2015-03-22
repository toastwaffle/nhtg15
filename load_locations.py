#!/usr/bin/env python2
# coding: utf-8

import os
import csv

from nhtg15_webapp import database
from nhtg15_webapp import models

with open('locations/counties.csv') as fh:
    reader = csv.reader(fh)

    count = 0

    for row in reader:
        database.DB.session.add(models.Area(row[0], 'COUNTY', row[1]))

        count += 1

        if count > 100:
            database.DB.session.commit()
            count = 0

    database.DB.session.commit()

with open('locations/districts.csv') as fh:
    reader = csv.reader(fh)

    count = 0

    for row in reader:
        database.DB.session.add(models.Area(row[0], 'DISTRICT', row[1]))

        count += 1

        if count > 100:
            database.DB.session.commit()
            count = 0

    database.DB.session.commit()

with open('locations/wards.csv') as fh:
    reader = csv.reader(fh)

    count = 0

    for row in reader:
        database.DB.session.add(models.Area(row[0], 'WARD', row[1]))

        count += 1

        if count > 100:
            database.DB.session.commit()
            count = 0

    database.DB.session.commit()

for filename in os.listdir('locations/postcodes'):
    filepath = os.path.join('locations/postcodes',filename)

    with open(filepath) as fh:
        reader = csv.reader(fh)

        count = 0

        for row in reader:
            location = models.Location(row[0], row[2], row[3])

            ward = models.Area.get_by_code(row[9])

            location.area_id = ward.id

            database.DB.session.add(location)

            district = models.Area.get_by_code(row[8])

            ward.parent_id = district.id

            country = models.Area.get_by_code(row[4])

            if not country:
                country = models.Area(row[4], 'COUNTRY', row[4])
                database.DB.session.add(country)
                database.DB.session.commit()

            if row[7] == '':
                district.parent_id = country.id
            else:
                county = models.Area.get_by_code(row[7])

                district.parent_id = county.id
                county.parent_id = country.id

            count += 1

            if count > 100:
                database.DB.session.commit()
                count = 0

        database.DB.session.commit()

    os.remove(filepath)
