import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import folium
from streamlit_folium import st_folium
from datetime import datetime
import time
import requests

# =========================
# Telegram Config
# =========================
TELEGRAM_TOKEN = "8438143594:AAFRSiO4qQakEiR8xksu87BYoaX8MBIo3aM"
CHAT_ID = "533909832"

# Track last alert to avoid spam
last_alert_sent = {"time": 0, "status": ""}

def send_telegram_alert(msg):
    """Hantar mesej ke Telegram bot"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        response = requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=5)
        if response.status_code == 200:
            st.success("✅ Telegram notification sent!")
        else:
            st.error(f"❌ Telegram error: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Telegram send error: {e}")

# =========================
# Page config
# =========================
st.set_page_config(
    page_title="BlindStick Monitor",
    page_icon="🦯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header { 
        font-size: 2.5rem; font-weight: bold; text-align: center; padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
        color: white; border-radius: 10px; margin-bottom: 2rem; 
    }
    .status-active { color: #4CAF50; font-weight: bold; font-size: 1.5rem; }
    .status-emergency { 
        color: #f44336; font-weight: bold; font-size: 1.5rem;
        animation: blink 1s infinite; 
    }
    @keyframes blink { 50% { opacity: 0.3; } }
    .alert-box { 
        padding: 1rem; border-radius: 8px; margin: 0.5rem 0; 
        color: #1a1a1a; font-weight: 500; 
    }
    .alert-emergency { background: #ffebee; border-left: 4px solid #f44336; color: #c62828; }
    .alert-warning { background: #fff3e0; border-left: 4px solid #ff9800; color: #e65100; }
    .alert-info { background: #e3f2fd; border-left: 4px solid #2196f3; color: #0d47a1; }
    .alert-box b { color: inherit; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# =========================
# Initialize Firebase
# =========================
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        try:
            firebase_config = dict(st.secrets["firebase"])
            cred = credentials.Certificate(firebase_config)
        except:
            cred = credentials.Certificate("blindstick-fyp-firebase-adminsdk.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://blindstick-fyp-default-rtdb.asia-southeast1.firebasedatabase.app'
        })
    return db.reference()

# =========================
# Get realtime data
# =========================
def get_data():
    try:
        ref = init_firebase()
        data = {
            'location': ref.child('location').get() or {},
            'alerts': ref.child('alerts').get() or {},
            'sensors': ref.child('sensors').get() or {},
            'system': ref.child('system').get() or {}
        }
        return data
    except Exception as e:
        st.error(f"❌ Firebase connection error: {e}")
        return {
            'location': {'latitude': 2.0456, 'longitude': 102.5677, 'address': 'UiTM Melaka'},
            'alerts': {'status': 'SAFE', 'timestamp': '00:00:00'},
            'sensors': {'distance': 50, 'alert_count': 0},
            'system': {'status': 'ACTIVE', 'battery': 85, 'signal': 'Strong'}
        }

# =========================
# Check and send Telegram alert
# =========================
def check_emergency(data):
    global last_alert_sent
    current_status = data['alerts'].get('status', 'SAFE')
    current_time = time.time()
    
    # Kalau emergency dan belum send dalam 10 saat
    if current_status == 'EMERGENCY' and (current_time - last_alert_sent["time"] > 10):
        distance = data['sensors'].get('distance', 'N/A')
        timestamp = data['alerts'].get('timestamp', 'N/A')
        location = f"{data['location'].get('latitude', '')}, {data['location'].get('longitude', '')}"
        
        msg = f"""🚨 EMERGENCY ALERT!
        
📍 Location: {location}
⏰ Time: {timestamp}
📏 Distance: {distance} cm
🔗 Track: https://www.google.com/maps?q={location}

