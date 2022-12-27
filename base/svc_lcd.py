"""
    LCD Service
    
    Input sent via the topic defined by subscr_input 
    are used to generated commands related to the LCD.
    
    
    See svc_lcd_input.py for how to build input messages for this service.
    
    Accepts following commands:
        'clear'               clears LCD display and resets all cursors, etc.
        {'cursor':[x,y]}      sets cursor to x (column 0 thru ??), y (row = 0 or 1)
        {'backlight':1}       turns backlight on (1) or off (0)
        {'msg':'some text'}   displays 'some text'
    
    Examples:
    
       ['clear',{'msg':'Temp:'},{'cursor':[0,1]},{'msg':'Humidity:'}]
       
       [{'cursor':[6,0]},{'msg':' 69.9'},{'cursor':[10,1]},{'msg':'38'}]
       
       
    
"""
from psos_svc import PsosService

import utf8_char
import svc_lcd_msg

import queue
import uasyncio

# All services classes are named ModuleService
class ModuleService(PsosService):

    def __init__(self, parms):
        super().__init__(parms)
        
        self._subscr_topic = parms.get_parm("subscr_msg")
        self._trigger_q = queue.Queue()
        
        i2c_svc = parms.get_parm("i2c")
        i2c = self.get_svc(i2c_svc).get_i2c()
        
        i2c_addr         = int(self.get_parm("i2c_addr", "0x27"))
        self.lcd_row_cnt = int(self.get_parm("lcd_row_cnt", "2"))
        self.lcd_col_cnt = int(self.get_parm("lcd_col_cnt", "16"))

        # modify class to support different displays in addition to LCD1602
        # *** in particular, supports the SSD1306 OLED emulating an LCD1602
        # *** for SSD1306 use "disp_class":"ssd1306_lcd" in psos_parms.json
        mod_name = self.get_parm("disp_driver","pico_i2c_lcd") # default to LCD1602
        module = __import__(mod_name)
        self.lcd = module.I2cLcd(i2c,i2c_addr,self.lcd_row_cnt, self.lcd_col_cnt)
        
        self.backlight_on   = True
        self.blink_task     = None
        self.blink_interval = 0
        self.timeout        = parms.get_parm("timeout",0)
        self.to_remain      = self.timeout + 1
        
        self.hg_task_cnt    = 0
        self.sym            = parms.get_parm("sym","✗")
        self.lock_cnt       = 0
        
        # dictionary to execute commands
        self.cmd_lookup = {
            svc_lcd_msg.CMD_CLEAR_SCREEN : self.clear_screen,

            svc_lcd_msg.CMD_CURSOR_ON    : self.lcd.show_cursor,
            svc_lcd_msg.CMD_CURSOR_OFF   : self.lcd.hide_cursor,

            svc_lcd_msg.CMD_BLINK_CURSOR_ON  : self.lcd.blink_cursor_on,
            svc_lcd_msg.CMD_BLINK_CURSOR_OFF : self.lcd.blink_cursor_off,

            svc_lcd_msg.CMD_BACKLIGHT_ON  : self.lcd.backlight_on,
            svc_lcd_msg.CMD_BACKLIGHT_OFF : self.lcd.backlight_off,

            svc_lcd_msg.CMD_DISPLAY_ON  : self.lcd.display_on,
            svc_lcd_msg.CMD_DISPLAY_OFF : self.lcd.display_off,
            
            svc_lcd_msg.CMD_BLK_HG      : self.blank_hourglass
        }
        
        # Add any custom characters
        # Any custom characters must have a byte array
        # defined in utf8_char.py in the dictionary CUSTOM_CHARACTERS
        custom_char = self.get_parm("custom_char","")
        for char in custom_char:
            if char in utf8_char.CUSTOM_CHARACTERS:
                b_array = utf8_char.CUSTOM_CHARACTERS[char]
                self.lcd.def_special_char(char,b_array)
            else:
                print("customer char not found: ",char)
                
        self.lcd_msg = svc_lcd_msg.SvcLcdMsg()
        self.svc_lcd = self
        # self.display_lcd_msg("LCD initialized")
        
    # run forever, but only blink backlight if
    # blink_interval > 0
    async def blink_lcd(self):
        while True:
            while self.blink_interval > 0:
                self.set_backlight(False)
                await uasyncio.sleep_ms(int(self.blink_interval * 1000))
                self.set_backlight(True)
                await uasyncio.sleep_ms(int(self.blink_interval * 1000))
                
            await uasyncio.sleep_ms(500)
        
    # run forever, but only turn off backlight 
    # if timeout == 0
    async def timeout_backlight(self):
        while True:
            if self.timeout != 0 and self.to_remain > 0:
                self.to_remain = self.to_remain - 1
                if self.to_remain <= 0:
                     self.set_backlight(False)
                     
            await uasyncio.sleep_ms(1000)
        
    # called directly from other services to
    # lock or unlock use of this device
    def set_lock(self,v):
        if v:
            self.lock_cnt += 1
        else:
            if self.lock_cnt > 0:
                self.lock_cnt -= 1
    
    # set symbol displayed in lower right
    # called directly by other services
    def set_sym(self,s):
        if self.sym != s:
            self.sym = s
            self.blank_hourglass()
        
    def get_timeout(self):
        return self.timeout
    
    def set_timeout(self,v):
        self.timeout = v
        
    async def run(self):
        # Start the blink coroutine.
        # It won't do anything until blink_interval is set
        self.blink_task = uasyncio.create_task(self.blink_lcd())
        
        # Start the timeout coroutine.
        # It won't do anything until timeout count is < 0-
        self.timeout_task = uasyncio.create_task(self.timeout_backlight())
        
        # subscribe to topic and wait for messages
        mqtt = self.get_mqtt()
        await mqtt.subscribe(self._subscr_topic,self._trigger_q)
        
        while True:
            q = await self._trigger_q.get()
            
            # throw away any queued input while display is locked
            if self.lock_cnt <= 0:
                self.lcd_msg.load_subscr(q)                
                self.process_msg(self.lcd_msg)
                    
    def process_msg(self, msg):
        
        if not self.backlight_on:
            self.set_backlight(True)
            
        if self.timeout > 0:
            self.to_remain = self.timeout + 1
            
        payload = msg.get_payload()
        
        if isinstance(payload,list):
            for command in payload:
                self.process_command(command)
        else:
            self.process_command(payload)
            
    def process_command(self, command):
        if isinstance(command,str):
            if command in self.cmd_lookup:
                self.cmd_lookup[command]()
            else:
                # log error: invalid command?
                print("unrecognized payload: "+command)
                # pass
        elif isinstance(command,dict):
            for key in command:
                if key == 'msg':
                    self.lcd.putstr(command[key])
                elif key == 'cursor':
                    self.set_cursor(command[key])
                elif key == 'backlight':
                    self.set_backlight(command[key])
                elif key == 'blink_backlight':
                    self.blink_interval = command[key]
                elif key == svc_lcd_msg.CMD_DSP_HG:
                    self.dsp_hg(command[key])
                else:
                    # log error in dictionary command
                    pass
        else:
            # log error in command type?
            pass
        
    def set_cursor(self, xy):
        if (isinstance(xy,list) or isinstance(xy,tuple)) and len(xy) == 2:
            x = xy[0]
            y = xy[1]
            
            if isinstance(x,int) and isinstance(y,int):
                self.lcd.move_to(x,y)
                return
        else:
            print("unrecognized xy:",xy)
            
        # log error in cursor command?
                
    def set_backlight(self, value):
        if value:
            self.lcd.backlight_on()
            self.backlight_on = True
        else:
            self.lcd.backlight_off()
            self.backlight_on = False
            
    # make sure that when we clear the screen
    # we reset the display, backlight and cursor
    def clear_screen(self):
        self.lcd.clear()
        self.set_backlight(True)
        self.lcd.display_on()
        self.lcd.blink_cursor_off()
        self.lcd.hide_cursor()
        self.blink_interval = 0
        self.blank_hourglass()
        
        
    # display the hourglass symbole for given period of time
    def dsp_hg(self,time):
        self.hg_task_cnt += 1
        self.hg_task = uasyncio.create_task(self.dsp_hg_tsk(time))
        
    async def dsp_hg_tsk(self,time):
        x,y = self.lcd.get_cursor()
        row = self.lcd_row_cnt-1
        col = self.lcd_col_cnt-1
        
        self.set_cursor((col,row))
        self.lcd.putstr(utf8_char.SYM_HOUR_GLASS)
        self.set_cursor((x,y))
        await uasyncio.sleep_ms(int(time* 1000))
        
        # ensure no other hg tasks are running
        self.hg_task_cnt -= 1
        if self.hg_task_cnt == 0:
            self.blank_hourglass()
            
    def blank_hourglass(self):
        x,y = self.lcd.get_cursor()
        row = self.lcd_row_cnt-1
        col = self.lcd_col_cnt-1
        
        self.set_cursor((col,row))
        self.lcd.putstr(self.sym)
        self.set_cursor((x,y))
        
    def write_direct(self,payload):
        self.lcd_msg.set_payload(payload)
        self.process_msg(self.lcd_msg)
