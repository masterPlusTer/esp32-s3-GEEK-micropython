import connectivity
import time

# Dirección MAC del receptor (cambia esto con la dirección MAC real del receptor)
mac_receptor = b'\x00\x00\x00\x00\x00\x00'  # Reemplaza con la MAC real
mensaje = "Hola desde el esp32-s3-geek!!!"

connectivity.init_espnow()


while True:
    connectivity.enviar_mensaje(mac_receptor, mensaje)
    print(f"Mensaje enviado: {mensaje}")
    time.sleep(5)


