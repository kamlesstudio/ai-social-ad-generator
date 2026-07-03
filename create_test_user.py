"""
Create test user and add credits
"""

from app.models.database import db_service

# Create user
user = db_service.create_user('+919999999999', {
    'name': 'Test User',
    'email': 'test@example.com',
    'credits': 50
})

print(f'✅ User created: {user}')

# Check credits
credits = db_service.get_user_credits('+919999999999')
print(f'💰 Credits: {credits}')

# Add more credits if needed
if credits < 50:
    new_credits = db_service.update_user_credits('+919999999999', 50)
    print(f'✅ Added credits: {new_credits}')