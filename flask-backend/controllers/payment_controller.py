import os
import hmac
import hashlib
import time

from flask import request, jsonify
from bson import ObjectId

from db import payments_collection, users_collection
from services.razorpay_service import razorpay_client


# =========================================================
# CREATE RAZORPAY ORDER
# =========================================================

def create_order():
    try:
        data = request.get_json() or {}

        plan_id = data.get("planId")
        amount = data.get("amount")
        credits = data.get("credits")

        if not amount or not credits:
            return jsonify({
                "message": "Invalid plan data"
            }), 400

        # Razorpay expects amount in paise
        options = {
            "amount": int(amount * 100),
            "currency": "INR",
            "receipt": f"receipt_{int(time.time() * 1000)}"
        }

        # Create Razorpay order
        order = razorpay_client.order.create(
            data=options
        )

        # Save payment in MongoDB
        payment_document = {
            "userId": ObjectId(request.user_id),
            "planId": plan_id,
            "amount": amount,
            "credits": credits,
            "razorpayOrderId": order["id"],
            "razorpayPaymentId": None,
            "status": "created",
            "createdAt": time.time(),
            "updatedAt": time.time()
        }

        payments_collection.insert_one(payment_document)

        return jsonify(order), 200

    except Exception as error:

        print("Create Razorpay Order Error:", error)

        return jsonify({
            "message": f"failed to create Razorpay order {error}"
        }), 500


# =========================================================
# VERIFY RAZORPAY PAYMENT
# =========================================================

def verify_payment():
    try:

        data = request.get_json() or {}

        razorpay_order_id = data.get("razorpay_order_id")
        razorpay_payment_id = data.get("razorpay_payment_id")
        razorpay_signature = data.get("razorpay_signature")

        if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
            return jsonify({
                "message": "Payment verification data is incomplete"
            }), 400

        # Same body used by Razorpay
        body = (
            razorpay_order_id
            + "|"
            + razorpay_payment_id
        )

        # Generate expected signature
        key_secret = os.getenv("RAZORPAY_KEY_SECRET")

        expected_signature = hmac.new(
            key_secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

        # Compare signatures safely
        if not hmac.compare_digest(
            expected_signature,
            razorpay_signature
        ):
            return jsonify({
                "message": "Invalid payment signature"
            }), 400

        # Find payment
        payment = payments_collection.find_one({
            "razorpayOrderId": razorpay_order_id
        })

        if not payment:
            return jsonify({
                "message": "Payment not found"
            }), 404

        # Already paid
        if payment.get("status") == "paid":
            return jsonify({
                "message": "Already processed"
            }), 200

        # Update payment
        payments_collection.update_one(
            {
                "_id": payment["_id"]
            },
            {
                "$set": {
                    "status": "paid",
                    "razorpayPaymentId": razorpay_payment_id,
                    "updatedAt": time.time()
                }
            }
        )

        # Add credits to user
        user_id = payment["userId"]

        users_collection.update_one(
            {
                "_id": user_id
            },
            {
                "$inc": {
                    "credits": payment["credits"]
                }
            }
        )

        # Get updated user
        updated_user = users_collection.find_one({
            "_id": user_id
        })

        # Convert ObjectId to JSON-safe format
        if updated_user:
            updated_user["_id"] = str(
                updated_user["_id"]
            )

        return jsonify({
            "success": True,
            "message": "Payment verified and credits added",
            "user": updated_user
        }), 200

    except Exception as error:

        print("Verify Razorpay Payment Error:", error)

        return jsonify({
            "message": f"failed to verify Razorpay payment {error}"
        }), 500