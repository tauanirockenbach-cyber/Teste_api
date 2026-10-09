#include <WiFi.h>
#include <DHT.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <WebServer.h>

// =====================================================
// DHT22
// =====================================================
#define DHT_PIN 4  // RECOMENDADO: Alterado de 15 para 4 para evitar pinos de boot
#define DHT_TYPE DHT11

DHT dht(DHT_PIN, DHT_TYPE);

// Variáveis globais para armazenar as últimas leituras estáveis
float tempAtual = 0.0;
float umidAtual = 0.0;
bool dhtComErro = true;

// =====================================================
// WI-FI
// =====================================================
const char* ssid = "Roteador";
const char* password = "naolembro";

// =====================================================
// SERVIDOR HTTP
// =====================================================
WebServer server(80);

// =====================================================
// OLED
// =====================================================
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define SCREEN_ADDRESS 0x3C

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// PROTÓTIPO
void handleDados();

// =====================================================
// SETUP
// =====================================================
void setup() {
  Serial.begin(115200);

  // Inicializa DHT
  dht.begin();

  // Inicializa OLED
  if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println("Erro ao inicializar OLED");
    while (true) { delay(1000); }
  }

  // Tela inicial
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(20, 0);
  display.println("SENSOR DHT22");
  display.display();
  delay(1000);

  // WI-FI
  WiFi.begin(ssid, password);
  Serial.print("Conectando ao Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi conectado!");
  Serial.print("IP do ESP32: ");
  Serial.println(WiFi.localIP());

  // API
  server.on("/api/dados", HTTP_GET, handleDados);
  server.begin();
  Serial.println("Servidor HTTP iniciado!");
}

// =====================================================
// API /api/dados (Apenas envia o dado já lido)
// =====================================================
void handleDados() {
  // Se o loop principal detectou erro no sensor, avisa a API
  if (dhtComErro) {
    server.send(500, "application/json", "{\"erro\":\"Falha na leitura do DHT22\"}");
    return;
  }

  // Cria e envia o JSON com as variáveis globais estáveis
  String json = "{";
  json += "\"temperatura\": " + String(tempAtual, 1) + ",";
  json += "\"umidade\": " + String(umidAtual, 1);
  json += "}";

  server.send(200, "application/json", json);
}

// =====================================================
// LOOP
// =====================================================
void loop() {
  // Processa requisições HTTP constantemente
  server.handleClient();

  // Controle de tempo para ler o sensor a cada 2 segundos de forma não-bloqueante
  static unsigned long tempoAnterior = 0;
  unsigned long tempoAtual = millis();

  if (tempoAtual - tempoAnterior >= 2000) {
    tempoAnterior = tempoAtual;

    // Realiza a leitura física do sensor
    float t = dht.readTemperature();
    float u = dht.readHumidity();

    if (isnan(t) || isnan(u)) {
      Serial.println("Erro na leitura do DHT22");
      dhtComErro = true;
      return;
    }

    // Se a leitura foi bem sucedida, atualiza as variáveis globais
    tempAtual = t;
    umidAtual = u;
    dhtComErro = false;

    // SERIAL
    Serial.print("Temperatura: "); Serial.print(tempAtual); Serial.println(" C");
    Serial.print("Umidade: "); Serial.print(umidAtual); Serial.println(" %");

    // OLED
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    
    display.setTextSize(1);
    display.setCursor(20, 0);
    display.println("SENSOR DHT22");

    display.setTextSize(1);
    display.setCursor(0, 18);
    display.println("Temperatura:");
    display.setTextSize(2);
    display.setCursor(0, 30);
    display.print(tempAtual, 1); display.println(" C");

    display.setTextSize(1);
    display.setCursor(75, 18);
    display.println("Umidade:");
    display.setTextSize(2);
    display.setCursor(75, 30);
    display.print(umidAtual, 1); display.println("%");

    display.display();
  }
}
