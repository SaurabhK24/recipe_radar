import functools
from flask import Blueprint, request, jsonify, session, g
from werkzeug.security import check_password_hash, generate_password_hash
from backend.db import get_db

def init_bin_str():
    size = 0
    with open('backend/ingredients_list.txt', 'r') as file:
        for size, _ in enumerate(file):
            pass

    bin_str = ''
    for i in range(size):
        bin_str += '0'

    return bin_str

bp = Blueprint('auth', __name__, url_prefix = '/auth')

@bp.route('/register', methods = ['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    db = get_db()
    error = None

    if not username:
        error = 'Username is required'
    elif ' ' in username:
        error = 'Username cannot contain spaces'
    elif not password:
        error = 'Password is required'
    elif ' ' in password:
        error = 'Password cannot contain spaces'

    if error is None:
        try:    # try to add the new user to the database
            db.execute( 
                'INSERT INTO user (username, password, ingredients) VALUES (?, ?, ?)',  # due to the way parameter substitution is
                (username, generate_password_hash(password), init_bin_str()),           # handled in python we don't need to
            )                                                                           # worry about sql injection! :D
            db.commit()
        except db.IntegrityError:   # username already exists
            error = f"User {username} is already registered."
        else:
            return jsonify({'message': 'Registration success'}), 201

    return jsonify({'error': error}), 400

@bp.route('/login', methods = ['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    db = get_db()
    error = None

    # get the user entry in the user table, if it exists
    user = db.execute(
        'SELECT * FROM user WHERE username = ?', (username,)
    ).fetchone()

    if user is None:
        error = 'Incorrect username'
    elif not check_password_hash(user['password'], password):
        error =  'Incorrect password'

    if error is None:
        session.clear()
        session['user_id'] = user['id']
        return jsonify({'message': 'Login success'}), 200
    
    return jsonify({'error': error}), 400

@bp.before_app_request
def load_current_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return jsonify({'message': 'Logout success'}), 200

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return jsonify({'error': 'Not signed in'}), 401
    
        return view(**kwargs)
    return wrapped_view
