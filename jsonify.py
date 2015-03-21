#!/usr/bin/env python2

import sys

import bs4
import feedparser
import gflags
import json
import re

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

    data = []

    for entry in feed['entries']:
        soup = bs4.BeautifulSoup(entry['summary'])

        dataitem = {}

        for field in soup.findAll('div', {'class': 'field__item'}):
            matches = r.match(field.get_text().strip()).groups()
            dataitem[matches[0].lower()] = matches[1]

        data.append(dataitem)

    print json.dumps(data)

if __name__ == '__main__':
    main(sys.argv)
