#!/usr/bin/env python2

import sys

import bs4
import feedparser
import gflags
import pytz
import re
from dateutil import parser

from nhtg15_webapp import database
from nhtg15_webapp import models

FLAGS = gflags.FLAGS

gflags.DEFINE_string('url',
                     'http://www.food.gov.uk/test-foodalerts-rss',
                     'URL to fetch feed from')

def main(argv):
    try:
        argv = FLAGS(argv)  # parse flags
    except gflags.FlagsError, e:
        print '{0}\nUsage: {1} ARGS\n{2}'.format(e, sys.argv[0], FLAGS)
        sys.exit(1)

    feed = feedparser.parse(FLAGS.url)

    r = re.compile('^(.*?): (.*?)$')

    newest_alert = models.Alert.query.order_by(
        models.Alert.datetime.desc()
    ).first()

    if newest_alert:
        newest_alert_date = newest_alert.datetime.replace(tzinfo=pytz.utc)
    else:
        newest_alert_date = None

    for entry in feed['entries']:
        alert_date = parser.parse(entry['published']).astimezone(pytz.utc)

        print alert_date

        if newest_alert_date is not None and alert_date <= newest_alert_date:
            continue

        soup = bs4.BeautifulSoup(entry['summary'])

        dataitem = {}

        for field in soup.findAll('div', {'class': 'field__item'}):
            matches = r.match(field.get_text().strip()).groups()
            dataitem[matches[0].lower()] = matches[1]

        alert = models.Alert(
            dataitem['brand'],
            dataitem['product'],
            dataitem['location'],
            alert_date,
            models.Allergen.get_by_name(dataitem['allergen'].lower())
        )

        database.DB.session.add(alert)
        database.DB.session.commit()

        alert.update_urls()

        alert.send_alerts()

if __name__ == '__main__':
    main(sys.argv)
