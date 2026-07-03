from app.models.database import db_service

credits = db_service.update_user_credits('+919999999999', 50)
print(f'✅ Credits updated: {credits}')

# Verify
balance = db_service.get_user_credits('+919999999999')
print(f'💰 New balance: {balance}')