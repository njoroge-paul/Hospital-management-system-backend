from flask import Blueprint, request, jsonify
from models import Appointment, Bill, Patient  
from sqlalchemy import desc
from db import db

appointments_bp = Blueprint('appointments', __name__)

# Endpoint to create an appointment
@appointments_bp.route('/', methods=['POST'])
def create_appointment():
    """
    Create a new appointment
    ---
    tags:
      - Appointments
    parameters:
      - name: appointment
        in: body
        required: true
        schema:
          type: object
          properties:
            patient_id:
              type: integer
              example: 1
            doctor_id:
              type: integer
              example: 2
            appointment_date:
              type: string
              format: date-time
              example: "2024-10-21T14:30:00Z"
            status:
              type: string
              example: "Scheduled"
            reason_for_visit:
              type: string
              example: "Routine checkup"
            notes:
              type: string
              example: "Patient has a history of allergies"
            cost:
              type: number
              example: 1000
    responses:
      201:
        description: Appointment created successfully
    """
    data = request.get_json()
    
    new_appointment = Appointment(
        patient_id=data['patient_id'],
        doctor_id=data['doctor_id'],
        appointment_date=data['appointment_date'],
        status=data.get('status', 'Scheduled'),
        reason_for_visit=data.get('reason_for_visit', ''),
        notes=data.get('notes', ''),
        cost=data.get('cost', 1000)
    )
    
    db.session.add(new_appointment)

    # Create a Bill record after creating the appointment
    new_bill = Bill(
        patient_id=new_appointment.patient_id,
        appointment_id=new_appointment.id,
        amount=float(data.get('cost', 1000)),
        description=f"Bill for appointment {new_appointment.id}"
    )
    
    db.session.add(new_bill)
    db.session.commit()
    
    return jsonify({"message": "Appointment created successfully", "appointment_id": new_appointment.id}), 201

# Endpoint to fetch all appointments for a specific doctor
@appointments_bp.route('/doctor/<int:doctor_id>', methods=['GET'])
def get_appointments_by_doctor(doctor_id):
    """
    Get all appointments for a specific doctor
    ---
    tags:
      - Appointments
    parameters:
      - name: doctor_id
        in: path
        required: true
        type: integer
        description: The ID of the doctor to fetch appointments for
    responses:
      200:
        description: A list of appointments for the specified doctor
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              patient_id:
                type: integer
              doctor_id:
                type: integer
              appointment_date:
                type: string
                format: date-time
              cost:
                type: number
              status:
                type: string
              reason_for_visit:
                type: string
              notes:
                type: string
              created_at:
                type: string
                format: date-time
              updated_at:
                type: string
                format: date-time
              patient:
                type: object
                properties:
                  id:
                    type: integer
                  first_name:
                    type: string
                  last_name:
                    type: string
                  email:
                    type: string
                  phone_number:
                    type: string
                  emergency_contact_phone_number:
                    type: string
    """
    appointments = Appointment.query.filter_by(doctor_id=doctor_id).order_by(desc(Appointment.created_at)).all()
    results = []
    
    for appointment in appointments:
        patient = Patient.query.get(appointment.patient_id)

        results.append({
            "id": appointment.id,
            "patient_id": appointment.patient_id,
            "doctor_id": appointment.doctor_id,
            "appointment_date": appointment.appointment_date,
            "cost": appointment.cost,
            "status": appointment.status,
            "reason_for_visit": appointment.reason_for_visit,
            "notes": appointment.notes,
            "created_at": appointment.created_at,
            "updated_at": appointment.updated_at,
            "patient": {
                "id": patient.id,
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "email": patient.email,
                "phone_number": patient.phone_number,
                "emergency_contact_phone_number": patient.emergency_contact_phone_number,
            } if patient else None  
        })
    
    return jsonify(results), 200

# Endpoint to fetch all appointments for a specific patient
@appointments_bp.route('/patient/<int:patient_id>', methods=['GET'])
def get_appointments_by_patient(patient_id):
    """
    Get all appointments for a specific patient
    ---
    tags:
      - Appointments
    parameters:
      - name: patient_id
        in: path
        required: true
        type: integer
        description: The ID of the patient to fetch appointments for
    responses:
      200:
        description: A list of appointments for the specified patient
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              patient_id:
                type: integer
              doctor_id:
                type: integer
              appointment_date:
                type: string
                format: date-time
              status:
                type: string
              reason_for_visit:
                type: string
              notes:
                type: string
              created_at:
                type: string
                format: date-time
              updated_at:
                type: string
                format: date-time
    """
    appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(desc(Appointment.created_at)).all()
    
    results = []
    
    for appointment in appointments:
        results.append({
            "id": appointment.id,
            "patient_id": appointment.patient_id,
            "doctor_id": appointment.doctor_id,
            "appointment_date": appointment.appointment_date,
            "status": appointment.status,
            "reason_for_visit": appointment.reason_for_visit,
            "notes": appointment.notes,
            "created_at": appointment.created_at,
            "updated_at": appointment.updated_at
        })
    
    return jsonify(results), 200

# Endpoint to update the status of an appointment
@appointments_bp.route('/<int:appointment_id>', methods=['PATCH'])
def update_appointment_status(appointment_id):
    """
    Update the status of an appointment
    ---
    tags:
      - Appointments
    parameters:
      - name: appointment_id
        in: path
        required: true
        type: integer
        description: The ID of the appointment to update
      - name: appointment
        in: body
        required: true
        schema:
          type: object
          properties:
            status:
              type: string
              example: "Completed"
            notes:
              type: string
              example: "Patient completed the checkup."
    responses:
      200:
        description: Appointment status updated successfully
    """
    data = request.get_json()
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Update the status field
    appointment.notes = data.get('notes', appointment.notes)
    appointment.status = data.get('status', appointment.status)
    db.session.commit()
    
    return jsonify({"message": "Appointment status updated successfully"}), 200

