import connectivity
import display
import write

# Inicializar el display
display.init_display()
display.fill_screen(0b0000000000000000)  # Llenar la pantalla 
display.set_rotation(3)  # Apaisado (90 grados)


# Inicializar ESP-NOW
print("Inicializando ESP-NOW...")
connectivity.init_espnow()
print("my mac adress is")
print(connectivity.get_my_mac())
# Mostrar mensaje inicial
print("Esperando mensajes...")

# Escuchar mensajes en un bucle
while True:
        host, mensaje = connectivity.recibir_mensajes()  # Recibe mensajes del módulo
        if mensaje:
            print(f"Mensaje recibido de {host}: {mensaje.decode('utf-8')}")
            
            write.text(10, 10, "Mensaje recibido de ", 0b1111100000000000, 0b0000000000000000)  # Texto rojo sobre fondo negro
            write.text(10, 30, f" {host}", 0b1111100000000000, 0b0000000000000000)  # Texto rojo sobre fondo negro
            write.text(10, 60, f" {mensaje.decode('utf-8')}", 0b1111100000000000, 0b0000000000000000)  # Texto rojo sobre fondo negro

            
            
            
