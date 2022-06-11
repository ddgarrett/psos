"""
    Define Names for UTF-8 Special Characters
    
    Currently used primarily for IR Remote transmitter keypads.

"""
KEY_FAST_FORWARD      = "⏩"
KEY_REWIND_FAST_BACK  = "⏪"
KEY_FAST_INCREASE     = "⏫"
KEY_FAST_DECREASE     = "⏬"
KEY_SKIP_TO_END_NEXT  = "⏭" 
KEY_SKIP_TO_START_PREV = "⏮"
KEY_PLAY_PAUSE_TOGGLE = "⏯"
KEY_STOPWATCH         = "⏱"
KEY_TIMER_CLOCK       = "⏲"
KEY_HOUR_GLASS        = "⏳"
KEY_REVERSE_BACK      = "⏴"
KEY_FORWARD_NEXT_PLAY = "⏵" 
KEY_INCREASE          = "⏶"
KEY_DECREASE          = "⏷"
KEY_PAUSE             = "⏸"
KEY_STOP              = "⏹" 
KEY_RECORD            = "⏺"
KEY_POWER_OFF         = "⭘"
KEY_OK                = ""

KEY_VOLUME_UP         = "🔊"
KEY_VOLUME_DOWN       = "🔉"

KEY_DEGREES_SYMBOL    = "°"

SYM_HOUR_GLASS            = "⌛"


# Keys that scroll up and down between apps
KEYS_NAVIGATE = [KEY_INCREASE, KEY_DECREASE]

KEYS_FORWARD_REVERSE = [
    KEY_REVERSE_BACK,
    KEY_FORWARD_NEXT_PLAY,
    KEY_OK ]

KEYS_NUMERIC = [
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    KEY_REVERSE_BACK,
    KEY_FORWARD_NEXT_PLAY,
    KEY_OK]

KEYS_NON_ZERO_NUMERIC = [
    "1", "2", "3", "4", "5", "6", "7", "8", "9",
    KEY_REVERSE_BACK,
    KEY_FORWARD_NEXT_PLAY,
    KEY_OK]


CUSTOM_CHARACTERS = {
    KEY_DEGREES_SYMBOL : [
        0b01100,
        0b10010,
        0b10010,
        0b01100,
        0b00000,
        0b00000,
        0b00000,
        0b00000
    ],
    
    KEY_REVERSE_BACK : [
        0b00010,
        0b00110,
        0b01110,
        0b11110,
        0b01110,
        0b00110,
        0b00010,
        0b00000
    ],

    KEY_FORWARD_NEXT_PLAY : [
        0b01000,
        0b01100,
        0b01110,
        0b01111,
        0b01110,
        0b01100,
        0b01000,
        0b00000
    ],
    
    KEY_INCREASE : [
        0b00000,
        0b00000,
        0b00100,
        0b01110,
        0b11111,
        0b00000,
        0b00000,
        0b00000
    ],

    KEY_DECREASE : [
        0b00000,
        0b00000,
        0b11111,    
        0b01110,
        0b00100,
        0b00000,
        0b00000,
        0b00000 
    ],
    
    SYM_HOUR_GLASS :[
        
        0b11111,
        0b11111,
        0b01110,
        0b00100,
        0b00100,
        0b01010,
        0b10001,
        0b11111
    ]

}

