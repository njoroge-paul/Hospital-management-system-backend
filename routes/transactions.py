from flask import Blueprint, request, jsonify, current_app
from db import db
import requests
from models import Transaction, Bill
import base64
from datetime import datetime
import logging
from sqlalchemy import desc

transactions_bp = Blueprint('transactions', __name__)
logger = logging.getLogger(__name__)

@transactions_bp.route('/', methods=['POST'])
def add_transaction():
    """
    Add a new transaction
    ---
    tags:
      - Transactions
    parameters:
      - name: transaction
        in: body
        required: true
        schema:
          type: object
          properties:
            checkout_request_id:
              type: string
              example: "CHK123456789"
            bill_id:
              type: integer
              example: 1
            status:
              type: string
              example: "Pending"
            amount:
              type: number
              example: 1000
            paying_phone_number:
              type: string
              example: "254712345678"
            receipt_number:
              type: string
              example: "RCPT12345"
            transaction_date:
              type: string
              format: date-time
              example: "2023-10-21T14:48:00"
    responses:
      201:
        description: Transaction added successfully
      400:
        description: Bad Request
    """
    data = request.get_json()

    # Create a new transaction object
    new_transaction = Transaction(
        checkout_request_id=data['checkout_request_id'],
        bill_id=data['bill_id'],
        status=data['status'],
        amount=data['amount'],
        paying_phone_number=data['paying_phone_number'],
        receipt_number=data['receipt_number'],
        transaction_date=data['transaction_date']
    )

    # Add the transaction to the session and commit
    db.session.add(new_transaction)
    db.session.commit()

    return jsonify({"message": "Transaction added", "transaction_id": new_transaction.id}), 201

@transactions_bp.route('/', methods=['GET'])
def get_all_transactions():
    """
    Retrieve all transactions
    ---
    tags:
      - Transactions
    responses:
      200:
        description: A list of transactions
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              checkout_request_id:
                type: string
                example: "CHK123456789"
              bill_id:
                type: integer
                example: 1
              status:
                type: string
                example: "Pending"
              amount:
                type: number
                example: 1000
              paying_phone_number:
                type: string
                example: "254712345678"
              receipt_number:
                type: string
                example: "RCPT12345"
              transaction_date:
                type: string
                format: date-time
                example: "2023-10-21T14:48:00"
      500:
        description: Internal Server Error
    """
    try:
        # Query all transactions from the database
        transactions = Transaction.query.all()

        # Prepare the transactions list in JSON format
        transactions_list = [
            {
                "id": transaction.id,
                "checkout_request_id": transaction.checkout_request_id,
                "bill_id": transaction.bill_id,
                "status": transaction.status,
                "amount": transaction.amount,
                "paying_phone_number": transaction.paying_phone_number,
                "receipt_number": transaction.receipt_number,
                "transaction_date": transaction.transaction_date
            }
            for transaction in transactions
        ]

        return jsonify(transactions_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Function to get OAuth token
def get_mpesa_access_token(consumer_key, consumer_secret):
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    r = requests.get(api_url, auth=(consumer_key, consumer_secret))
    json_response = r.json()
    access_token = json_response['access_token']
    return access_token

# Function to initiate STK push
def stk_push_request(phone_number, amount, bill_id, description):
    access_token = get_mpesa_access_token(current_app.config['MPESA_CONSUMER_KEY'], current_app.config['MPESA_CONSUMER_SECRET'])
    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    
    headers = {"Authorization": f"Bearer {access_token}"}
    shortcode = current_app.config['MPESA_SHORTCODE']

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    passkey = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'
    data_to_encode = '174379' + passkey + timestamp
    password = base64.b64encode(data_to_encode.encode('utf-8')).decode('utf-8')

    # STK Push payload
    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": 'https://your_callback_url.com/transactions/callback',
        "AccountReference": f"{bill_id}_transaction",
        "TransactionDesc": description
    }

    logger.info("Payload Data: %s", payload)

    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()

@transactions_bp.route('/deposit', methods=['POST'])
def initiate_mpesa_payment():
    """
    Initiate an M-Pesa payment
    ---
    tags:
      - Transactions
    parameters:
      - name: payment
        in: body
        required: true
        schema:
          type: object
          properties:
            bill_id:
              type: integer
              example: 1
            phone_number:
              type: string
              example: "254712345678"
            description:
              type: string
              example: "Payment for services"
    responses:
      200:
        description: STK Push initiated successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "STK Push initiated successfully"
            transaction_id:
              type: integer
              example: 1
      400:
        description: Failed to initiate STK Push
      404:
        description: Bill not found
    """
    logger.info("Received payload: %s", request.json)

    data = request.get_json()

    bill_id = data['bill_id']
    bill = Bill.query.get(bill_id)

    if not bill:
        return jsonify({"message": "Bill not found"}), 404

    phone_number = data['phone_number']
    amount = bill.amount
    description = data.get('description', 'Payment')  # Optional description

    # Call the STK Push function
    stk_response = stk_push_request(phone_number, amount, bill_id, description)

    if stk_response.get('ResponseCode') == '0':
        checkout_request_id = stk_response.get('CheckoutRequestID')

        transaction = Transaction(
            checkout_request_id=checkout_request_id,
            bill_id=bill_id,
            status="Pending",
            amount=amount,
            paying_phone_number=phone_number,
            transaction_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        db.session.add(transaction)
        db.session.commit()

        return jsonify({"message": "STK Push initiated successfully", "transaction_id": transaction.id}), 200
    else:
        return jsonify({"message": "Failed to initiate STK Push", "error": stk_response.get('errorMessage')}), 400

@transactions_bp.route('/callback', methods=['POST'])
def mpesa_callback():
    """
    Handle M-Pesa callback
    ---
    tags:
      - Transactions
    responses:
      200:
        description: Callback processed successfully
      404:
        description: Transaction not found
      500:
        description: Internal Server Error
    """
    data = request.get_json()
    if data:
        logger.info("Callback Data: %s", data)

    try:
        checkout_request_id = data['Body']['stkCallback']['CheckoutRequestID']
        result_code = data['Body']['stkCallback']['ResultCode']
        logger.info("checkout_request_id: %s", checkout_request_id)

        transaction = Transaction.query.filter_by(checkout_request_id=checkout_request_id).first()

        if transaction:
            if result_code == 0:
                transaction.status = "Paid"
                bill = Bill.query.filter_by(id=transaction.bill_id).first()
                if bill:
                    bill.status = "Paid"

                db.session.commit()
                return jsonify({"message": "Transaction and Bill updated successfully"}), 200
            else:
                return jsonify({"message": "Payment not successful, no updates made"}), 200
        else:
            return jsonify({"error": "Transaction not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

