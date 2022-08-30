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
import ntptime  # uses special version in lib

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
                
        # version 2 - connect to wifi during startup
        
        self.connect_wifi()
        while not self.wifi_connected():
            print(".",end="")
            time.sleep_ms(500)
            
        if self.get_parm("set_time",False):
            retry = 3
            while retry > 0:
                if self.set_time():
                    break
                else:
                    retry = retry - 1
                
            if retry <= 0:
                print("unable to set time")
    
        
    def set_time(self):
        try:
            ntptime.settime()
            return True
        except Exception as e:
            return False
        
        
    async def run(self):
        
        while True:
            if not self.wifi_connected():
                await self.reset()
                
            await uasyncio.sleep_ms(1000)
    
    
    def connect_wifi(self):
        
        if not self._station.active():
            self._station.active(True)
    
        if not self.wifi_connected():
            wifi_network = self.get_parm("wifi",None)
            
            if wifi_network == None:
                print("scanning network for options")
                wifi_network = self.scan_networks()
            
            wifi = secrets.wifi[wifi_network]
            ssid = wifi["ssid"]
            password = wifi["password"]
            
            print("connecting to network " + ssid)
            self._station.connect(ssid, password)
        else:
            print("already connected: " + str(self._station.ifconfig()))
        
    def wifi_connected(self):
        return self._station.isconnected()
    
    # Scan wifi network then compare to
    # to secrets.wifi_priority to find a recognized wifi network
    def scan_networks(self):
        nets = self._station.scan()
        
        for known in secrets.wifi_priority:
            known_ssid = secrets.wifi[known]["ssid"].encode()
            print("checking for ssid == ",known_ssid)
            for net in nets:
                ssid, bssid, channel, RSSI, authmode, hidden = net
                if known_ssid == ssid:
                    return known
                
        print("no known wifi networks found")
        return None
        
        
        



