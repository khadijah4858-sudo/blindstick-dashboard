import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
from datetime import datetime
import time

# Page config
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
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .status-active {
        color: #4CAF50;
        font-weight: bold;
        font-size: 1.5rem;
    }
    .status-emergency {
        color: #f44336;
        font-weight: bold;
        font-size: 1.5rem;
        animation: blink 1s infinite;
    }
    @keyframes blink {
        50% { opacity: 0.3; }
    }
    .alert-box {
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .alert-emergency {
        background: #ffebee;
        border-left: 4px solid #f44336;
    }
    .alert-warning {
        background: #fff3e0;
        border-left: 4px solid #ff9800;
    }
    .alert-info {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Firebase
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate("blindstick-fyp-firebase-adminsdk.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://blindstick-fyp-default-rtdb.asia-southeast1.firebasedatabase.app'
        })
    return db.reference()

# Get realtime data
def get_data():
    ref = init_firebase()
    return {
        'location': ref.child('location').get() or {},
        'alerts': ref.child('alerts').get() or {},
        'sensors': ref.child('sensors').get() or {},
        'system': ref.child('system').get() or {}
    }

# Main dashboard
def main():
    # Header
    st.markdown('<div class="main-header">🦯 BLINDSTICK LIVE MONITORING</div>', unsafe_allow_html=True)
    
    placeholder = st.empty()
    
    while True:
        with placeholder.container():
            data = get_data()
            
            # Top metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                status = data['system'].get('status', 'Unknown')
                if status == 'EMERGENCY':
                    st.markdown(f'<div class="status-emergency">🚨 {status}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="status-active">🟢 ACTIVE</div>', unsafe_allow_html=True)
            
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
            
            # Location Map
            col_map, col_info = st.columns([2, 1])
            
            with col_map:
                st.subheader("📍 Current Location")
                
                lat = data['location'].get('latitude', 2.0456)
                lon = data['location'].get('longitude', 102.5677)
                
                m = folium.Map(location=[lat, lon], zoom_start=16, tiles='OpenStreetMap')
                
                folium.Marker(
                    [lat, lon],
                    popup=f"User Location<br>Lat: {lat}<br>Lon: {lon}",
                    tooltip="Click for details",
                    icon=folium.Icon(color='red', icon='user', prefix='fa')
                ).add_to(m)
                
                folium.Circle([lat, lon], radius=50, color='blue', fill=True, opacity=0.2).add_to(m)
                
                st_folium(m, width=700, height=400)
                st.caption(f"📍 Coordinates: {lat:.6f}, {lon:.6f}")
                st.caption(f"🏢 Address: {data['location'].get('address', 'Loading...')}")
            
            with col_info:
                st.subheader("🚨 Alert Status")
                alert_status = data['alerts'].get('status', 'SAFE')
                alert_time = data['alerts'].get('timestamp', 'N/A')
                
                if alert_status == 'EMERGENCY':
                    st.markdown('<div class="alert-box alert-emergency">🔴 <b>EMERGENCY ACTIVE</b><br>Immediate attention required!</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="alert-box alert-info">🟢 <b>NO EMERGENCY</b><br>System operating normally</div>', unsafe_allow_html=True)
                
                st.caption(f"Last Alert: {alert_time}")
                
                st.divider()
                
                st.subheader("📊 Obstacle Detection")
                distance = data['sensors'].get('distance', 0)
                progress = max(0, min(100, (distance / 100) * 100))
                st.progress(progress / 100)
                st.metric("Distance", f"{distance} cm")
                
                if distance < 30:
                    st.warning("⚠️ Obstacle nearby!")
                else:
                    st.success("✅ Clear path")
                
                alerts_today = data['sensors'].get('alert_count', 0)
                st.metric("Alerts Today", alerts_today)
            
            st.divider()
            
            # Activity Chart
            st.subheader("📈 Activity Chart (Last 24 Hours)")
            hours = [f"{i:02d}:00" for i in range(0, 24, 2)]
            alerts = [5, 8, 3, 12, 7, 15, 9, 11, 6, 4, 8, 10]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hours,
                y=alerts,
                mode='lines+markers',
                name='Obstacle Alerts',
                line=dict(color='#667eea', width=3),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                xaxis_title="Time",
                yaxis_title="Alert Count",
                height=300,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.divider()
            
            # Recent Alerts
            st.subheader("📜 Recent Alerts")
            recent_alerts = data['alerts'].get('history', [])
            sample_alerts = [
                {'time': '14:35', 'type': 'emergency', 'msg': 'Emergency Button Pressed'},
                {'time': '14:20', 'type': 'warning', 'msg': 'Obstacle Warning (15cm)'},
                {'time': '14:10', 'type': 'info', 'msg': 'System Status Check OK'},
                {'time': '13:55', 'type': 'warning', 'msg': 'Obstacle Warning (22cm)'},
            ]
            
            for alert in sample_alerts:
                alert_class = f"alert-{alert['type']}"
                icon = '🔴' if alert['type']=='emergency' else '🟡' if alert['type']=='warning' else '🟢'
                st.markdown(f'<div class="alert-box {alert_class}">{icon} <b>{alert["time"]}</b> - {alert["msg"]}</div>', unsafe_allow_html=True)
        
        time.sleep(2)

if __name__ == "__main__":
    main()
