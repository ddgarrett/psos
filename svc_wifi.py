"""
    WiFi Class
    
    Class that contains WiFi connection
    (plus related methods?)
    
"""

from psos_svc import PsosService
import uasyncio
import secrets
import network
import time
import machine

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        self._station = network.WLAN(network.STA_IF)
    
        if self.get_parm("disconnect",True):
            if self._station.active() and self._station.isconnected():
                old = self._station.ifconfig()
                print("disconnecting from " + str(old))
                self._station.disconnect()
                time.sleep_ms(50) # wait for disconnect
                
        self.connect_wifi()
        while not self.wifi_connected():
            print(".",end="")
            time.sleep_ms(500)
    
        
    async def run(self):

        while True:
            if not self.wifi_connected():
                await self.reset()
            else:
                pass
                
            await uasyncio.sleep_ms(5000)
    
    
    def connect_wifi(self):
        
        if not self._station.active():
            self._station.active(True)
    
        if not self.wifi_connected():
            wifi_network = self.get_parm("wifi")
            
            wifi = secrets.wifi[wifi_network]
            ssid = wifi["ssid"]
            password = wifi["password"]
            
            print("connecting to network " + ssid)
            self._station.connect(ssid, password)
        else:
            print("already connected: " + str(self._station.ifconfig()))
        
    def wifi_connected(self):
        return self._station.isconnected()
        
        



