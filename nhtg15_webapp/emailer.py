# coding: utf-8
'''
emailer.py

Contains Emailer class to aid with sending emails from templates
'''

import atexit
import logging
import smtplib

from jinja2 import Environment, PackageLoader
from email.mime.text import MIMEText

from nhtg15_webapp import app


class Emailer:
    def __init__(self, app):
        self.defaultfrom = app.config['EMAIL_FROM']
        self.smtp_host = app.config['SMTP_HOST']

        self.logger = logging.getLogger('nhtg15_webapp.emailer')

        self.smtp = None

        self.jinjaenv = None

        atexit.register(self.shutdown)

    def smtp_open(self):
        try:
            status = self.smtp.noop()[0]
        except:  # smtplib.SMTPServerDisconnected
            status = -1
        return True if status == 250 else False

    def get_template(self, template):
        if self.jinjaenv is None:
            self.jinjaenv = Environment(
                loader=PackageLoader(
                    'nhtg15_webapp',
                    'templates'
                )
            )

        return self.jinjaenv.get_template(template)

    def send_template(self, to, subject, template, **kwargs):
        template = self.get_template(template)

        try:
            msgfrom = kwargs['email_from']
        except KeyError:
            msgfrom = self.defaultfrom

        self.send_text(
            to,
            subject,
            template.render(**kwargs),
            msgfrom
        )

    def send_text(self, to, subject, text, msgfrom=None):
        if msgfrom is None:
            msgfrom = self.defaultfrom

        msg = MIMEText(
            text,
            'plain',
            'utf-8'
        )

        msg['Subject'] = ("[NHTG15] - " + subject)
        msg['From'] = msgfrom
        if isinstance(to, list):
            for email in to:
                msg['To'] = email
        else:
            msg['To'] = to

        self.send_message(msg)

    def send_message(self, msg):
        if self.smtp is None or not self.smtp_open():
            self.smtp = smtplib.SMTP(self.smtp_host)

        try:
            self.smtp.sendmail(msg['From'], msg.get_all('To'), msg.as_string())
        except smtplib.SMTPRecipientsRefused as e:
            self.logger.error(
                (
                    'SMTP server at {0} refused recipients {1} refused for '
                    'message with subject {2}'
                ).format(
                    self.smtp_host,
                    e.recipients,
                    msg['Subject']
                )
            )
        except smtplib.SMTPHeloError as e:
            self.logger.error(
                (
                    'SMTP server at {0} did not reply properly to HELO for '
                    'message with subject {1}'
                ).format(
                    self.smtp_host,
                    msg['Subject']
                )
            )
        except smtplib.SMTPSenderRefused as e:
            self.logger.error(
                (
                    'SMTP server at {0} did not allow sender {1} for '
                    'message with subject {2}'
                ).format(
                    self.smtp_host,
                    msg['From'],
                    msg['Subject']
                )
            )
        except smtplib.SMTPDataError as e:
            self.logger.error(
                (
                    'SMTP server at {0} responded with unexpected error code '
                    '{1} with error message {2} for message with subject {3}'
                ).format(
                    self.smtp_host,
                    e.smtp_code,
                    e.smtp_error,
                    msg['Subject']
                )
            )

    def shutdown(self):
        if self.smtp is not None and self.smtp_open():
            self.smtp.quit()


EMAILER = Emailer(app.APP)