Immediate action required!"""
        
        send_telegram_alert(msg)
        last_alert_sent["time"] = current_time
        last_alert_sent["status"] = current_status

# =========================
# Main dashboard
# =========================
def main():
    st.markdown('<div class="main-header">🦯 BLINDSTICK LIVE MONITORING</div>', unsafe_allow_html=True)
    st.info("🔄 Dashboard updates automatically every 5 seconds")
    
    # Get data
    data = get_data()
    
    # Check emergency and send Telegram
    check_emergency(data)
    
    # -------------------------
    # Top Metrics
    # -------------------------
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        status = data['system'].get('status', 'Unknown')
        if status == 'EMERGENCY':
            st.markdown(f'<div class="status-emergency">🚨 {status}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-active">🟢 {status}</div>', unsafe_allow_html=True)
    with col2:
        battery = data['system'].get('battery', 0)
        st.metric("🔋 Battery", f"{battery}%")
    with col3:
        signal = data['system'].get('signal', 'Unknown')
        st.metric("📡 Signal", signal)
    with col4:
        last_update = datetime.now().strftime("%H:%M:%S")
        st.metric("⏰ Updated", last_update)
    st.divider()
    
    # -------------------------
    # Location Map
    # -------------------------
    col_map, col_info = st.columns([2,1])
    with col_map:
        st.subheader("📍 Current Location")
        lat = float(data['location'].get('latitude', 2.0456))
        lon = float(data['location'].get('longitude', 102.5677))
        m = folium.Map(location=[lat, lon], zoom_start=16, tiles='OpenStreetMap')
        folium.Marker(
            [lat, lon],
            popup=f"<b>User Location</b><br>Lat: {lat}<br>Lon: {lon}",
            tooltip="Blind Stick User",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
        folium.Circle([lat, lon], radius=50, color='blue', fill=True, opacity=0.2).add_to(m)
        st_folium(m, width=700, height=400)
        st.caption(f"📍 Coordinates: {lat:.6f}, {lon:.6f}")
        st.caption(f"🏢 Address: {data['location'].get('address', 'Loading...')}")
    
    # -------------------------
    # Alert Status & Sensors
    # -------------------------
    with col_info:
        st.subheader("🚨 Alert Status")
        
        # Get timestamp from Firebase
        firebase_timestamp = data['alerts'].get('timestamp', 'N/A')
        
        # If Firebase timestamp valid, use it; otherwise use current time
        if firebase_timestamp and firebase_timestamp != 'N/A' and firebase_timestamp != '00:00:00':
            display_time = firebase_timestamp
        else:
            display_time = datetime.now().strftime("%H:%M:%S")

        alert_status = data['alerts'].get('status', 'SAFE')
        if alert_status == 'EMERGENCY':
            st.markdown('<div class="alert-box alert-emergency">🔴 <b>EMERGENCY ACTIVE</b><br>Immediate attention required!</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-box alert-info">🟢 <b>NO EMERGENCY</b><br>System operating normally</div>', unsafe_allow_html=True)
        
        st.caption(f"Last Alert: {display_time}")
        st.divider()
        
        st.subheader("📊 Obstacle Detection")
        distance = int(data['sensors'].get('distance', 0))
        progress = max(0, min(100, (distance / 100) * 100))
        st.progress(progress / 100, text=f"Distance: {distance} cm")
        
        if distance < 30:
            st.warning("⚠️ Obstacle nearby!")
        elif distance < 50:
            st.info("ℹ️ Caution zone")
        else:
            st.success("✅ Clear path")
        
        alerts_today = int(data['sensors'].get('alert_count', 0))
        st.metric("Alerts Today", alerts_today)
    
    # -------------------------
    # Recent Alerts
    # -------------------------
    st.divider()
    st.subheader("📜 Recent Alerts")
    
    # Get history from Firebase
    try:
        alerts_history = data['alerts'].get('history', {})
        recent_alerts = []
        
        for key, msg in alerts_history.items():
            # Extract timestamp from key (milliseconds)
            try:
                timestamp_ms = int(key)
                alert_time = datetime.fromtimestamp(timestamp_ms / 1000).strftime("%H:%M:%S")
            except:
                alert_time = datetime.now().strftime("%H:%M:%S")
            
            recent_alerts.append({
                'time': alert_time,
                'type': 'emergency' if 'Emergency' in msg or '🚨' in msg else 'warning' if '⚠️' in msg else 'info',
                'msg': msg,
                'timestamp': timestamp_ms if 'timestamp_ms' in locals() else 0
            })
        
        # Sort by timestamp (most recent first)
        recent_alerts = sorted(recent_alerts, key=lambda x: x.get('timestamp', 0), reverse=True)[:5]
        
        if not recent_alerts:
            raise Exception("No alerts")
            
    except:
        recent_alerts = [
            {
                'time': datetime.now().strftime("%H:%M:%S"),
                'type': 'info',
                'msg': 'System Online - Waiting for data...',
                'timestamp': 0
            }
        ]
    
    for alert in recent_alerts:
        alert_type = alert.get('type', 'info')
        alert_class = f"alert-{alert_type}"
        icon = '🔴' if alert_type=='emergency' else '🟡' if alert_type=='warning' else '🟢'
        st.markdown(
            f'<div class="alert-box {alert_class}">{icon} <b>{alert["time"]}</b> - {alert["msg"]}</div>', 
            unsafe_allow_html=True
        )
    
    # -------------------------
    # Footer
    # -------------------------
    st.divider()
    col_footer1, col_footer2, col_footer3 = st.columns(3)
    with col_footer1:
        st.info("💡 **Real-time:** Dashboard updates every 5 seconds")
    with col_footer2:
        st.info("🔗 **Telegram:** Alerts sent automatically")
    with col_footer3:
        st.info("📱 **Mobile:** Works on all devices")
    
    # Auto-refresh every 5 seconds
    time.sleep(5)
    st.rerun()

if __name__ == "__main__":
    main()
