# psos
Publish / Subscribe based OS.

Instead of using queues and I2C to communicate between different microcontrollers, as MBOS did, use MQTT messages which can be sent and received over a local area network or the world wide web. MQTT uses a lightweight (compared to HTTP) protocol running under TCP/IP. It includes protocols that can guarantee delivery to clients which subscribe to topics.

# Release 0.0.1
This first release is very lightweight. It is able to run on ESP8266 which implements WiFi and a TCP/IP stack, along with Micropython. The public MQTT broker, HiveMQ, uses TLS (the succssor to SSL) plus usernames and passwords to assure secure communications across the internet.

- Free HiveMQ server for publicly accessible MQTT broker
- Local Area Network docker based Mosquitto MQTT broker
- Node-Red Server running from docker container to monitor messages and generate MQTT messages


