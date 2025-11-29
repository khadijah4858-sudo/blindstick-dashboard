import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
from datetime import datetime
import json

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
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
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
        color: #1a1a1a;
        font-weight: 500;
    }
    .alert-emergency {
        background: #ffebee;
        border-left: 4px solid #f44336;
        color: #c62828;
    }
    .alert-warning {
        background: #fff3e0;
        border-left: 4px solid #ff9800;
        color: #e65100;
    }
    .alert-info {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
        color: #0d47a1;
    }
    .alert-box b {
        color: inherit;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Firebase with Streamlit Secrets
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        try:
            # Try to load from Streamlit secrets (for cloud deployment)
            firebase_config = dict(st.secrets["firebase"])
            cred = credentials.Certificate(firebase_config)
        except:
            # Fallback to local file (for local testing)
            cred = credentials.Certificate("blindstick-fyp-firebase-adminsdk.json")
        
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://blindstick-fyp-default-rtdb.asia-southeast1.firebasedatabase.app'
        })
    return db.reference()

# Get realtime data
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
        st.error(f"Firebase connection error: {e}")
        # Return dummy data for testing
        return {
            'location': {'latitude': 2.0456, 'longitude': 102.5677, 'address': 'UiTM Melaka (Demo Data)'},
            'alerts': {'status': 'SAFE', 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            'sensors': {'distance': 50, 'alert_count': 8},
            'system': {'status': 'ACTIVE', 'battery': 85, 'signal': 'Strong'}
        }

# Main dashboard
def main():
    # Header
    st.markdown('<div class="main-header">🦯 BLINDSTICK LIVE MONITORING</div>', unsafe_allow_html=True)
    
    # Auto-refresh button
    col_refresh, col_mode = st.columns([1, 4])
    with col_refresh:
        if st.button("🔄 Refresh Data"):
            st.rerun()
    
    with col_mode:
        auto_refresh = st.checkbox("Auto-refresh (every 5s)", value=False)
    
    # Get data
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
        st.metric("🔋 Battery", f"{battery}%", 
                  delta=f"{battery-80}%" if battery > 80 else f"{battery-80}%")
    
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
            popup=f"<b>User Location</b><br>Lat: {lat}<br>Lon: {lon}",
            tooltip="Blind Stick User",
            icon=folium.Icon(color='red', icon='info-sign')
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
        st.progress(progress / 100, text=f"Distance: {distance} cm")
        
        if distance < 30:
            st.warning("⚠️ Obstacle nearby!")
        elif distance < 50:
            st.info("ℹ️ Caution zone")
        else:
            st.success("✅ Clear path")
        
        alerts_today = data['sensors'].get('alert_count', 0)
        st.metric("Alerts Today", alerts_today)
    
    st.divider()
    
    # Activity Chart
    col_chart, col_stats = st.columns([3, 1])
    
    with col_chart:
        st.subheader("📈 Activity Chart (Last 24 Hours)")
        hours = [f"{i:02d}:00" for i in range(0, 24, 2)]
        
        # Try to get real data from Firebase, fallback to demo
        try:
            alerts_data = data.get('activity', {}).get('hourly_alerts', [5, 8, 3, 12, 7, 15, 9, 11, 6, 4, 8, 10])
        except:
            alerts_data = [5, 8, 3, 12, 7, 15, 9, 11, 6, 4, 8, 10]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hours,
            y=alerts_data,
            mode='lines+markers',
            name='Obstacle Alerts',
            line=dict(color='#667eea', width=3),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(102, 126, 234, 0.2)'
        ))
        
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Alert Count",
            height=300,
            hovermode='x unified',
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col_stats:
        st.subheader("📊 Statistics")
        st.metric("Total Alerts", sum(alerts_data) if isinstance(alerts_data, list) else 0)
        st.metric("Peak Hour", "12:00" if isinstance(alerts_data, list) else "N/A")
        st.metric("Avg/Hour", f"{sum(alerts_data)/len(alerts_data):.1f}" if isinstance(alerts_data, list) else "N/A")
    
    st.divider()
    
    # Recent Alerts
    st.subheader("📜 Recent Alerts")
    
    # Try to get real alerts from Firebase
    try:
        recent_alerts = data['alerts'].get('history', [])
        if not recent_alerts or len(recent_alerts) == 0:
            raise Exception("No data")
    except:
        # Fallback demo data
        recent_alerts = [
            {'time': datetime.now().strftime("%H:%M"), 'type': 'info', 'msg': 'System Online - Demo Mode'},
            {'time': '14:35', 'type': 'warning', 'msg': 'Obstacle Warning (25cm)'},
            {'time': '14:20', 'type': 'warning', 'msg': 'Obstacle Warning (15cm)'},
            {'time': '14:10', 'type': 'info', 'msg': 'System Status Check OK'},
        ]
    
    for alert in recent_alerts:
        alert_type = alert.get('type', 'info')
        alert_class = f"alert-{alert_type}"
        icon = '🔴' if alert_type=='emergency' else '🟡' if alert_type=='warning' else '🟢'
        st.markdown(
            f'<div class="alert-box {alert_class}">{icon} <b>{alert["time"]}</b> - {alert["msg"]}</div>', 
            unsafe_allow_html=True
        )
    
    # Footer info
    st.divider()
    col_footer1, col_footer2, col_footer3 = st.columns(3)
    with col_footer1:
        st.info("💡 **Tip:** Enable auto-refresh for live monitoring")
    with col_footer2:
        st.info("🔗 **Share:** Send this URL to caregivers")
    with col_footer3:
        st.info("📱 **Mobile:** Works on all devices")
    
    # Auto-refresh logic
    if auto_refresh:
        import time
        time.sleep(5)
        st.rerun()

if __name__ == "__main__":
    main()