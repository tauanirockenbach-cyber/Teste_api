#baud_rate = velocidade configurada no arduino
import serial
import time

def ler_dados_via_cabo():
    porta_com = 'COM5' 
    baud_rate = 115200
    
    print(f"Conectando ao ESP32 via cabo USB na porta {porta_com}...")
    
    try:
        ser = serial.Serial(porta_com, baud_rate, timeout=2)
        time.sleep(1) 
        #Elimina dados já guardados
        ser.reset_input_buffer()
        
        print("Buscando dados de temperatura e umidade...\n")
        
        leituras_encontradas = 0
        
        for _ in range(20):
            if ser.in_waiting > 0:
                # Lê a linha enviada pelo ESP32 e converte em texto comum
                linha = ser.readline().decode('utf-8', errors='ignore').strip()
                
                # Se encontrar o texto que o ESP32 envia, mostra na tela do Python
                if "Temperatura:" in linha or "Umidade:" in linha:
                    print(f"{linha}")
                    leituras_encontradas += 1
            
            # Se já pegou a temperatura e a umidade, fecha e encerra
            if leituras_encontradas >= 2:
                break
                
            time.sleep(0.2)
            
        ser.close()
        
        if leituras_encontradas == 0:
            print("O cabo conectou, mas o ESP32 não enviou nenhum texto.")
            
    except serial.SerialException as e:
        print("\nNão foi possivel conectar")

# Executa o programa
ler_dados_via_cabo()
