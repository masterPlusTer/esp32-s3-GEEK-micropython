"""ESP32-S3-GEEK MicroPython v1.29 diagnostic; run from Thonny.
No third-party modules. Uses existing tested display.py and sd_files.py.
No writes except one unique temporary file on mounted SD.
"""
import os
import time
import gc
from machine import Pin

REPORT = []
FONT = {
 'A':('010','101','111','101','101'),'B':('110','101','110','101','110'),
 'C':('011','100','100','100','011'),'D':('110','101','101','101','110'),
 'E':('111','100','110','100','111'),'F':('111','100','110','100','100'),
 'G':('011','100','101','101','011'),'H':('101','101','111','101','101'),
 'I':('111','010','010','010','111'),'J':('001','001','001','101','010'),
 'K':('101','101','110','101','101'),'L':('100','100','100','100','111'),
 'M':('101','111','111','101','101'),'N':('101','111','111','111','101'),
 'O':('010','101','101','101','010'),'P':('110','101','110','100','100'),
 'Q':('010','101','101','011','001'),'R':('110','101','110','101','101'),
 'S':('011','100','010','001','110'),'T':('111','010','010','010','010'),
 'U':('101','101','101','101','111'),'V':('101','101','101','101','010'),
 'W':('101','101','111','111','101'),'X':('101','101','010','101','101'),
 'Y':('101','101','010','010','010'),'Z':('111','001','010','100','111'),
 '0':('111','101','101','101','111'),'1':('010','110','010','010','111'),
 '2':('110','001','010','100','111'),'3':('110','001','010','001','110'),
 '4':('101','101','111','001','001'),'5':('111','100','110','001','110'),
 '6':('011','100','110','101','010'),'7':('111','001','010','010','010'),
 '8':('010','101','010','101','010'),'9':('010','101','011','001','110'),
 ' ':('000','000','000','000','000'),':':('000','010','000','010','000'),
 '.':('000','000','000','000','010'),'-':('000','000','111','000','000'),
 '/':('001','001','010','100','100'),'+':('000','010','111','010','000'),
 '?':('110','001','010','000','010'),'!':('010','010','010','000','010')
}
BG=0x0000; FG=0xFFFF; GREEN=0x07E0; RED=0xF800; YELLOW=0xFFE0
screen = None
row = 0

def smalltext(message, x, y, color=FG, scale=2):
    if screen is None: return
    for ch in message.upper():
        glyph = FONT.get(ch, FONT['?'])
        for cy, line in enumerate(glyph):
            for cx, bit in enumerate(line):
                if bit == '1':
                    screen.fill_rect(x + cx*scale, y + cy*scale, scale, scale, color)
        x += 4*scale

def show(name, status):
    global row
    print('%-13s %s' % (name, status))
    REPORT.append((name, status))
    if screen:
        if row > 10:
            screen.fill(BG)
            row=0
        color = GREEN if status.startswith('OK') else (YELLOW if status.startswith('SKIP') or status.startswith('INFO') else RED)
        smalltext(name[:12], 2, 2+row*12, FG, 2)
        smalltext(status.split(' ')[0][:5], 136, 2+row*12, color, 2)
        row += 1

def attempt(name, fn):
    try:
        fn()
    except Exception as e:
        show(name, 'FAIL %s: %s' % (type(e).__name__, e))

