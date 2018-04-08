from intweet.models.user import User
from intweet.models.rule import Rule
from intweet.models.tweet import Tweet
from intweet.config import CONFIG
from flask import render_template, request, url_for,\
    session, redirect, Blueprint
from intweet.database import get_db_session
import validators
import re
from sqlalchemy import func


bp = Blueprint('routes', __name__)


@bp.route('/')
@bp.route('/dashboard')
@bp.route('/home')
def home():
    local_config = {
        "page_name": "Home"
    }
    # Home Page
    if session.get('logged_in'):
        userdata = {
            'fullname': session.get('name'),
            'email': session.get('email')
        }
        return render_template('user_home.html', global_config=CONFIG,
                               local_config=local_config, userdata=userdata)
    else:
        return render_template('home.html', global_config=CONFIG,
                               local_config=local_config)


@bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('email', None)
    session.pop('name', None)
    return redirect(url_for('routes.home'))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Login Page
    error = {}
    error['errors'] = 0
    if request.method == 'POST':
        if not request.form['email'] or len(request.form['email']) == 0:
            error['message'] = "No email address provided"
            error['errors'] += 1

        elif not request.form['password'] or \
                len(request.form['password']) == 0:
            error['message'] = "No password provided"
            error['errors'] += 1

        else:
            # Attempt to log the user in
            db = get_db_session()
            query = db.query(User).\
                filter(User.email == request.form['email'])
            user = query.one()
            if not user.validate_password(request.form['password']):
                # email and password incorrect
                error['message'] = "Invalid credentials"
                error['errors'] += 1
            else:
                # email and password correct - log the user in!
                session['logged_in'] = True
                session['user'] = user.email
                session['name'] = user.fullname
                session['user_id'] = user.id
                return redirect(url_for('routes.home'))

    local_config = {
        "page_name": "Login"
    }
    return render_template('login.html', global_config=CONFIG,
                           local_config=local_config, error=error)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    # Register Page
    error = {}
    error['errors'] = 0
    db = get_db_session()

    if request.method == 'POST':
        if not request.form['email'] or len(request.form['email']) == 0:
            error['message'] = "No email address provided"
            error['errors'] += 1

        elif not request.form['password'] or \
                len(request.form['password']) == 0:
            error['message'] = "No password provided"
            error['errors'] += 1

        elif not request.form['fullname'] or \
                len(request.form['fullname']) == 0:
            error['message'] = "No full name provided"
            error['errors'] += 1

        elif not validators.email(request.form['email']):
            error['message'] = "Invalid email address provided"
            error['errors'] += 1

        elif len(request.form['password']) < 8 or \
                re.search('[0-9]', request.form['password']) is None or \
                re.search('[A-Z]', request.form['password']) is None or \
                re.search('[a-z]', request.form['password']) is None:
            error['message'] = "Password does not meet requirements"
            error['errors'] += 1

        elif db.query(User).filter(
                User.email == request.form['email']).count() > 0:
            error['message'] = "User already registered"
            error['errors'] += 1

        else:
            # We can actually register them now!
            user = User(
                fullname=request.form['fullname'],
                email=request.form['email'],
                password=request.form['password'],
                admin=0,
                active=1
            )
            db.add(user)
            db.commit()

            session['logged_in'] = True
            session['user'] = user.email
            session['name'] = user.fullname
            session['user_id'] = user.id
            return redirect(url_for('routes.home'))

    local_config = {
        "page_name": "Register"
    }

    return render_template(
        'register.html',
        global_config=CONFIG,
        local_config=local_config,
        error=error
    )


@bp.route('/monitor', methods=['GET', 'POST'])
def monitor():
    if not session.get('logged_in'):
        return redirect(url_for('routes.home'))
    else:
        userdata = {
            'fullname': session.get('name'),
            'email': session.get('email'),
            'user_id': session.get('user_id')
        }
        local_config = {
            "page_name": "Your Monitoring Rules"
        }
        db = get_db_session()
        query = db.query(
            Rule.rulename,
            Rule.keywords,
            Rule.description,
            Rule.active,
            Rule.account_handle,
            Rule.id,
            func.count().label('total')
        ).filter(
            Rule.userid == userdata['user_id']
        ).outerjoin(
            Tweet
        ).filter(
            Rule.id == Tweet.ruleid
        ).group_by(
            Rule.id
        ).order_by(
            Rule.rulename
        )
        rules = query.all()

        return render_template(
            'user_rules.html',
            global_config=CONFIG,
            local_config=local_config,
            userdata=userdata,
            rules=rules
        )
