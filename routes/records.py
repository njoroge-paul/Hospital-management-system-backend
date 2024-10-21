from flask import Blueprint, request, jsonify
from models import Record
from db import db

records_bp = Blueprint('records', __name__)

# Route to add a new record
@records_bp.route('/', methods=['POST'])
def add_record():
    """
    Add a new patient record
    ---
    tags:
      - Records
    parameters:
      - name: record
        in: body
        required: true
        schema:
          type: object
          properties:
            subject:
              type: string
              example: "Follow-up on test results"
            patient_id:
              type: integer
              example: 1
            record:
              type: string
              example: "Patient shows improvement in condition."
    responses:
      200:
        description: Record added successfully
      400:
        description: Missing required fields
    """
    data = request.get_json()

    # Check if all required fields are present
    if not all(key in data for key in ('subject', 'patient_id', 'record')):
        return jsonify({'error': 'Missing required fields'}), 400

    # Create a new Record object
    new_record = Record(
        subject=data['subject'],
        patient_id=data['patient_id'],
        record=data['record']
    )

    # Add to the session and commit to save in the database
    db.session.add(new_record)
    db.session.commit()

    return jsonify({'message': 'Record added successfully!'}), 200