def test_lcd():
    global screen
    import display
    screen = display.Display(rotation=1)
    for color in (RED,GREEN,0x001F,FG,BG):
        screen.fill(color)
        time.sleep_ms(120)
    screen.fill(BG)
    # Test primitive drawing without requiring a newer Draw class
    import draw
    draw.line(0,0,screen.width-1,screen.height-1,RED)
    draw.rectangle(2,2,screen.width-3,screen.height-3,GREEN,False)
    draw.circle(screen.width//2,screen.height//2,14,YELLOW,False)
    time.sleep_ms(800)
    screen.fill(BG)
    show('LCD', 'OK visual check')

def test_button():
    # BOOT GPIO0 is active low. Avoid holding on reboot (download mode).
    b = Pin(0, Pin.IN, Pin.PULL_UP)
    print('Press and release BOOT once in 5 seconds (do not reset).')
    deadline=time.ticks_add(time.ticks_ms(),5000)
    was_down=False
    while time.ticks_diff(deadline,time.ticks_ms()) > 0:
        if b.value()==0: was_down=True
        if was_down and b.value()==1:
            show('BOOT BTN','OK pressed')
            return
        time.sleep_ms(20)
    show('BOOT BTN','SKIP not pressed')

def test_sd():
    from sd_files import SDStorage
    sd=None
    try:
        sd=SDStorage().mount()
        names=sd.list()
        print('SD items:',len(names))
        # Distinctive name, never overwrite an existing file.
        name='__geek_diag_%08x.tmp' % (time.ticks_us() & 0xffffffff)
        while name in names:
            name='__geek_diag_%08x.tmp' % ((time.ticks_us()+1) & 0xffffffff)
        payload=b'GEEK_SD_RW_VERIFY_2026\n' * 3
        created=False
        try:
            sd.write(name,payload,overwrite=False)
            created=True
            if sd.read(name,binary=True)!=payload:
                raise OSError('readback mismatch')
            sd.delete(name)
            created=False
            if name in sd.list():
                raise OSError('delete not reflected in directory')
            show('SD R/W/DEL','OK %d items' % len(names))
        finally:
            if created:
                # Try cleanup, but never hide the original failure.
                try: sd.delete(name)
                except Exception as e: print('Cleanup needed:',name,e)
    finally:
        if sd is not None:
            try: sd.unmount()
            except Exception as e: print('SD unmount:',e)

def test_wifi():
    import network
    sta=network.WLAN(network.STA_IF)
    was_active=sta.active()
    try:
        sta.active(True)
        if sta.isconnected():
            show('WIFI','OK '+sta.ifconfig()[0])
        else:
            # Scanning alone checks RX, without credentials or external Internet.
            networks=sta.scan()
            show('WIFI SCAN','OK %d AP' % len(networks))
            print('Networks:',[(s[0],s[3]) for s in networks[:5]])
    finally:
        if not was_active and not sta.isconnected(): sta.active(False)

def test_ble():
    import bluetooth
    ble=bluetooth.BLE()
    found=[0]
    done=[False]
    def irq(event, data):
        if event == 5:  # _IRQ_SCAN_RESULT
            found[0] += 1
        elif event == 6:  # _IRQ_SCAN_DONE
            done[0] = True
    ble.active(True)
    try:
        ble.irq(irq)
        ble.gap_scan(2500, 30000, 30000)
        deadline=time.ticks_add(time.ticks_ms(), 3500)
        while not done[0] and time.ticks_diff(deadline,time.ticks_ms()) > 0:
            time.sleep_ms(50)
        print('BLE advertisements detected:',found[0])
        show('BLE SCAN','OK %d ads' % found[0])
    finally:
        try: ble.gap_scan(None)
        except Exception: pass
        ble.active(False)

def test_espnow():
    import network, espnow
    sta=network.WLAN(network.STA_IF)
    original=sta.active()
    e=espnow.ESPNow()
    try:
        sta.active(True)
        e.active(True)
        show('ESP NOW','OK init only')
    finally:
        try: e.active(False)
        except Exception: pass
        if not original and not sta.isconnected(): sta.active(False)

def test_external_interfaces():
    # Ports physically exposed but no attached counterpart = no loopback test possible.
    from machine import I2C, UART
    # Do not instantiate buses with guessed pins: could conflict with other peripherals.
    show('I2C/UART','SKIP no device')

def test_system():
    import sys
    print('Firmware:',sys.version)
    print('Free heap:',gc.mem_free(),'bytes')
    show('SYSTEM','OK '+str(gc.mem_free()//1024)+' KB')

def main():
    print('\n=== ESP32-S3-GEEK DIAGNOSTIC ===')
    attempt('LCD',test_lcd)
    attempt('SYSTEM',test_system)
    attempt('BOOT BTN',test_button)
    attempt('SD',test_sd)
    attempt('WIFI',test_wifi)
    attempt('BLE',test_ble)
    attempt('ESP NOW',test_espnow)
    attempt('I2C/UART',test_external_interfaces)
    print('\n=== SUMMARY ===')
    for name, result in REPORT: print(name,':',result)
    print('Finished. Display remains on until next program/reset.')

if __name__=='__main__':
    main()

