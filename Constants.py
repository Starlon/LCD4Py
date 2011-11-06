TYPE_TEXT = 0
TYPE_GRAPHIC = 1

DIR_EAST=0
DIR_WEST=1
DIR_NORTH=2
DIR_SOUTH=3

LAYERS = 3

CHUNK_SIZE=16

R_NUMBER=1
R_STRING=2

KEY_UP_PRESS = 1
KEY_DOWN_PRESS = 2
KEY_LEFT_PRESS = 3
KEY_RIGHT_PRESS = 4
KEY_ENTER_PRESS = 5
KEY_EXIT_PRESS = 6
KEY_UP_RELEASE = 7
KEY_DOWN_RELEASE = 8
KEY_LEFT_RELEASE = 9
KEY_RIGHT_RELEASE = 10
KEY_ENTER_RELEASE = 11
KEY_EXIT_RELEASE = 12

command_names =[
" 0 = Ping",
" 1 = Read Version",
" 2 = Write Flash",
" 3 = Read Flash",
" 4 = Store Boot State",
" 5 = Reboot",
" 6 = Clear LCD",
" 7 = LCD Line 1",
" 8 = LCD Line 2",
" 9 = LCD CGRAM",
"10 = Read LCD Memory",
"11 = Place Cursor",
"12 = Set Cursor Style",
"13 = Contrast",
"14 = Backlight",
"15 = Read Fans",
"16 = Set Fan Rpt.",
"17 = Set Fan Power",
"18 = Read DOW ID",
"19 = Set Temp. Rpt",
"20 = DOW Transaction",
"21 = Set Live Display",
"22 = Direct LCD Command",
"23 = Set Key Event Reporting",
"24 = Read Keypad, Polled Mode",
"25 = Set Fan Fail-Safe",
"26 = Set Fan RPM Glitch Filter",
"27 = Read Fan Pwr & Fail-Safe",
"28 = Set ATX switch functionality",
"29 = Watchdog Host Reset",
"30 = Rd Rpt",
"31 = Send Data to LCD (row,col)",
"32 = Key Legends",
"33 = Set Baud Rate",
"34 = Set/Configure GPIO",
"35 = Read GPIO & Configuration"]

error_names =[
"Error: Ping",
"Error: Version",
"Error: WriteFlash",
"Error: ReadFlash",
"Error: StoreBootState",
"Error: Reboot",
"Error: ClearLCD",
"Error: SetLCD1",
"Error: SetLCD2",
"Error: SetLCDCGRAM",
"Error: ReadLCDMemory",
"Error: PlaceLCDCursor",
"Error: LCDCursorStyle",
"Error: Contrast",
"Error: Backlight",
"Error: QueryFan",
"Error: SetFanRept.",
"Error: SetFanPower",
"Error: ReadDOWID",
"Error: SetTemp.Rept.",
"Error: DOWTransaction",
"Error: SetupLiveDisp",
"Error: DirectLCDCommand",
"Error: SetKeyEventReporting",
"Error: ReadKeypad,PolledMode",
"Error: SetFanFail-Safe",
"Error: SetFanRPMGlitchFilter",
"Error: ReadFanPwr&Fail-Safe",
"Error: SetATXswitchfunctionality",
"Error: WatchdogHostReset",
"Error: ReadReporting/ATX/Watchdog",
"Error: SendDatatoLCD(row,col)",
"Error: KeyLegends",
"Error: SetBaudRate",
"Error: Set/ConfigureGPIO",
"Error: ReadGPIO&Configuration"]
