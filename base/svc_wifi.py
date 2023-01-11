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
import utf8_char
import gc

# All initialization classes are named ModuleService
class ModuleService(PsosService):
    
    def __init__(self, parms):
        super().__init__(parms)
        
        self._station = network.WLAN(network.STA_IF)
        
        if self.get_parm("disconnect",True):
            if self._station.active() and self._station.isconnected():
                old = self._station.ifconfig()
                print("disconnecting from ",str(old))
                self._station.disconnect()
                time.sleep_ms(50) # wait for disconnect
                
        gc.collect()
        
    async def run(self):
        
        await self.reconnect_wifi()
        
        while True:
            if not self.wifi_connected():
                self.reset("wifi connection lost")
                # possible rp2 bug causing ENOMEM error
                # after a certain number of reconnects?
                # await self.reconnect_wifi()
                
            await uasyncio.sleep_ms(1000)
    
    async def reconnect_wifi(self):
        self.display_lcd_msg("WiFi connect...")
        self.connect_wifi()
        retry = 60 # try for max 30 seconds
        while not self.wifi_connected():
            print(".",end="")
            retry = retry - 1
            if retry <= 0:
                self.reset("unable to connect to wifi")
                #print("unable to connect to wifi")
                
                # wait 5 seconds before retrying
                # await uasyncio.sleep_ms(5000)
                # return
            await uasyncio.sleep_ms(500)
            
        await uasyncio.sleep_ms(0)
        
        if self.get_parm("set_time",True):
            retry = 3
            while retry > 0:
                self.display_lcd_msg("Setting time...")
                if self.set_time():
                    break
                else:
                    retry = retry - 1
                    await uasyncio.sleep_ms(500)
                    
            if retry <= 0:
                self.display_lcd_msg("Time not set")
                print("unable to set time")
            else:
                self.display_lcd_msg(self.get_dt().replace("\t","\n"))
                
    def set_time(self):
        try:
            ntptime.settime()
            return True
        except Exception as e:
            return False
        
    def connect_wifi(self):
        if not self._station.active():
            self._station.active(True)
    
        if not self._station.isconnected():
            wifi_network = self.get_parm("wifi",None)
            
            if wifi_network == None:
                print("scanning network for options")
                wifi_network = self.scan_networks()
            
            if wifi_network == None:
                # wait extra time for wifi network
                time.sleep_ms(5000)
                self.reset("no wifi network available")
                
            wifi = secrets.wifi[wifi_network]
            ssid = wifi["ssid"]
            password = wifi["password"]
            
            print("connecting to network " + ssid)
            self._station.connect(ssid, password)
        else:
            print("already connected: " + str(self._station.ifconfig()))
        
    def wifi_connected(self):
        if self.is_rp2():
            return (self._station.isconnected() and
                    self._station.status() == 3)
            
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