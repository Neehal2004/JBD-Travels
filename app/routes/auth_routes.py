from flask import Blueprint, request, jsonify
from ..models import db, User
from ..services.auth_service import generate_token, token_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    full_name = data.get('full_name', '').strip()
    role = data.get('role', 'customer').strip().lower()
    nationality = data.get('nationality', 'United States')

    if not username or not email or not password:
        return jsonify({'success': False, 'message': 'Username, email and password are required.'}), 400

    if role not in ['customer', 'employee', 'admin']:
        role = 'customer'

    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Username is already taken.'}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email is already registered.'}), 409

    user = User(
        username=username,
        email=email,
        full_name=full_name or username,
        role=role,
        nationality=nationality
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    token = generate_token(user)
    return jsonify({
        'success': True,
        'message': f'Registration successful as {role.capitalize()}.',
        'token': token,
        'user': user.to_dict()
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email_or_user = data.get('email_or_username', '').strip()
    password = data.get('password', '')
    expected_role = data.get('role') or data.get('expected_role')

    if not email_or_user or not password:
        return jsonify({'success': False, 'message': 'Please provide email/username and password.'}), 400

    user = User.query.filter(
        (User.email == email_or_user.lower()) | (User.username == email_or_user)
    ).first()

    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': 'Invalid credentials. Please verify your email/username and password.'}), 401

    # Role enforcement when logging in via specific portal
    if expected_role:
        role_req = expected_role.strip().lower()
        if role_req == 'admin' and user.role != 'admin':
            return jsonify({'success': False, 'message': 'Access denied: This account does not possess Administrator privileges.'}), 403
        if role_req in ['employee', 'agent'] and user.role != 'employee':
            return jsonify({'success': False, 'message': 'Access denied: This account does not possess Travel Agent privileges.'}), 403
        if role_req == 'customer' and user.role != 'customer':
            return jsonify({'success': False, 'message': 'Access notice: Staff accounts (Agent / Admin) must sign in through their respective role portal.'}), 403

    token = generate_token(user)
    return jsonify({
        'success': True,
        'message': f'Welcome back, {user.full_name or user.username}!',
        'token': token,
        'user': user.to_dict()
    })

@auth_bp.route('/me', methods=['GET'])
@token_required
def me(current_user):
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    })

@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    data = request.get_json() or {}
    if 'full_name' in data:
        current_user.full_name = data['full_name'].strip()
    if 'phone' in data:
        current_user.phone = data['phone'].strip()
    if 'nationality' in data:
        current_user.nationality = data['nationality'].strip()
    if 'preferred_currency' in data:
        current_user.preferred_currency = data['preferred_currency'].strip()

    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Profile updated successfully.',
        'user': current_user.to_dict()
    })
