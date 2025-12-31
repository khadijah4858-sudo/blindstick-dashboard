import firebase_admin
from firebase_admin import credentials, db
import random
import time
from datetime import datetime

# Initialize
cred = credentials.Certificate("blindstick-fyp-firebase-adminsdk.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://blindstick-fyp-default-rtdb.asia-southeast1.firebasedatabase.app'
})

ref = db.reference()

while True:
    # Generate random data
    data = {
        'location': {
            'latitude': 2.0456 + random.uniform(-0.001, 0.001),
            'longitude': 102.5677 + random.uniform(-0.001, 0.001),
            'address': 'UiTM Melaka - Live Demo'
        },
        'system': {
            'status': random.choice(['ACTIVE', 'ACTIVE', 'ACTIVE', 'EMERGENCY']),
            'battery': random.randint(75, 100),
            'signal': random.choice(['Strong', 'Medium', 'Weak'])
        },
        'sensors': {
            'distance': random.randint(10, 100),
            'alert_count': random.randint(5, 20)
        },
        'alerts': {
            'status': random.choice(['SAFE', 'SAFE', 'SAFE', 'EMERGENCY']),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }
    
    ref.update(data)
    print(f"Data updated: {datetime.now()}")
    time.sleep(5)