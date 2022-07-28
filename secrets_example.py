# Python secrets file.
# In .gitignore and therefore never sent to repo.

# MQTT certificates
from hivemq_root_ca import hivemq_root_ca

# wifi network connection priority
wifi_priority = ["wifi_esp","wifi_pixel","wifi_home"]

# WiFi environments
# Each environment includes MQTT broker connection priority
wifi =  {
    "wifi_home":{
        'ssid'     : 'xxxxx',
        'password' : 'xxxxx',
        'mqtt_priority' : ["mqtt_docker_home","mqtt_hivemq"]
        },
    "wifi_pixel":{
        'ssid'     : 'xxxxx',
        'password' : 'xxxxx',
        'mqtt_priority' : ["mqtt_docker_pixel","mqtt_hivemq"]
        },
    "wifi_esp" :{
        'ssid'     : 'xxxxx',
        'password' : 'xxxxx',
        'mqtt_priority' : ["mqtt_docker_esp"]
        }
    }

# MQTT environemts
# Note that docer server IP address may vary by wifi network
mqtt =  {
    "mqtt_docker_esp" :{
        'server' : 'xxxxx',
        'port'   : 1883,
        'username' : 'xxxxx',
        'password' : 'xxxxx'        },
    "mqtt_docker_pixel" :{
        'server' : 'xxxxx',
        'port'   : 1883,
        'username' : 'xxxxx',
        'password' : 'xxxxx'        },
    "mqtt_docker_home" :{
        'server' : 'xxxxx',
        'port'   : 1883,
        'username' : 'xxxxx',
        'password' : 'xxxxx'        },    
    "mqtt_hivemq" :{
        'server' : 'xxxxx.hivemq.cloud',
        'port'   : 8883,
        'username' : 'xxxxx',
        'password' : 'xxxxx',
        'ca_cert'  : hivemq_root_ca
        },
}

