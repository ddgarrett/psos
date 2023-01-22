'''
    PSOS Touch Button
    
    Defines a Menu Button used by Svc Touch Menu class.

'''
import color_brg_556 as clr

# Button Class
class Button():
    def __init__(self, lcd,panel,x,y,title,select=False):
        super().__init__()
        self.lcd = lcd
        self.panel = panel
        self.x = x
        self.y = y
        self.title = title
        
        self.select_act = None
        self.deselect_act = None

        self.height = 40
        self.width  = 80
        self.select = select
            
    def render(self):
        if len(self.title) > 0:
            c = clr.CYAN
            bg = clr.BLACK
            if self.select:
                c = ~c
                bg = ~bg
            self.lcd.rect(self.x,self.y,self.width,self.height,c)
            self.lcd.fill_rect(self.x+1,self.y+1,self.width-2,self.height-2,bg)
            if len(self.title) == 1:
                pad_y = int(self.height/2-4)
                self.rend_label(0,pad_y)
            else:
                pad_y = int(self.height/2-12)
                self.rend_label(0,pad_y)
                self.rend_label(1,pad_y+12)                
     
    def rend_label(self,idx,y):
        c = clr.YELLOW
        if self.select:
            c = ~c
        pw = len(self.title[idx])*8
        x = int((self.width-pw)/2)+self.x
        self.lcd.text(self.title[idx],x,y+self.y,c)
        
    def select(self):
        if self.select_act != None:
            pass
    
    def deselect(self):
        if self.deselect_act != None:
            pass
