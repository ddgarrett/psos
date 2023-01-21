'''
    3.5 inch IPS LCD from Waveshare - Touch Part of Interface
    
    
'''
from machine import Pin,SPI,PWM
import framebuf
import time
import os
import micropython
import gc
import uasyncio


'''
LCD_DC   = const(8)
LCD_CS   = const(9)
LCD_SCK  = const(10)
LCD_MOSI = const(11)
LCD_MISO = const(12)
LCD_BL   = const(13)
LCD_RST  = const(15)
'''
TP_CS    = const(16)
TP_IRQ   = const(17)

class Touch():

    def __init__(self,spi_svc):
        
        self.tp_cs =Pin(TP_CS,Pin.OUT)
        self.irq = Pin(TP_IRQ,Pin.IN)
        
        self.tp_cs(1)
        
        self.spi_svc = spi_svc
        self.spi = spi_svc.get_spi()

        
        gc.collect()
        
    async def get_touch(self): 
        if self.irq() == 0:
            gc.collect()
            
            await self.spi_svc.lock()
            
            # self.spi = await self.spi_svc.set_spi(5_000_000,LCD_SCK,LCD_MOSI,LCD_MISO)
            # self.spi = SPI(1,5_000_000,sck=Pin(LCD_SCK),mosi=Pin(LCD_MOSI),miso=Pin(LCD_MISO))
            
            self.tp_cs(0)
            X_Point = 0
            Y_Point = 0
            for i in range(0,3):
                self.spi.write(bytearray([0XD0]))
                read_data = self.spi.read(2)
                # print("x:",Read_date[0],Read_date[1],end="  ")
                time.sleep_us(10)
                Y_Point=Y_Point+(((read_data[0]<<8)+read_data[1])>>3)
                
                self.spi.write(bytearray([0X90]))
                read_data = self.spi.read(2)
                # print("y:",Read_date[0],Read_date[1])
                X_Point=X_Point+(((read_data[0]<<8)+read_data[1])>>3)

            X_Point=X_Point/3
            Y_Point=Y_Point/3
            
            self.tp_cs(1)
            
            # resets spi to previous settings and unlocks spi
            self.spi_svc.unlock()
            # self.spi_svc.reset()
            # self.spi = SPI(1,60_000_000,sck=Pin(LCD_SCK),mosi=Pin(LCD_MOSI),miso=Pin(LCD_MISO))
            
            Result_list = [X_Point,Y_Point]
            # print(Result_list)
            gc.collect()
            return(Result_list)
        
