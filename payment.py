from yookassa import Configuration, Payment
import uuid

Configuration.account_id = 418488
Configuration.secret_key = live_x3MHeMtUz451_uhHNqafe13zSNqOqr27naz3sxPiUsQ

async def create_yookassa_payment(amount, description, user_id):
    payment = Payment.create({
        "amount": {
            "value": f"{amount}.00",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": f"https://t.me/your_bot?start=payment_{user_id}"
        },
        "capture": True,
        "description": description,
        "metadata": {
            "user_id": user_id
        }
    }, uuid.uuid4())
    
    return payment.confirmation.confirmation_url, payment.id
