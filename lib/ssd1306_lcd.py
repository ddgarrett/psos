'''
    Wrapper for ssd1306 to emulate an LCD1602.
    
    Provides calls supported by pico_i2c_lcd.py, a subclass of lcd_api, including:
    - show_cursor
    - hide_cursor
    - blink_cursor_on
    - blink_cursor_off
    - backlight_on
    - backlight_off
    - display_on
    - display_off
    - def_special_char
    - putstr
    - move_to
    - clear

'''

from ssd1306 import SSD1306_I2C
import gfx

class I2cLcd(SSD1306_I2C):
    
    def __init__(self, i2c, i2c_addr, num_lines=4, num_columns=16,row_height=16,col_width=8):
        # mod_name,i2c,i2c_addr,self.lcd_row_cnt, self.lcd_col_cnt
        width = num_columns * col_width
        height = num_lines * row_height
        
        super().__init__(width, height, i2c, addr=i2c_addr)
        
        self.row_cnt = num_lines
        self.col_cnt = num_columns
        self.row_height = row_height
        self.col_width = col_width
        
        self.x = 0
        self.y = 0
        
        self.spc = {} # special character mapping
        
        self.gfx = gfx.GFX(width, height, self.pixel, vline=self.vline, hline=self.hline)
        
    def show_cursor(self):
        pass
    
    def hide_cursor(self):
        pass
    
    def blink_cursor_on(self):
        pass
    
    def blink_cursor_off(self):
        pass
    

    def backlight_on(self):
        super().poweron()
    
    def backlight_off(self):
        super().poweroff()
    
    def display_on(self):
        super().poweron()
    
    def display_off(self):
        super().poweroff()
    
    def def_special_char(self,utf8_char,charmap):
         self.spc[utf8_char] = charmap
        
    def putstr(self,string):
        for c in string:
            
            if c == '\n':
                self.y += 1
                self.x = -1
                
            if self.x < self.col_cnt and self.y < self.row_cnt:
                # blank out character
                w = self.col_width
                h = self.row_height
                self.gfx.fill_rect(self.x*w,self.y*h,w,h,0)
                
                if c in self.spc:
                    self.write_bits(self.spc[c])
                else:
                    px = self.x * self.col_width
                    py = self.y * self.row_height
                    super().text(c,px,py)
                    
            self.x += 1
    
        super().show()
        
    def zfl(self,s,width):
        # pad s with leading zeroes
        return '{:0>{w}}'.format(s,w=width)
    
    def write_bits(self,bmap):
        py = self.y * self.row_height - 1
        for b in bmap:
            py = py + 1
            px = self.x * self.col_width - 1
            bp = self.zfl(bin(b)[2:],7)
            for b2 in range(7):
                px = px + 1
                if bp[b2] == "1":
                    self.pixel(px,py,1)
                # else:
                #    self.pixel(px,py,0)
        
        
    def move_to(self,x,y):
        self.x = x
        self.y = y
    
    def get_cursor(self):
        return(self.x,self.y)
    
    def clear(self):
        super().fill(0)
        super().show()
        self.x = 0
        self.y = 0
        
     

        