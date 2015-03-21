# coding: utf-8
'''
emailer.py

Contains Emailer class to aid with sending emails from templates
'''

import logging

from jinja2 import Environment, PackageLoader
import twilio
import twilio.rest

from nhtg15_webapp import app


class Texter:
    def __init__(self, app):
        self.defaultfrom = app.config['SMS_FROM']

        self.logger = logging.getLogger('nhtg15_webapp.texter')

        self.client = twilio.rest.TwilioRestClient(
            app.config['SMS_ACCOUNT_SID'],
            app.config['SMS_AUTH_TOKEN']
        )

        self.jinjaenv = None

    def get_template(self, template):
        if self.jinjaenv is None:
            self.jinjaenv = Environment(
                loader=PackageLoader(
                    'nhtg15_webapp',
                    'templates'
                )
            )

        return self.jinjaenv.get_template(template)

    def send_template(self, to, template, **kwargs):
        template = self.get_template(template)

        try:
            msgfrom = kwargs['email_from']
        except KeyError:
            msgfrom = self.defaultfrom

        self.send_message(
            to,
            template.render(**kwargs),
        )

    def send_message(self, to, msg):
        try:
            message = self.client.messages.create(
                body=msg,
                to=to,
                from_=self.defaultfrom
            )
        except twilio.TwilioRestException as e:
            self.logger.error('Failed to send message: {}'.format(e))


TEXTER = Texter(app.APP)
