# PSOS
Publish / Subscribe OS (PSOS) is a framework that supports incremental development of complex microcontroller systems using simple MicroPython modules. Key features include:
- Simple to learn and use
- Easily extensible through simple to develop reusable modules
- Low overhead

PSOS uses the [uasyncio](https://docs.micropython.org/en/latest/library/uasyncio.html) library. This supports cooperative multitasking through coroutines that are both simple to learn and use as well as low overhead.

The publish/subscribe functionality is supported using [MQTT](https://en.wikipedia.org/wiki/MQTT) a "lightweight, easy to use machine to machine network protocol." Although MQTT was developed primarily for communication between devices, PSOS also uses it to communicate between coroutines on a single microcontroller. The result is a flexible topology that allows services to run independently of where related services are physically located allowing the redistribution of services to where the most resources are available.

An MQTT related technology, [Node-RED](https://en.wikipedia.org/wiki/Node-RED), is also a major influence on PSOS. As described in the linked to Wikipedia article

> Node-RED is a flow-based development tool.. for wiring together hardware devices, APIs and online services as part of the Internet of Things... 
>Elements of applications can be saved or shared for re-use. The runtime is built on Node.js. The flows created in Node-RED are stored using JSON

Although PSOS uses MicroPython instead of JavaScript, and is not developed via a visual UI like Node-RED, it does store the system definition in JSON and uses an Application Programming Interface (API) that is sometimes similar to Node-RED. 

There is a major difference though in that PSOS does not require a central server to run the defined modules. Instead services are distributed over one or more microcontrollers in the MQTT network.

# Release 0.0.1
This first release is very lightweight. It is able to run on ESP8266 which implements WiFi and a TCP/IP stack, along with Micropython. The public MQTT broker, HiveMQ, uses TLS (the succssor to SSL) plus usernames and passwords to assure secure communications across the internet.

- Free HiveMQ server for publicly accessible MQTT broker
- Local Area Network docker based Mosquitto MQTT broker
- Node-Red Server running from docker container to monitor messages and generate MQTT messages


