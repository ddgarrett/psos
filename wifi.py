import network
import secrets
import time

st = network.WLAN(network.STA_IF)

if st.isconnected():
    st.disconnect()
    
if not st.active():
    st.active(True)

wifi_network = "home"
            
wifi = secrets.wifi[wifi_network]
ssid = wifi["ssid"]
password = wifi["password"]

print("connecting to network " + ssid)
st.connect(ssid, password)

while not st.isconnected():
    print(".",end="")
    time.sleep_ms(500)

print("connected to ",st.ifconfig())
