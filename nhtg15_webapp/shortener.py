import logging

import requests

from nhtg15_webapp import app

def shorten(url):
    try:
        r = requests.get(
            'https://api-ssl.bitly.com/v3/shorten',
            params={
                'access_token': app.APP.config['BITLY_ACCESS_TOKEN'],
                'longUrl': url,
                'domain': 'j.mp'
            }
        )

        return r.json()['data']['url']
    except Exception as e:
        logging.getLogger('nhtg15_webapp.shortener').error(e)
        return url
