import requests
import random
import time
from datetime import datetime

# Firebase Config
FIREBASE_URL = "https://blindstick-fyp-default-rtdb.asia-southeast1.firebasedatabase.app"
FIREBASE_SECRET = "3gRvZR3D5hiePgFW3wGkYUWv9jCRYGuHwpNw7X6j"

# Telegram Config
TELEGRAM_TOKEN = "8438143594:AAFRSiO4qQakEiR8xksu87BYoaX8MBIo3aM"
CHAT_ID = "533909832"

# Random Locations (Malaysia)
LOCATIONS = [
    {"name": "UiTM Melaka Jasin", "lat_min": 2.0400, "lat_max": 2.0500, "lon_min": 102.5600, "lon_max": 102.5750},
    {"name": "KL City Centre", "lat_min": 3.1390, "lat_max": 3.1490, "lon_min": 101.6869, "lon_max": 101.6969},
    {"name": "Penang Georgetown", "lat_min": 5.4140, "lat_max": 5.4240, "lon_min": 100.3287, "lon_max": 100.3387},
    {"name": "Johor Bahru", "lat_min": 1.4854, "lat_max": 1.4954, "lon_min": 103.7618, "lon_max": 103.7718},
    {"name": "Melaka Town", "lat_min": 2.1896, "lat_max": 2.1996, "lon_min": 102.2501, "lon_max": 102.2601},
    {"name": "Shah Alam", "lat_min": 3.0738, "lat_max": 3.0838, "lon_min": 101.5183, "lon_max": 101.5283},
    {"name": "Alor Setar", "lat_min": 6.1248, "lat_max": 6.1348, "lon_min": 100.3673, "lon_max": 100.3773},
    {"name": "Ipoh", "lat_min": 4.5975, "lat_max": 4.6075, "lon_min": 101.0901, "lon_max": 101.1001},
    {"name": "Kota Kinabalu", "lat_min": 5.9788, "lat_max": 5.9888, "lon_min": 116.0753, "lon_max": 116.0853},
    {"name": "Kuching", "lat_min": 1.5535, "lat_max": 1.5635, "lon_min": 110.3593, "lon_max": 110.3693},
]

def generate_random_location():
    """Generate random location from predefined areas"""
    location = random.choice(LOCATIONS)
    
    lat = random.uniform(location["lat_min"], location["lat_max"])
    lon = random.uniform(location["lon_min"], location["lon_max"])
    
    return {
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
        "address": location["name"]
    }

def get_timestamp():
    """Get current timestamp"""
    return datetime.now().strftime("%H:%M:%S")

def send_to_firebase(location, timestamp):
    """Send data to Firebase"""
    print("\n📤 Sending to Firebase...")
    
    # 1. Update location
    url = f"{FIREBASE_URL}/location.json?auth={FIREBASE_SECRET}"
    data = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "address": location["address"]
    }
    response = requests.put(url, json=data)
    print(f"   → Location: {'✅' if response.status_code == 200 else '❌'}")
    
    # 2. Update alerts
    url = f"{FIREBASE_URL}/alerts.json?auth={FIREBASE_SECRET}"
    data = {
        "status": "EMERGENCY",
        "timestamp": timestamp
    }
    response = requests.put(url, json=data)
    print(f"   → Alert: {'✅' if response.status_code == 200 else '❌'}")
    
    # 3. Add to history
    url = f"{FIREBASE_URL}/alerts/history.json?auth={FIREBASE_SECRET}"
    data = {
        f"alert_{int(time.time())}": f"🚨 Emergency at {timestamp} - {location['address']}"
    }
    response = requests.patch(url, json=data)
    print(f"   → History: {'✅' if response.status_code == 200 else '❌'}")
    
    # 4. Update system
    url = f"{FIREBASE_URL}/system.json?auth={FIREBASE_SECRET}"
    data = {
        "status": "EMERGENCY",
        "battery": 85,
        "signal": "Strong"
    }
    response = requests.put(url, json=data)
    print(f"   → System: {'✅' if response.status_code == 200 else '❌'}")

def send_to_telegram(location, timestamp):
    """Send alert to Telegram"""
    print("\n📤 Sending to Telegram...")
    
    message = f"""🚨 *EMERGENCY ALERT*

🎲 *Demo Mode - Random Location*

📍 *Coordinates:* {location['latitude']}, {location['longitude']}
🏢 *Area:* {location['address']}
⏰ *Time:* {timestamp}

🗺️ [Open in Google Maps](https://www.google.com/maps?q={location['latitude']},{location['longitude']})

_This is a demo with random location_"""
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    response = requests.post(url, data=data)
    print(f"   → Telegram: {'✅ Sent!' if response.status_code == 200 else '❌ Failed'}")

def simulate_emergency():
    """Main function to simulate emergency alert"""
    print("\n" + "="*50)
    print("🚨 SIMULATING EMERGENCY ALERT")
    print("="*50)
    
    # Generate random location
    location = generate_random_location()
    timestamp = get_timestamp()
    
    print("\n🎲 Random Emergency Location:")
    print(f"   Area:      {location['address']}")
    print(f"   Latitude:  {location['latitude']}")
    print(f"   Longitude: {location['longitude']}")
    print(f"   Time:      {timestamp}")
    
    # Send to Firebase
    send_to_firebase(location, timestamp)
    
    # Send to Telegram
    send_to_telegram(location, timestamp)
    
    print("\n✅ Emergency alert sent successfully!")
    print("="*50 + "\n")

if __name__ == "__main__":
    # Ask for mode
    print("\n🦯 BLINDSTICK EMERGENCY SIMULATOR")
    print("="*50)
    print("1. Single alert")
    print("2. Multiple alerts (testing mode)")
    print("3. Auto mode (every 10 seconds)")
    
    choice = input("\nSelect mode (1/2/3): ").strip()
    
    if choice == "1":
        simulate_emergency()
    
    elif choice == "2":
        count = int(input("How many alerts? "))
        for i in range(count):
            print(f"\n[Alert {i+1}/{count}]")
            simulate_emergency()
            if i < count - 1:
                time.sleep(3)  # Wait 3 seconds between alerts
    
    elif choice == "3":
        print("\n🔄 Auto mode started (Ctrl+C to stop)")
        try:
            while True:
                simulate_emergency()
                print("⏳ Waiting 10 seconds...\n")
                time.sleep(10)
        except KeyboardInterrupt:
            print("\n\n⛔ Auto mode stopped")
    
    else:
        print("❌ Invalid choice")