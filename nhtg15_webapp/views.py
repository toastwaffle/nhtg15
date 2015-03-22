import random

import flask
from flask.ext.login import current_user, login_user, logout_user, login_required

from nhtg15_webapp import database
from nhtg15_webapp import models

VIEWS = flask.Blueprint('views', __name__)

@VIEWS.route('/')
@VIEWS.route('/<int:page>/')
def index(page=1):
    if current_user.is_anonymous():
        return flask.render_template("home.html", form={})
    else:
        alerts = models.Alert.query.paginate(page, 2)
        return flask.render_template("dashboard.html",
                                     alerts=alerts,
                                     allergens=models.Allergen.query.all())

@VIEWS.route('/login/', methods=['POST'])
def login():
    user = models.User.get_by_email(flask.request.form['email'])

    if not user:
        flask.flash(u'No such user', 'error')
    elif not user.check_password(flask.request.form['password']):
        flask.flash(u'Incorrect password', 'error')
    else:
        login_user(
            user,
            remember=(
                'remember-me' in flask.request.form and
                flask.request.form['remember-me'] == 'yes'
            )
        )
        flask.flash(u'Logged in successfully.', 'success')

    return flask.redirect(flask.url_for('.index'))

@VIEWS.route('/register/', methods=['POST'])
def register():
    if models.User.get_by_email(flask.request.form['email']) is not None:
        flask.flash(u'Email in use', 'error')
        return flask.redirect(flask.url_for('.index'))

    valid = True
    flashes = []

    if (
        'firstname' not in flask.request.form or
        flask.request.form['firstname'] == ''
    ):
        flashes.append(u'First Name cannot be blank')
        valid = False

    if (
        'surname' not in flask.request.form or
        flask.request.form['surname'] == ''
    ):
        flashes.append(u'Surname cannot be blank')
        valid = False

    if (
        'email' not in flask.request.form or
        flask.request.form['email'] == ''
    ):
        flashes.append(u'Email cannot be blank')
        valid = False

    if (
        'password' not in flask.request.form or
        flask.request.form['password'] == ''
    ):
        flashes.append(u'Password cannot be blank')
        valid = False
    elif len(flask.request.form['password']) < 8:
        flashes.append(u'Password must be at least 8 characters long')
        valid = False
    elif (
        'confirm' not in flask.request.form or
        flask.request.form['password'] != flask.request.form['confirm']
    ):
        flashes.append(u'Passwords do not match')
        valid = False

    if (
        'phone' not in flask.request.form or
        flask.request.form['phone'] == ''
    ):
        flashes.append(u'Phone cannot be blank')
        valid = False

    if (
        'postcode' not in flask.request.form or
        flask.request.form['postcode'] == ''
    ):
        flashes.append(u'Postcode cannot be blank')
        valid = False

    location = models.Location.get_by_postcode(flask.request.form['postcode'])

    if not location:
        flashes.append(u'Postcode not recognised')
        valid = False

    if not valid:
        flask.flash(
            (
                u'There were errors in your provided details. Please fix '
                u'these and try again'
            ),
            'error'
        )
        for msg in flashes:
            flask.flash(msg, 'warning')

        return flask.render_template(
            'home.html',
            form=flask.request.form
        )

    user = models.User(
        flask.request.form['email'],
        flask.request.form['password'],
        flask.request.form['firstname'],
        flask.request.form['surname'],
        flask.request.form['phone'],
        location
    )

    database.DB.session.add(user)
    database.DB.session.commit()

    user.send_email_verification()
    user.send_sms_verification()

    flask.flash(u'Your user account has been registered', 'success')

    login_user(
        user,
        remember=(
            'remember-me' in flask.request.form and
            flask.request.form['remember-me'] == 'yes'
        )
    )

    return flask.redirect(flask.url_for('.index'))

@VIEWS.route('/logout/')
@login_required
def logout():
    logout_user()

    return flask.redirect(flask.url_for('.index'))

