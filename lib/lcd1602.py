import machine
import time

"""
    Modified: Feb. 27, 2022  by: DDG
    Add __init__ parms for pin_sda, pin_scl
    to allow using different pins.
    Default is same as before.
    
"""

class LCD():
    def __init__(self, addr=0x27, blen=1, pin_sda=0, pin_scl=1):
        sda = machine.Pin(pin_sda)
        scl = machine.Pin(pin_scl)
        self.bus = machine.I2C(0,sda=sda, scl=scl, freq=400000)
        #print(self.bus.scan())
        self.addr = addr
        self.blen = blen
        self.send_command(0x33) # Must initialize to 8-line mode at first
        time.sleep(0.005)
        self.send_command(0x32) # Then initialize to 4-line mode
        time.sleep(0.005)
        self.send_command(0x28) # 2 Lines & 5*7 dots
        time.sleep(0.005)
        self.send_command(0x0C) # Enable display without cursor
        time.sleep(0.005)
        self.send_command(0x01) # Clear Screen
        self.bus.writeto(self.addr, bytearray([0x08]))

    def write_word(self, data):
        temp = data
        if self.blen == 1:
            temp |= 0x08
        else:
            temp &= 0xF7
            
        self.bus.writeto(self.addr, bytearray([temp]))
        
    def send_command(self, cmd):
        # Send bit7-4 firstly
        buf = cmd & 0xF0
        buf |= 0x04 # RS = 0, RW = 0, EN = 1
        self.write_word(buf)
        time.sleep(0.002)
        buf &= 0xFB # Make EN = 0
        self.write_word(buf)
        # Send bit3-0 secondly
        buf = (cmd & 0x0F) << 4
        buf |= 0x04 # RS = 0, RW = 0, EN = 1
        self.write_word(buf)
        time.sleep(0.002)
        buf &= 0xFB # Make EN = 0
        self.write_word(buf)
        
    def send_data(self, data):
        # Send bit7-4 firstly
        buf = data & 0xF0
        buf |= 0x05 # RS = 1, RW = 0, EN = 1
        self.write_word(buf)
        time.sleep(0.002)
        buf &= 0xFB # Make EN = 0
        self.write_word(buf)
        # Send bit3-0 secondly
        buf = (data & 0x0F) << 4
        buf |= 0x05 # RS = 1, RW = 0, EN = 1
        self.write_word(buf)
        time.sleep(0.002)
        buf &= 0xFB # Make EN = 0
        self.write_word(buf)
        
    def clear(self):
        self.send_command(0x01) # Clear Screen
        
    def openlight(self): # Enable the backlight
        self.bus.writeto(self.addr,bytearray([0x08]))
        # self.bus.close()
        
    def write(self, x, y, str):
        if x < 0:
            x = 0
        if x > 15:
            x = 15
        if y < 0:
            y = 0
        if y > 1:
            y = 1
            
        # Move cursor
        addr = 0x80 + 0x40 * y + x
        self.send_command(addr)
        
        for chr in str:
            self.send_data(ord(chr))
            
    def message(self, text):
        #print("message: %s"%text)
        for char in text:
            if char == '\n':
                self.send_command(0xC0) # next line
            else:
                self.send_data(ord(char))
                
    #
    # Added stuff
    #
    def closelight(self): # Disable the backlight
        self.bus.writeto(self.addr,bytearray([0x00]))
        # self.bus.close()
        
    def cursor_home(self):
        self.send_command(0x02)
        
    def set_cursor(self,x,y):
        addr = 0x80 + 0x40 * y + x
        self.send_command(addr)
        
    # blink x times
    # pausing blink_len seconds between off/on
    def blink(self,x,blink_len):
        for i in range(x):
            self.closelight()
            time.sleep(blink_len)
            self.openlight()
            time.sleep(blink_len)
