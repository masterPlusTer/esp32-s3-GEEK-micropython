"""MicroPython Wi-Fi with bounded connection time and useful errors."""
import network
import time

class WiFi:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)

    def connect(self, ssid, password, timeout_ms=12000):
        self.wlan.active(True)
        if self.wlan.isconnected():
            return self.wlan.ifconfig()
        self.wlan.connect(ssid, password)
        started = time.ticks_ms()
        bad = tuple(getattr(network, n) for n in
                    ('STAT_WRONG_PASSWORD', 'STAT_NO_AP_FOUND', 'STAT_CONNECT_FAIL')
                    if hasattr(network, n))
        while not self.wlan.isconnected():
            status = self.wlan.status()
            if status in bad:
                self.wlan.disconnect()
                raise OSError('Wi-Fi status failure: %s' % status)
            if time.ticks_diff(time.ticks_ms(), started) >= timeout_ms:
                self.wlan.disconnect()
                raise OSError('Wi-Fi timed out after %d ms' % timeout_ms)
            time.sleep_ms(100)
        return self.wlan.ifconfig()

    def disconnect(self):
        if self.wlan.active():
            self.wlan.disconnect()
            self.wlan.active(False)

    def scan(self):
        self.wlan.active(True)
        return self.wlan.scan()

