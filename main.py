import requests

menu_moedas = """

\033[31m=== Opções de Moedas para Consulta ===\033[0m

Tradicionais:
USD-BRL (Dólar Americano)
EUR-BRL (Euro)
GBP-BRL (Libra Esterlina)
ARS-BRL (Peso Argentino)

Criptomoedas:
BTC-BRL (Bitcoin)
ETH-BRL (Ethereum)
=====================================
"""
print(menu_moedas)

def consultar_moeda(moeda): 
    url = f"https://economia.awesomeapi.com.br/json/last/{moeda}"
    resposta = requests.get(url)

    if resposta.status_code == 200:
        print("Deu certo!")    
        print(resposta.json())
        return resposta.json()
        
    elif resposta.status_code == 404:
        numero = resposta.json()
        status = numero.get("status")
        print(f"Status com erro: {status}")
        code = numero.get("code")
        print(f"Código do erro: {code}")
        message = numero.get("message")
        print(f"Mensagem do erro: {message}")

    else:
        print("Deu ruim!")
    

moeda_desejada = input("\033[31mDigite a moeda desejada que deseja consultar (ex: USD-BRL): \033[0m")
print("\n")
dados_api = consultar_moeda(moeda_desejada)
print("\n")

#-------------------------------------------------------------------------------------------------------

if dados_api:
    valor = dados_api[moeda_desejada]["bid"]
    print("\nRequisição bem sucedida!")
    print(f"O valor atual de {moeda_desejada} é: R$ {moeda_desejada} {float(valor):.2f}") 

else:
    print(f"\nErro ao consultar a moeda: {moeda_desejada} \nVerifique se o formato está correto")
