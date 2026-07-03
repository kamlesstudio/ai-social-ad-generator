"""
Payment processing with Stripe
"""

import stripe
from app.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

# Credit packages
CREDIT_PACKAGES = {
    "starter": {"credits": 10, "price": 9.99},
    "popular": {"credits": 50, "price": 39.99},
    "pro": {"credits": 100, "price": 69.99},
    "enterprise": {"credits": 500, "price": 299.99},
}

def create_checkout_session(package_id: str, user_id: str):
    """
    Create a Stripe checkout session for credit purchase
    """
    package = CREDIT_PACKAGES.get(package_id)
    if not package:
        raise ValueError(f"Invalid package: {package_id}")
    
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"{package['credits']} Credits",
                    "description": f"Generate {package['credits']} AI social media ad videos",
                },
                "unit_amount": int(package["price"] * 100),  # Stripe uses cents
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"https://your-domain.com/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url="https://your-domain.com/cancel",
        metadata={
            "user_id": user_id,
            "package_id": package_id,
            "credits": str(package["credits"])
        }
    )
    
    return session.url

def handle_webhook(payload: dict):
    """
    Handle Stripe webhook events
    """
    event_type = payload.get("type")
    
    if event_type == "checkout.session.completed":
        session = payload["data"]["object"]
        user_id = session["metadata"]["user_id"]
        credits = int(session["metadata"]["credits"])
        
        # Add credits to user
        from app.main import user_credits
        user_credits[user_id] = user_credits.get(user_id, 0) + credits
        
        return {"status": "success", "user_id": user_id, "credits_added": credits}
    
    return {"status": "ignored"}