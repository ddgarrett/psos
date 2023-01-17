'''
    3.5 inch IPS LCD from Waveshare
    
    Represents a single subpane in the entire LCD.
    To use,
        - LCD(width,height)
        - set_view(x,y)
            - to specify where the (0,0) point is on LCD
            
        - usual commands such as
            - fill(c)
            - rect(x,y,width,height,c)
            - fill_rect(x,y,width,height,c)
            - text(str,x,y,c)
    
    virtual_lcd.py class VLCD suppports rendering the entire 3.5" LCD
    one subpane at a time. That class calls the show_page(x,y) method to render
    the buffer at a particular point on the LCD.
    
    This is done because the full 480x320 pixel LCD would require a buffer that
    is 480 * 320 * 2 bytes long = 307,200 bytes. By breaking this up into, for example,
    12 different views, each 160x80, we use only 25,600 bytes for the buffer.
    
'''
from machine import Pin,SPI,PWM
import framebuf
import time
import os
from micropython import const
import micropython
import gc

from gfx import GFX

from sys import byteorder

_VER  = const("0.3")
print('running 3.5" LCD v{}'.format(_VER))

LCD_DC   = const(8)
LCD_CS   = const(9)
LCD_SCK  = const(10)
LCD_MOSI = const(11)
LCD_MISO = const(12)
LCD_BL   = const(13)
LCD_RST  = const(15)
TP_CS    = const(16)
TP_IRQ   = const(17)

class LCD(framebuf.FrameBuffer):

    def __init__(self,width,height):
        self.width = width
        self.height = height

        self.cs = Pin(LCD_CS,Pin.OUT)
        self.rst = Pin(LCD_RST,Pin.OUT)
        self.dc = Pin(LCD_DC,Pin.OUT)
        
        self.tp_cs =Pin(TP_CS,Pin.OUT)
        self.irq = Pin(TP_IRQ,Pin.IN)
        
        self.cs(1)
        self.dc(1)
        self.rst(1)
        self.tp_cs(1)
        self.spi = SPI(1,60_000_000,sck=Pin(LCD_SCK),mosi=Pin(LCD_MOSI),miso=Pin(LCD_MISO))
        
        gc.collect()
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        self.init_display()

        
    def write_cmd(self, cmd):
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        if type(buf) == int:
            buf = bytearray([buf])
        if type(buf) == list:
            for b in buf:
                self.write_bytearray(bytearray([b]))
            return
        
        self.write_bytearray(buf)
         
    def write_bytearray(self,buf):
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(buf)
        self.cs(1)

    def init_display(self):
        """Initialize display"""  
        self.rst(1)
        time.sleep_ms(5)
        self.rst(0)
        time.sleep_ms(10)
        self.rst(1)
        time.sleep_ms(5)
        
        self.write_cmd(0x21)  # Inversion on
        self.write_cmd(0xC2)  # Power control 4 (normal mode)
        self.write_data(0x33) # - cmd data (step up cycle)
        
        self.write_cmd(0xB1)  # Frame rate control
        self.write_data(0xB0) # - parm
        
        self.write_cmd(0X3A)   # Pixel format
        self.write_data(0x55)  # 16 bits/pixel
        
        self.write_cmd(0x11)   # Sleep out - turn off sleep mode
        time.sleep_ms(120)     # wait for wakeup
        
        self.write_cmd(0x29)   # Display On
        
        self.write_cmd(0xB6)   # Display Function Control
        self.write_data(0x00)
        self.write_data(0x62)
        
        self.write_cmd(0x36)   # Memory access control (p. 191) (second one)
        self.write_data(0x28)  # - parm 2=row/col exchange, 8=BRG vs RBG order
        
        gc.collect()
    
    def show_pg(self,x,y):
        c_start = x * self.width
        c_end   = c_start + self.width - 1
        
        # convert two int to four bytes
        col = self.shift(c_start)
        col.extend(self.shift(c_end))
        
        self.write_cmd(0x2A)   # column start address - frame memory MCU can access
        self.write_data(col)   # write the four bytes
        
        r_start = y * self.height
        r_end   = r_start + self.height - 1
        
        # convert two int to four bytes
        row = self.shift(r_start)
        row.extend(self.shift(r_end))

        self.write_cmd(0x2B)   # page (row) address set - frame memory MCU can access
        self.write_data(row)   # write four bytes
        
        self.write_cmd(0x2C)   # Memory write
        
        self.write_bytearray(self.buffer) # write the entire buffer to LCD
        
        gc.collect()
        
    def bl_ctrl(self,duty):
        pwm = PWM(Pin(LCD_BL))
        pwm.freq(1000)
        if(duty>=100):
            pwm.duty_u16(65535)
        else:
            pwm.duty_u16(655*duty)
        
    def touch_get(self): 
        if self.irq() == 0:
            gc.collect()
            self.spi = SPI(1,5_000_000,sck=Pin(LCD_SCK),mosi=Pin(LCD_MOSI),miso=Pin(LCD_MISO))
            self.tp_cs(0)
            X_Point = 0
            Y_Point = 0
            for i in range(0,3):
                self.spi.write(bytearray([0XD0]))
                Read_date = self.spi.read(2)
                # print("x:",Read_date[0],Read_date[1],end="  ")
                time.sleep_us(10)
                X_Point=X_Point+(((Read_date[0]<<8)+Read_date[1])>>3)
                
                self.spi.write(bytearray([0X90]))
                Read_date = self.spi.read(2)
                # print("y:",Read_date[0],Read_date[1])
                Y_Point=Y_Point+(((Read_date[0]<<8)+Read_date[1])>>3)

            X_Point=X_Point/3
            Y_Point=Y_Point/3
            
            self.tp_cs(1) 
            self.spi = SPI(1,60_000_000,sck=Pin(LCD_SCK),mosi=Pin(LCD_MOSI),miso=Pin(LCD_MISO))
            Result_list = [X_Point,Y_Point]
            # print(Result_list)
            gc.collect()
            return(Result_list)
        
    def blink(self):
        for i in range(5):
            LCD.write_cmd(0x20)  # Inversion off
            time.sleep(.5)
            LCD.write_cmd(0x21)  # Inversion on
            time.sleep(.5)
            
    # shift an int 1 byte to the right
    # returning the lowerst order byte
    def shift(self,n):
        return [(n >> 8), (n & 0xff)]

