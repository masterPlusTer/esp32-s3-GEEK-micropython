import network
import bluetooth
from espnow import ESPNow

class WiFiManager:
    def __init__(self):
        """
        Inicializa el módulo Wi-Fi en modo estación (STA).
        """
        self.wlan = network.WLAN(network.STA_IF)

    def connect(self, ssid, password):
        """
        Conecta el ESP32-S3 a una red Wi-Fi.
        
        :param ssid: Nombre de la red Wi-Fi.
        :param password: Contraseña de la red Wi-Fi.
        """
        self.wlan.active(True)
        if not self.wlan.isconnected():
            print(f"Conectando a {ssid}...")
            self.wlan.connect(ssid, password)
            while not self.wlan.isconnected():
                pass
        print("Conectado a Wi-Fi:", self.wlan.ifconfig())

    def disconnect(self):
        """
        Desconecta el ESP32-S3 de la red Wi-Fi.
        """
        if self.wlan.isconnected():
            self.wlan.disconnect()
            print("Wi-Fi desconectado.")

    def is_connected(self):
        """
        Verifica si el ESP32-S3 está conectado a una red Wi-Fi.
        
        :return: True si está conectado, False en caso contrario.
        """
        return self.wlan.isconnected()
    
    

class BluetoothManager:
    def __init__(self):
        """
        Inicializa el módulo BLE.
        """
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.name = "ESP32-S3"
        self.callbacks = {}

    def start_advertising(self, name="ESP32-S3"):
        """
        Inicia el anuncio BLE.
        
        :param name: Nombre del dispositivo que será visible en BLE.
        """
        self.name = name
        adv_payload = self._generate_payload(name)
        self.ble.gap_advertise(100, adv_payload)
        print(f"BLE anunciado como {name}")

    def stop_advertising(self):
        """
        Detiene el anuncio BLE.
        """
        self.ble.gap_advertise(None)
        print("BLE anuncio detenido.")

    def on_receive(self, callback):
        """
        Configura un callback para manejar datos entrantes.
        
        :param callback: Función que será llamada cuando lleguen datos.
        """
        self.callbacks["on_receive"] = callback
        self.ble.irq(self._irq_handler)

    def _irq_handler(self, event, data):
        """
        Manejador de interrupciones BLE.
        """
        if event == bluetooth._IRQ_GATTS_WRITE:
            conn_handle, attr_handle = data
            if "on_receive" in self.callbacks:
                self.callbacks["on_receive"](conn_handle, attr_handle)

    def _generate_payload(self, name):
        """
        Genera el payload del anuncio BLE.

        :param name: Nombre del dispositivo BLE.
        :return: Bytes con el payload.
        """
        payload = bytearray()
        payload.extend(bytearray([2, 1, 6]))  # Flags
        name_bytes = name.encode("utf-8")
        payload.extend(bytearray([len(name_bytes) + 1, 9]))  # Complete Local Name
        payload.extend(name_bytes)
        return payload


#ESP NOW
    
#FAVOR DE RECORDAR QUE EL ESP-NOW Y EL WIFI NO SE LLEVAN BIEN
#SI VAS A USAR ESPNOW TEN EN CUENTA QUE NO VAS A PODER USAR WIFI PORQUE AMBOS DOS COMPARTEN ANTENA
#PERO SE PUEDE USAR ESP-NOW CON BLUETOOTH SIN PROBLEMAS :)   
    
    
# Declarar variables globales
pares_registrados = set()
espnow_instance = None  # Instancia global de ESP-NOW

# Inicialización de ESP-NOW
def init_espnow():
    global espnow_instance
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    espnow_instance = ESPNow()
    espnow_instance.active(True)

# Función para enviar un mensaje al receptor
def enviar_mensaje(mac_receptor, mensaje):
    """
    Envía un mensaje al receptor especificado.
    
    :param mac_receptor: Dirección MAC del receptor (bytes)
    :param mensaje: Mensaje a enviar (str)
    """
    global pares_registrados, espnow_instance  # Asegurar acceso a las variables globales
    if mac_receptor not in pares_registrados:
        espnow_instance.add_peer(mac_receptor)  # Agregar receptor como par
        pares_registrados.add(mac_receptor)  # Registrar el par manualmente

    # Enviar el mensaje
    espnow_instance.send(mac_receptor, mensaje)
    print(f"Mensaje enviado a {mac_receptor}: {mensaje}")

# Función para recibir mensajes
def recibir_mensajes():
    """
    Escucha mensajes entrantes.
    :return: (host, mensaje)
    """
    global espnow_instance
    if espnow_instance:
        host, mensaje = espnow_instance.recv()
        return host, mensaje
    else:
        raise RuntimeError("ESP-NOW no está inicializado. Llama a init_espnow primero.")

# Función para obtener la dirección MAC en formato legible
def get_my_mac():
    """
    Devuelve la dirección MAC del dispositivo actual en formato legible.
    """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    mac = wlan.config('mac')
    mac_legible = ':'.join('{:02X}'.format(b) for b in mac)
    return mac_legible

# Función para configurar una dirección MAC temporal
def configurar_mac_temporal(nueva_mac):
    """
    Configura una dirección MAC temporal en el dispositivo.
    
    :param nueva_mac: Nueva dirección MAC (bytes)
    """
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(mac=nueva_mac)
    mac_configurada = wlan.config('mac')
    print("Dirección MAC configurada:", ':'.join('{:02X}'.format(b) for b in mac_configurada))



