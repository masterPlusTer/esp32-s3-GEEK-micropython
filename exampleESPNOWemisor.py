import ESPNOW
import time

# Dirección MAC del receptor (cambia esto con la dirección MAC real del receptor)
mac_receptor = b'\x00\x00\x00\x00\x00\x00'  # Reemplaza con la MAC real
mensaje = "Hola desde el esp32-s3-geek!!!"

ESPNOW.init_espnow()


while True:
    ESPNOW.enviar_mensaje(mac_receptor, mensaje)
    print(f"Mensaje enviado: {mensaje}")
    time.sleep(5)


