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
                # TODO: write out special character bit map
                if c in self.spc:
                    px = self.x * self.col_width
                    py = self.y * self.row_height
                    super().text("*",px,py)
                else:
                    px = self.x * self.col_width
                    py = self.y * self.row_height
                    super().text(c,px,py)
                    
            self.x += 1
    
        super().show()
        
    def move_to(self,x,y):
        self.x = x
        self.y = y
    
    def clear(self):
        super().fill(0)
        super().show()
        self.x = 0
        self.y = 0
        
     

        