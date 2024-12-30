import display
import write
import connectivity


# Inicializar el display
display.init_display()
display.fill_screen(0b0000000000000000)  # Llenar la pantalla 
display.set_rotation(3)  # Apaisado (90 grados)

# Inicializar Wi-Fi
wifi = connectivity.WiFiManager()
wifi.connect("WIFI USER", "WIFI PASSWORD")
    
# Inicializar Bluetooth
ble = connectivity.BluetoothManager()
ble.start_advertising("ESP32-S3 Geek")
write.text(10, 10, "ble connected", 0b1111100000000000, 0b1111111111111111, size=12)  # Texto rojo sobre fondo blanco


def on_receive(conn_handle, attr_handle):
    print(f"Datos recibidos en conexión {conn_handle}, atributo {attr_handle}")

    ble.on_receive(on_receive)
    
