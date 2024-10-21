from flask import Blueprint, request, jsonify
from db import db
from models import Bill

bills_bp = Blueprint('bills', __name__)

@bills_bp.route('/', methods=['POST'])
def create_bill():
    """
    Create a new bill
    ---
    tags:
      - Bills
    parameters:
      - name: bill
        in: body
        required: true
        schema:
          type: object
          properties:
            patient_id:
              type: integer
              example: 1
            status:
              type: string
              example: "Paid"
            description:
              type: string
              example: "Consultation fee for appointment"
            amount:
              type: number
              example: 1000
    responses:
      200:
        description: Bill created successfully
      400:
        description: Missing required fields
    """
    data = request.get_json()
    
    # Check for required fields
    if 'patient_id' not in data or 'status' not in data or 'amount' not in data:
        return jsonify({"message": "Missing required fields"}), 400
    
    # Create the bill
    new_bill = Bill(
        status=data['status'],
        patient_id=data['patient_id'],
        description=data.get('description', ''),  # Default to empty string if not provided
        amount=data['amount']
    )

    db.session.add(new_bill)
    db.session.commit()

    return jsonify({"message": "Bill created successfully"}), 200