@VIEWS.route('/updatedetails/', methods=['POST'])
@login_required
def update_details():
    valid = True
    flashes = []

    if (
        flask.request.form['email'] != current_user.email and
        models.User.get_by_email(flask.request.form['email']) is not None
    ):
        flashes.append(u'That email address is already in use. ')
        valid = False

    if (
        'oldpassword' in flask.request.form and
        flask.request.form['oldpassword'] != ''
    ):
        if not current_user.check_password(flask.request.form['oldpassword']):
            flashes.append(u'Current password is incorrect')
            valid = False

        if (
            'password' not in flask.request.form or
            'confirm' not in flask.request.form or
            flask.request.form['password'] == '' or
            flask.request.form['password'] != flask.request.form['confirm']
        ):
            flashes.append(u'New passwords do not match')
            valid = False

        if len(flask.request.form['password']) < 8:
            flashes.append(u'Password must be at least 8 characters long')
            valid = False

    if (
        'firstname' not in flask.request.form or
        flask.request.form['firstname'] == ''
    ):
        flashes.append(u'First Name cannot be blank')
        valid = False

    if (
        'surname' not in flask.request.form or
        flask.request.form['surname'] == ''
    ):
        flashes.append(u'Surname cannot be blank')
        valid = False

    if (
        'email' not in flask.request.form or
        flask.request.form['email'] == ''
    ):
        flashes.append(u'Email cannot be blank')
        valid = False

    if (
        'phone' not in flask.request.form or
        flask.request.form['phone'] == ''
    ):
        flashes.append(u'Phone cannot be blank')
        valid = False

    if (
        'postcode' not in flask.request.form or
        flask.request.form['postcode'] == ''
    ):
        flashes.append(u'Postcode cannot be blank')
        valid = False

    location = models.Location.get_by_postcode(flask.request.form['postcode'])

    if not location:
        flashes.append(u'Postcode not recognised')
        valid = False

    if not valid:
        flash(
            (
                u'There were errors in your provided details. Please fix '
                u'these and try again'
            ),
            'error'
        )
        for msg in flashes:
            flash(msg, 'warning')
    else:
        current_user.firstname = flask.request.form['firstname']
        current_user.surname = flask.request.form['surname']
        current_user.location_id = location.id

        if flask.request.form['email'] != current_user.email:
            current_user.email = flask.request.form['email']
            current_user.email_verified = False
            current_user.email_verification_key = str(random.randint(100000, 999999))
            current_user.send_email_verification()

        if flask.request.form['phone'] != current_user.phone:
            current_user.phone = flask.request.form['phone']
            current_user.sms_verified = False
            current_user.sms_verification_key = str(random.randint(100000, 999999))
            current_user.send_sms_verification()

        if (
            'password' in flask.request.form and
            flask.request.form['password'] != ""
        ):
            current_user.set_password(flask.request.form['password'])

        database.DB.session.commit()

        flask.flash(u'Your details have been updated', 'success')

        return flask.redirect(flask.url_for('.index'))

@VIEWS.route('/resendemailverification/')
@login_required
def resend_email_verification():
    current_user.email_verification_key = str(random.randint(100000, 999999))
    database.DB.session.commit()

    current_user.send_email_verification()

    return flask.redirect(flask.url_for('.index'))

@VIEWS.route('/verifyemail/', methods=['POST'])
@login_required
def verify_email():
    if 'code' in flask.request.form:
        if flask.request.form['code'] == current_user.email_verification_key:
            current_user.email_verification_key = None
            current_user.email_verified = True

            database.DB.session.commit()

            flask.flash(u'Email verified.', 'success')
        else:
            flask.flash(u'Email verification code invalid.', 'success')

    return flask.redirect(flask.url_for('.index'))

@VIEWS.route('/resendsmsverification/')
@login_required
def resend_sms_verification():
    current_user.sms_verification_key = str(random.randint(100000, 999999))
    database.DB.session.commit()

    current_user.send_sms_verification()

    return flask.redirect(flask.url_for('.index'))

@VIEWS.route('/verifysms/', methods=['POST'])
@login_required
def verify_sms():
    if 'code' in flask.request.form:
        if flask.request.form['code'] == current_user.sms_verification_key:
            current_user.sms_verification_key = None
            current_user.sms_verified = True

            database.DB.session.commit()

            flask.flash(u'Phone verified.', 'success')
        else:
            flask.flash(u'Phone verification code invalid.', 'success')

    return flask.redirect(flask.url_for('.index'))

@VIEWS.route('/updatealertpreferences/', methods=['POST'])
@login_required
def update_alert_preferences():
    if (
        'send_emails' in flask.request.form and
        flask.request.form['send_emails'] == 'yes'
    ):
        current_user.send_email_alerts = True
    else:
        current_user.send_email_alerts = False

    if (
        'send_sms' in flask.request.form and
        flask.request.form['send_sms'] == 'yes'
    ):
        current_user.send_sms_alerts = True
    else:
        current_user.send_sms_alerts = False

    for allergen in models.Allergen.query.all():
        key = 'allergen-{}'.format(allergen.id)

        if (
            key in flask.request.form and
            flask.request.form[key] == 'yes'
        ):
            if allergen not in current_user.allergens:
                current_user.allergens.append(allergen)
        else:
            if allergen in current_user.allergens:
                current_user.allergens.remove(allergen)

    database.DB.session.commit()

    flask.flash(u'Alert preferences updated.', 'success')

    return flask.redirect(flask.url_for('.index'))
