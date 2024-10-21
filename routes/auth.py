from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from models import User
from db import db

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User Registration
    ---
    tags:
      - Auth
    parameters:
      - name: user
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: "user@example.com"
              description: Email of the user
            password:
              type: string
              example: "password123"
              description: Password of the user
            role:
              type: integer
              example: 1
              description: Role of the user (default is 1)
    responses:
      201:
        description: User registered successfully
      400:
        description: User already exists
    """
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 1)

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "User already exists"}), 400

    new_user = User(email=email)
    new_user.set_password(password)
    new_user.set_role(role)  

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User Login
    ---
    tags:
      - Auth
    parameters:
      - name: user
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: "user@example.com"
              description: Email of the user
            password:
              type: string
              example: "password123"
              description: Password of the user
    responses:
      200:
        description: User logged in successfully
        schema:
          type: object
          properties:
            access_token:
              type: string
              example: "your_jwt_access_token"
            role:
              type: integer
              example: 2
              description: Role of the user
            id:
              type: integer
              example: 1
              description: User ID
            doctor_id:
              type: integer
              example: 1
              description: Doctor ID (if applicable)
            patient_id:
              type: integer
              example: 1
              description: Patient ID (if applicable)
      401:
        description: Invalid credentials
    """
    data = request.get_json()
    email = data['email']
    password = data['password']

    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        access_token = create_access_token(identity={'email': user.email})

        if user.role == 2:
            return jsonify(access_token=access_token, role=user.role, id=user.id, doctor_id=user.doctor_id), 200
        
        if user.role == 3:
            return jsonify(access_token=access_token, role=user.role, id=user.id, patient_id=user.patient_id), 200
        else:
            return jsonify(access_token=access_token, role=user.role, id=user.id), 200
            
    else:
        return jsonify({"message": "Invalid credentials"}), 401

@auth_bp.route('/users', methods=['GET'])
def users():
    """
    Get User Count
    ---
    tags:
      - Auth
    responses:
      200:
        description: Count of registered users
        schema:
          type: object
          properties:
            user_count:
              type: integer
              example: 10
    """
    user_count = User.query.count()
    return jsonify(user_count=user_count), 200

