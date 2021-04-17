
WINDOWS_KEY_SET = {
    'LBUTTON': 1,   # Left mouse button
    'RBUTTON': 2,   # Right mouse button
    'CANCEL': 3,    # Control-break processing
    'MBUTTON': 4,   # Middle mouse button (three-button mouse)
    'XBUTTON1': 5,  # X1 mouse button
    'XBUTTON2': 6,  # X2 mouse button

    'BACK': 8,      # BACKSPACE key
    'BACKSPACE': 8, # BACKSPACE key
    'TAB': 9,       # TAB key
    'CLEAR': 12,    # CLEAR key
    'ENTER': 13,    # ENTER key
    'SHIFT': 16,    # SHIFT key
    'CONTROL': 17,  # CTRL key
    'ALT': 18,      # ALT key
    'PAUSE': 19,    # PAUSE key
    'CAPS': 20,     # CAPS LOCK key

    'KANA': 21,     # IME Kana mode
    'HANGUEL': 21,  # IME Hanguel mode (maintained for compatibility; use VK_HANGUL)
    'HANGUL': 21,   # IME Hangul mode
    'JUNJA': 23,    # IME Junja mode
    'FINAL': 24,    # IME final mode
    'HANJA': 25,    # IME Hanja mode
    'KANJI': 25,    # IME Kanji mode

    'CONVERT': 28,     # IME convert
    'NONCONVERT': 29,  # IME nonconvert
    'ACCEPT': 30,      # IME accept
    'MODECHANGE': 31,  # IME mode change request

    'ESCAPE': 27,    # ESC key
    'ESC': 27,       # ESC key
    'SPACE': 32,     # Пробел
    'PRIOR': 33,     # PAGE UP key
    'NEXT': 34,      # PAGE DOWN key
    'END': 35,       # END key
    'HOME': 36,      # HOME key
    'LEFT': 37,      # LEFT ARROW key
    'UP': 38,        # UP ARROW key
    'RIGHT': 39,     # RIGHT ARROW key
    'DOWN': 40,      # DOWN ARROW key
    'SELECT': 41,    # SELECT key
    'PRINT': 42,     # PRINT key
    'EXECUTE': 43,   # EXECUTE key
    'SNAPSHOT': 44,  # PRINT SCREEN key
    'INSERT': 45,    # INS key
    'DELETE': 46,    # DEL key
    'DEL': 46,       # DEL key
    'HELP': 47,      # HELP key

    '0': 48,  # 0 key
    '1': 49,  # 1 key
    '2': 50,  # 2 key
    '3': 51,  # 3 key
    '4': 52,  # 4 key
    '5': 53,  # 5 key
    '6': 54,  # 6 key
    '7': 55,  # 7 key
    '8': 56,  # 8 key
    '9': 57,  # 9 key
    'A': 65,
    'B': 66,
    'C': 67,
    'D': 68,
    'E': 69,
    'F': 70,
    'G': 71,
    'H': 72,
    'I': 73,
    'J': 74,
    'K': 75,
    'L': 76,
    'M': 77,
    'N': 78,
    'O': 79,
    'P': 80,
    'Q': 81,
    'R': 82,
    'S': 83,
    'T': 84,
    'U': 85,
    'V': 86,
    'W': 87,
    'X': 88,
    'Y': 89,
    'Z': 90,

    'LWIN': 91,        # Left Windows key (Natural keyboard)
    'RWIN': 92,        # Right Windows key (Natural keyboard)
    'APPS': 93,        # Applications key (Natural keyboard)
    'SLEEP': 95,       # Computer Sleep key
    'NUMPAD0': 96,     # Numeric keypad 0 key
    'NUMPAD1': 97,     # Numeric keypad 1 key
    'NUMPAD2': 98,     # Numeric keypad 2 key
    'NUMPAD3': 99,     # Numeric keypad 3 key
    'NUMPAD4': 100,    # Numeric keypad 4 key
    'NUMPAD5': 101,    # Numeric keypad 5 key
    'NUMPAD6': 102,    # Numeric keypad 6 key
    'NUMPAD7': 103,    # Numeric keypad 7 key
    'NUMPAD8': 104,    # Numeric keypad 8 key
    'NUMPAD9': 105,    # Numeric keypad 9 key
    'MULTIPLY': 106,   # Multiply key
    'ADD': 107,        # Add key
    'SEPARATOR': 108,  # Separator key
    'SUBTRACT': 109,   # Subtract key
    'DECIMAL': 110,    # Decimal key
    'DIVIDE': 111,     # Divide key

    'F1':  112,  # F1 key
    'F2':  113,  # F2 key
    'F3':  114,  # F3 key
    'F4':  115,  # F4 key
    'F5':  116,  # F5 key
    'F6':  117,  # F6 key
    'F7':  118,  # F7 key
    'F8':  119,  # F8 key
    'F9':  120,  # F9 key
    'F10': 121,  # F10 key
    'F11': 122,  # F11 key
    'F12': 123,  # F12 key
    'F13': 124,  # F13 key
    'F14': 125,  # F14 key
    'F15': 126,  # F15 key
    'F16': 127,  # F16 key
    'F17': 128,  # F17 key
    'F18': 129,  # F18 key
    'F19': 130,  # F19 key
    'F20': 131,  # F20 key
    'F21': 132,  # F21 key
    'F22': 133,  # F22 key
    'F23': 134,  # F23 key
    'F24': 135,  # F24 key

    'NUMLOCK': 144,              #NUM LOCK key
    'SCROLL': 145,               #SCROLL LOCK key
    'LSHIFT': 160,               #Left SHIFT key
    'RSHIFT': 161,               #Right SHIFT key
    'LCONTROL': 162,             #Left CONTROL key
    'RCONTROL': 163,             #Right CONTROL key
    'LMENU': 164,                #Left MENU key
    'RMENU': 165,                #Right MENU key
    'BROWSER_BACK': 166,         #Browser Back key
    'BROWSER_FORWARD': 167,      #Browser Forward key
    'BROWSER_REFRESH': 168,      #Browser Refresh key
    'BROWSER_STOP': 169,         #Browser Stop key
    'BROWSER_SEARCH': 170,       #Browser Search key
    'BROWSER_FAVORITES': 171,    #Browser Favorites key
    'BROWSER_HOME': 172,         #Browser Start and Home key
    'VOLUME_MUTE': 173,          #Volume Mute key
    'VOLUME_DOWN': 174,          #Volume Down key
    'VOLUME_UP': 175,            #Volume Up key
    'MEDIA_NEXT_TRACK': 176,     #Next Track key
    'MEDIA_PREV_TRACK': 177,     #Previous Track key
    'MEDIA_STOP': 178,           #Stop Media key
    'MEDIA_PLAY_PAUSE': 179,     #Play/Pause Media key
    'LAUNCH_MAIL': 180,          #Start Mail key
    'LAUNCH_MEDIA_SELECT': 181,  #Select Media key
    'LAUNCH_APP1': 182,          #Start Application 1 key
    'LAUNCH_APP2': 183,          #Start Application 2 key

    'OEM_1': 186,       #Used for miscellaneous characters; it can vary by keyboard. For the US standard keyboard, the ';:' key
    'OEM_PLUS': 187,    #For any country/region, the '+' key
    'OEM_COMMA': 188,   #For any country/region, the ',' key
    'OEM_MINUS': 189,   #For any country/region, the '-' key
    'OEM_PERIOD': 190,  #For any country/region, the '.' key
    'OEM_2': 191,       #Used for miscellaneous characters; it can vary by keyboard. For the US standard keyboard, the '/?' key =
    'OEM_3': 192,       #Used for miscellaneous characters; it can vary by keyboard. = For the US standard keyboard, the '`~' key
    'OEM_4': 219,       #Used for miscellaneous characters; it can vary by keyboard. For the US standard keyboard, the '[{' key
    'OEM_5': 220,       #Used for miscellaneous characters; it can vary by keyboard.For the US standard keyboard, the '\|' key
    'OEM_6': 221,       #Used for miscellaneous characters; it can vary by keyboard.For the US standard keyboard, the ']}' key
    'OEM_7': 222,       #Used for miscellaneous characters; it can vary by keyboard.For the US standard keyboard, the 'single-quote/double-quote' key
    'OEM_8': 223,       #Used for miscellaneous characters; it can vary by keyboard.
    'OEM_102': 226,     #Either the angle bracket key or the backslash key on the RT 102-key keyboard 0xE3-E4 OEM specific

    'PROCESSKEY': 229,  #IME PROCESS key 0xE6 = OEM specific #
    'PACKET': 231,      #Used to pass Unicode characters as if they were keystrokes. The VK_PACKET key is the low word of a 32-bit Virtual Key value used for non-keyboard input methods. For more information, see Remark in KEYBDINPUT, SendInput, WM_KEYDOWN, and WM_KEYUP #-
    'ATTN': 246,        #Attn key
    'CRSEL': 247,       #CrSel key
    'EXSEL': 248,       #ExSel key
    'EREOF': 249,       #Erase EOF key
    'PLAY': 250,        #Play key
    'ZOOM': 251,        #Zoom key
    'NONAME': 252,      #Reserved
    'PA1': 253,         #PA1 key
    'OEM_CLEAR': 254,   #
}