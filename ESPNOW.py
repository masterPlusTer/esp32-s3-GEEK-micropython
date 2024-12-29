import network
from espnow import ESPNow

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

