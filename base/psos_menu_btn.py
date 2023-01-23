'''
    PSOS Touch Button
    
    Defines a Menu Button used by Svc Touch Menu class.

'''
import uasyncio
import color_brg_556 as clr

# Button Class
class Button():
    def __init__(self, panel,x,y):
        super().__init__()
        self.panel = panel
        self.x = x
        self.y = y
        self.title = []
        
        self.height = 40
        self.width  = 80
        self.selected = False
        
        self.parms = None
    
    def selectable(self):
        return len(self.title) > 0
    
    # set parms from a json menu entry
    def set_parms(self,parms):
        if parms == None:
            self.title = []
            self.parms = None
            return
        
        n = parms["name"]
        if type(n) == str:
            n = [n]
        self.title = n
            
        self.parms = parms
    
    def render(self,lcd):
        if len(self.title) > 0:
            c = clr.CYAN
            bg = clr.BLACK
            if self.selected:
                c = ~c
                bg = ~bg
            lcd.rect(self.x,self.y,self.width,self.height,c)
            lcd.fill_rect(self.x+1,self.y+1,self.width-2,self.height-2,bg)
            if len(self.title) == 1:
                pad_y = int(self.height/2-4)
                self.render_label(lcd,0,pad_y)
            else:
                pad_y = int(self.height/2-12)
                self.render_label(lcd,0,pad_y)
                self.render_label(lcd,1,pad_y+12)                
     
    def render_label(self,lcd,idx,y):
        c = clr.YELLOW
        if self.selected:
            c = ~c
        pw = len(self.title[idx])*8
        x = int((self.width-pw)/2)+self.x
        lcd.text(self.title[idx],x,y+self.y,c)
        
    async def select_btn(self,msg_q):
        if not self.selectable():
            return None
        if "select" in self.parms:
            msg = self.parms["select"]
            msg_q.append((msg[0],msg[1]))
            
        self.selected = True
        if "submenu" in self.parms:
            return self.parms["submenu"]
        
        return None   
    
    async def deselect_btn(self,msg_q):
        if self.parms == None:
            return
        if "deselect" in self.parms:
            msg = self.parms["deselect"]
            msg_q.append((msg[0],msg[1]))
            
        self.selected = False
