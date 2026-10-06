
#include <WiFi.h>             // Biblioteca nativa do ESP32
#include <HTTPClient.h>       // Biblioteca nativa do ESP32
#include <Wire.h>             // Biblioteca nativa do ESP32
#include <Adafruit_SSD1306.h> // Necessária Instalação
#include <ArduinoJson.h>      // Necessária Instalação
// Configurações da rede WiFi à se conectar
const char* host = "esp32";
const char* ssid = "Wokwi-GUEST";
const char* password = "";
#define SCREEN_WIDTH 128 // Largura da tela OLED, em pixels
#define SCREEN_HEIGHT 64 // Altura da tela OLED, em pixels
#define OLED_RESET     -1 // Pino de Reset (ou -1 se compartilhar o pino de reset do Arduino)
#define SCREEN_ADDRESS 0x3C // Endereço I2C: 0x3D para 128x64 ou 0x3C para 128x32
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET); // objeto para
//                                                              controle do display OLED.
float dolar, euro, libra, peso, bitcoin, iene; // armazenará os valores das moedas
float varDolar, varEuro, varLibra, varPeso, varBitcoin, varIene; // armazenará as
//                                               variações dos valores das moedas.
bool invalido = true; // armazenará se a requisição de cotação é ou não inválida
// https://economia.awesomeapi.com.br/json/last/USD-BRL,EUR-BRL,GBP-BRL,ARS-BRL,BTC-BRL,JPY-BRL/
String url = "https://economia.awesomeapi.com.br/json/last/";
String moedas = "USD-BRL,EUR-BRL,GBP-BRL,ARS-BRL,BTC-BRL,JPY-BRL";
int telaAtual = 5; // índice de tela OLED
// Timers:
unsigned long timerRequisicao; const int periodoRequisicao = 30000; // de requisição HTTP
unsigned long timerExibicao; const int periodoExibicao = 5000; // de Troca de Tela
unsigned long timerProgress; const int periodoProgress = 50; // de Barra de Progresso
int larguraDisplay; // armazenará a largura do display (em Pixels)
int alturaDisplay; // armazenará a altura do display (em Pixels)
void setup() {
  url.concat(moedas); // concatena a String url com a String moedas
  Serial.begin(115200); // Configura a taxa de transferência em bits por
  //                        segundo (baud rate) para transmissão serial.
  Serial.println();
  delay(1000);
  if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) // Inicializa o display
  {
    Serial.println("Falha na alocação de SSD1306");
    for (;;); // Não prossiga, faça um loop para sempre
  }
  larguraDisplay = display.width() - 1;
  alturaDisplay = display.height() - 1;
  display.clearDisplay(); // Limpa a tela
  display.setTextSize(1); // multiplica a escala do texto por 1
  display.setTextColor(SSD1306_WHITE); // define a cor dos objetos
  //                                        (texto, linhas, círculos, etc.) do
  //                                        display para a cor branca equivalente
  //                                        do display (azul).
  display.setCursor(10, 0); // configura o cursor para ir na coluna 10 e linha 0
  display.println("Consulta moedas");
  display.setCursor(0, 16); // configura o cursor para ir na coluna 0 e linha 16
  display.println("Valor Compra");
  display.drawLine(0, 42, display.width() - 1, 42, SSD1306_WHITE); // desenha uma
  //                                   linha, partindo da coluna 0 e linha 42 até
  //                                   a coluna final e linha 42, utilizando a cor
  //                                   branca correspondente (azul).
  display.setCursor(0, 46); // configura o cursor para ir na coluna 0 e linha 46
  display.setTextSize(2); // multiplica a escala do texto por 2
  display.write(0x12); // escreve o caractere ↕ (Code Page 437) de endereço 0x12
  display.setTextSize(1); // multiplica a escala do texto por 1
  display.setCursor(20, 46); // configura o cursor para ir na coluna 20 e linha 46
  display.println("Variacao em %");
  display.display();// Atualiza o display
  WiFi.disconnect(); // desconecta de algum WiFi conectado anteriormente
  WiFi.mode(WIFI_STA); // define o ESP32 para o modo estação de WiFi
  WiFi.setHostname(host); // define o hostname do ESP32 para com a rede WiFi
  WiFi.begin(ssid, password); // se conecta no WiFi com  SSID e a senha informada
  Serial.println("[SETUP] Iniciando o WiFi");
  if (WiFi.waitForConnectResult() == WL_CONNECTED) // Espera o ESP32 se conectar
    //           na rede informada e retorna o resultado após um tempo esperando.
  {
    Serial.println("[SETUP] WiFi iniciado com sucesso!");
  }
  else
  {
    Serial.println("[SETUP] Houve falha na inicialização do WiFi. A placa será reiniciada.");
    ESP.restart();
  }
  display.clearDisplay(); // Limpa a tela
  display.setTextSize(1); // multiplica a escala do texto por 1
  display.setTextColor(SSD1306_WHITE); // define a cor dos objetos
  //                                        (texto, linhas, círculos, etc.) do
  //                                        display para a cor branca equivalente
  //                                        do display (azul).
  display.setCursor(10, 0);
  display.println("Cotacao do Dolar");
  display.setTextSize(2);
  display.setCursor(0, 16); // configura o cursor para ir na coluna 0 e linha 16
  display.println("Busca...");
  display.display(); // Atualiza a tela
}
void loop() {
  // Faz a requisição e atualiza os dados
  if (millis() - timerRequisicao >= periodoRequisicao || timerRequisicao == 0) {
    HTTPClient http; // Cria o objeto da classe HTTPClient
    Serial.println("[HTTP] begin...");
    http.begin(url); // se conecta com o servidor através da UR fornecida
    Serial.println("[HTTP] GET...");
    int httpCode = http.GET(); // envia uma solicitação GET e obtém o código de resposta
    if (httpCode == 200) // se o código de resposta for igual à 200 (OK), ...
    {
      invalido = false; // armazena que a requisição de cotação não é inválida
      DynamicJsonDocument doc(2048); // Bytes necessários para armazenar os objetos
      //                      e matrizes JSON na memória. 2048 Bytes com base no
      //                      cálculo em http://arduinojson.org/v6/assistant.
      // Analisa o objeto JSON
      DeserializationError error = deserializeJson(doc, http.getString());
      if (error) // se houve erros na análise do JSON, ...
      {
        Serial.print("deserializeJson() falhou: ");
        Serial.println(error.f_str());
        invalido = true; // armazena que a requisição de cotação é inválida
      } else  // se não houve erros na análise do JSON, ...
      {
        // Extrai os valores do tempo e repassa para as variáveis globais
        dolar = String((const char*)doc["USDBRL"]["bid"]).toFloat();
        varDolar = String((const char*)doc["USDBRL"]["pctChange"]).toFloat();
        euro = String((const char*)doc["EURBRL"]["bid"]).toFloat();
        varEuro = String((const char*)doc["EURBRL"]["pctChange"]).toFloat();
        libra = String((const char*)doc["GBPBRL"]["bid"]).toFloat();
        varLibra = String((const char*)doc["GBPBRL"]["pctChange"]).toFloat();
        peso = String((const char*)doc["ARSBRL"]["bid"]).toFloat();
        varPeso = String((const char*)doc["ARSBRL"]["pctChange"]).toFloat();
        bitcoin = String((const char*)doc["BTCBRL"]["bid"]).toFloat();
        varBitcoin = String((const char*)doc["BTCBRL"]["pctChange"]).toFloat();
        iene = String((const char*)doc["JPYBRL"]["bid"]).toFloat();
        varIene = String((const char*)doc["JPYBRL"]["pctChange"]).toFloat();
      }
    } else {
      invalido = true; // armazena que a requisição de cotação é inválida
    }
    http.end();  // finaiza a conexão HTTP
    Serial.println("[HTTP] GET END!\n");
    timerRequisicao = millis();
  }
  // Muda a tela
  if (millis() - timerExibicao >= periodoExibicao || timerExibicao == 0) {
    telaAtual++; // a cada passada neste ponto, a tela muda
    if (telaAtual > 5) // se o índice da tela atual for maior
      //                     que a quantidade de telas máxima,...
    {
      telaAtual = 0; // volta para a tela inicial
    }
    if (invalido) // se a requisição anterior for inválida, ...
    {
      timerRequisicao = millis() + periodoRequisicao; // adiciona o tempo de periodo
      //                            entre as exibições + o tempo atual de millis()
      //                            para que uma nova requisição seja feita agora
      //                            e não após espera o período periodoRequisicao
      //                            terminar.
    }
    // exibe a cotação de uma determinada moeda de acordo com a tela atual
    //   à que o programa se encontra.
    switch (telaAtual) {
      case 0: // Dólar
        printMoeda("Dolar", dolar, varDolar);
        break;
      case 1: // Euro
        printMoeda("Euro", euro, varEuro);
        break;
      case 2: // Libra Esterlina
        printMoeda("Libra Est.", libra, varLibra);
        break;
      case 3: // Peso Argentino
        printMoeda("Peso Arge.", peso, varPeso);
        break;
      case 4: // Bitcoin
        printMoeda("Bitcoin", bitcoin, varBitcoin);
        break;
      case 5: // Iene
        printMoeda("Iene", iene, varIene);
        break;
    }
    display.display(); // Atualiza o display
    timerExibicao = millis();
  }
  // Exibe a barra de progresso
  if (millis() - timerProgress >= periodoProgress || timerProgress == 0) {
    // exibe o progresso atual de acordo com a tela atual à que o programa se
    //  encontra e então com converte a faixa de periodo para porcentagem
    switch (telaAtual)
    {
      case 0: // Dólar
        printProgressBar(
          map(millis() - timerExibicao, 0, periodoExibicao, 0, 16)
        ); // 0% a 16%
        break;
      case 1: // Euro
        printProgressBar(
          map(millis() - timerExibicao, 0, periodoExibicao, 16, 32)
        ); // 16% a 32%
        break;
      case 2: // Libra Esterlina
        printProgressBar(
          map(millis() - timerExibicao, 0, periodoExibicao, 32, 48)
        ); // 32% a 48%
        break;
      case 3: // Peso Argentino
        printProgressBar(
          map(millis() - timerExibicao, 0, periodoExibicao, 48, 64)
        ); // 48% a 64%
        break;
      case 4: // Bitcoin
        printProgressBar(
          map(millis() - timerExibicao, 0, periodoExibicao, 64, 80)
        ); // 64% a 80%
        break;
      case 5: // Iene
        printProgressBar(
          map(millis() - timerExibicao, 0, periodoExibicao, 80, 100)
        ); // 80% a 100%
        break;
    }
    display.display(); // Atualiza Display
    timerProgress = millis();
  }
  delay(1); // pausa de 1 milissegundo
}
/**
  Função que mostra na tela o valor, a variação e o nome da moeda informada
  @param nomeMoeda - O nome da moeda à ser mostrada.
  @param moeda - O valor de cotação da moeda.
  @param variacaoMoeda - O valor de variação da moeda.
*/
void printMoeda(String nomeMoeda, float moeda, float variacaoMoeda) {
  if (invalido)  // se a requisição anterior for inválida, ...
  {
    Serial.println("Requisição inválida"); // imprime que a requisição é inválida
    display.clearDisplay(); // Limpa a tela
    display.setTextSize(1); // multiplica a escala do texto por 1
    display.setTextColor(SSD1306_WHITE); // define a cor dos objetos
    //                                        (texto, linhas, círculos, etc.) do
    //                                        display para a cor branca equivalente
    //                                        do display (azul).
    display.setCursor(10, 0); // configura o cursor para ir na coluna 10 e linha 0
    display.println("Cotacao do Dolar");
    display.setTextSize(1); // multiplica a escala do texto por 2
    display.setCursor(0, 16); // configura o cursor para ir na coluna 0 e linha 16
    display.println("Erro Rede");
  }
  else  // se não, ...
  {
    display.setTextWrap(false);
    display.clearDisplay(); // Limpa a tela
    display.setTextSize(1); // multiplica a escala do texto por 2
    display.setTextColor(SSD1306_WHITE); // define a cor dos objetos
    //                                        (texto, linhas, círculos, etc.) do
    //                                        display para a cor branca equivalente
    //                                        do display (azul).
    display.setCursor(0, 0); // configura o cursor para ir na coluna 0 e linha 0
    display.println("Cotacao do Dolar");
    display.println(nomeMoeda); // imprime o nome da moeda
    display.setTextSize(1); // multiplica a escala do texto por 2
    display.setCursor(0, 16); // configura o cursor para ir na coluna 0 e linha 16
    display.print("R$ ");
    if (moeda > 99) // se o valor da moeda for maior que 99, ...
    {
      display.setTextSize(1); // multiplica a escala do texto por 2
    }
    else // se não, ...
    {
      display.setTextSize(2); // multiplica a escala do texto por 3
    }
    display.println(String(moeda, 2)); // imprime o valor da moeda com 2 dígitos decimais
    display.drawLine(0, 40, display.width() - 1, 40, SSD1306_WHITE); // desenha uma
    //                                   linha, partindo da coluna 0 e linha 42 até
    //                                   a coluna final e linha 42, utilizando a cor
    //                                   branca correspondente (azul).
    display.setCursor(0, 42); // configura o cursor para ir na coluna 0 e linha 42
    display.setTextSize(2); // multiplica a escala do texto por 2
    if (variacaoMoeda > 0) // se o valor de variação da moeda for maior que 0, ...
    {
      display.write(0x18); // escreve o caractere ↑ (Code Page 437) de endereço 0x18
    }
    else if (variacaoMoeda < 0)
    {
      display.write(0x19); // escreve o caractere ↓ (Code Page 437) de endereço 0x19
    }
    else
    {
      display.write(0x12); // escreve o caractere ↕ (Code Page 437) de endereço 0x12
    }
    display.setCursor(20, 42); // configura o cursor para ir na coluna 20 e linha 42
    variacaoMoeda = abs(variacaoMoeda); // define o valor de variação da moeda
    //                                      para o valor absoluto do mesmo.
    display.print(String(variacaoMoeda, 2)); // imprime a variação da moeda
    display.println("%");
  }
}
/**
  Função que mostra na tela a barra de progresso
  @param percent - O valor em porcentagem da barra de progresso.
*/
void printProgressBar(int percent) {
  if (!invalido) // se a requisição anterior for inválida, ...
  {
    // Desenha o quadrado externo
    display.drawRect(0,
                     alturaDisplay - 3,
                     larguraDisplay,
                     5,
                     SSD1306_WHITE); // desenha um retângulo sem cor de preenchimento, partindo
    //                                    da coluna '0' e linha 'alturaDisplay - 5' com uma
    //                                    largura de 'larguraDisplay' e com uma altura de '5',
    //                                    utilizando a cor branca correspondente (azul).
    //Variáveis locais de controle
    int larguraInternaMinima = 1;
    int larguraInternaMaxima = larguraDisplay - 1;
    int larguraInterna;
    larguraInterna = map(percent, 0, 70, larguraInternaMinima, larguraInternaMaxima);
    // Desenha o quadrado interno (preenchimento)
    display.fillRect(1, alturaDisplay - 4 + 1, larguraInterna, 2, SSD1306_WHITE);
    //Desenha as barras de separação das telas
    display.fillRect(21, alturaDisplay - 5, 1, 5, SSD1306_BLACK);
    display.fillRect(41, alturaDisplay - 5, 1, 5, SSD1306_BLACK);
    display.fillRect(61, alturaDisplay - 5, 1, 5, SSD1306_BLACK);
    display.fillRect(81, alturaDisplay - 5, 1, 5, SSD1306_BLACK);
    display.fillRect(101, alturaDisplay - 5, 1, 5, SSD1306_BLACK);
  }
}