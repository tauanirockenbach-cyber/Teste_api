import requests
import streamlit as st

st.set_page_config(page_title="Consulta de Moedas", page_icon="💱", layout="centered")

# ---------- Opções de moedas (mesmo menu do código original) ----------
MOEDAS = {
    "Tradicionais": {
        "USD-BRL": "Dólar Americano",
        "EUR-BRL": "Euro",
        "GBP-BRL": "Libra Esterlina",
        "ARS-BRL": "Peso Argentino",
    },
    "Criptomoedas": {
        "BTC-BRL": "Bitcoin",
        "ETH-BRL": "Ethereum",
    },
}
OPCOES = {codigo: f"{codigo} ({nome})" for grupo in MOEDAS.values() for codigo, nome in grupo.items()}
OUTRA = "Outra (digitar o código)"

# ---------- Identidade visual ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&family=DM+Sans:wght@400;500;700&display=swap');
:root{--tinta:#1B2559;--fundo:#F2F4FB;--realce:#FFD23F;--texto2:#4A5380;--linha:#C9CFE6;--alta:#1E7B4F;--baixa:#B3243A;}
.stApp{background:var(--fundo);color:var(--tinta);font-family:'DM Sans',system-ui,sans-serif;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{max-width:760px;padding-top:2rem;}
h1,h2,h3{font-family:'Bricolage Grotesque','DM Sans',sans-serif;color:var(--tinta);}
h1{font-weight:800;letter-spacing:-.01em;}
.sub{color:var(--texto2);margin:-.5rem 0 1.2rem;}
.stSelectbox div[data-baseweb="select"]>div,.stTextInput input{border:1.5px solid var(--linha)!important;border-radius:8px!important;background:#fff!important;}
.stTextInput input:focus{border-color:var(--tinta)!important;box-shadow:0 0 0 3px var(--realce)!important;}
.stButton>button{background:var(--realce);color:var(--tinta);font-weight:700;font-size:1.05rem;border:2px solid var(--tinta);
 border-radius:8px;padding:.6rem 1.4rem;width:100%;}
.stButton>button:hover{background:var(--tinta);color:#fff;border-color:var(--tinta);}
.stButton>button:focus-visible{outline:3px solid var(--tinta);outline-offset:2px;}
.cotacao{background:#fff;border:2px solid var(--tinta);border-radius:14px;box-shadow:6px 6px 0 var(--tinta);padding:1.2rem 1.4rem;margin:1.2rem 0 .8rem;}
.cotacao .par{color:var(--texto2);font-weight:500;}
.cotacao .valor{font-family:'Bricolage Grotesque',sans-serif;font-weight:800;font-size:3rem;line-height:1.1;}
.cotacao .var{font-weight:700;}
.alta{color:var(--alta);} .baixa{color:var(--baixa);}
.grade{display:grid;grid-template-columns:repeat(3,1fr);gap:.6rem;}
.grade div{background:#fff;border:1.5px solid var(--linha);border-radius:8px;padding:.6rem .8rem;}
.grade small{color:var(--texto2);display:block;}
.grade b{font-size:1.1rem;}
@media (max-width:560px){.grade{grid-template-columns:1fr 1fr;}.cotacao .valor{font-size:2.4rem;}}
</style>
""", unsafe_allow_html=True)


def brl(v):
    """Formata número no padrão brasileiro: R$ 1.234,56"""
    return "R$ " + f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def consultar_moeda(moeda):
    """Mesma lógica do código original: devolve (dados, erro)."""
    url = f"https://economia.awesomeapi.com.br/json/last/{moeda}"
    try:
        resposta = requests.get(url, timeout=10)
    except requests.RequestException:
        return None, "Não foi possível conectar à API. Verifique sua internet e tente de novo."

    if resposta.status_code == 200:
        return resposta.json(), None

    if resposta.status_code == 404:
        info = resposta.json()
        return None, (f"Moeda não encontrada. Status: {info.get('status')} · "
                      f"Código: {info.get('code')} · Mensagem: {info.get('message')}")

    return None, f"A API respondeu com erro (código {resposta.status_code}). Tente novamente em instantes."


# ---------- Tela ----------
st.title("Consulta de moedas")
st.markdown('<p class="sub">Escolha uma moeda e veja a cotação atual em reais.</p>', unsafe_allow_html=True)

escolha = st.selectbox("Qual moeda você quer consultar?", list(OPCOES) + [OUTRA],
                       format_func=lambda c: c if c == OUTRA else OPCOES[c])

moeda_desejada = escolha
if escolha == OUTRA:
    moeda_desejada = st.text_input("Código da moeda", placeholder="Exemplo: USD-BRL").strip().upper()

if st.button("Consultar cotação"):
    if not moeda_desejada:
        st.error("Digite o código da moeda. Exemplo: USD-BRL")
    else:
        with st.spinner("Consultando..."):
            dados_api, erro = consultar_moeda(moeda_desejada)

        if erro or not dados_api:
            st.error(erro or f"Erro ao consultar a moeda: {moeda_desejada}. Verifique se o formato está correto.")
        else:
            chave = moeda_desejada.replace("-", "")
            if chave not in dados_api:
                st.error(f"Não encontramos {moeda_desejada} na resposta. Verifique se o formato está correto.")
            else:
                d = dados_api[chave]
                variacao = float(d.get("pctChange", 0))
                classe = "alta" if variacao >= 0 else "baixa"
                sinal = "▲" if variacao >= 0 else "▼"
                st.markdown(f"""
                <div class="cotacao">
                  <div class="par">{d.get('name', moeda_desejada)}</div>
                  <div class="valor">{brl(d['bid'])}</div>
                  <div class="var {classe}">{sinal} {variacao:+.2f}% hoje</div>
                </div>
                <div class="grade">
                  <div><small>Máxima</small><b>{brl(d['high'])}</b></div>
                  <div><small>Mínima</small><b>{brl(d['low'])}</b></div>
                  <div><small>Venda (ask)</small><b>{brl(d['ask'])}</b></div>
                </div>
                """, unsafe_allow_html=True)
                st.caption(f"Valor de compra (bid) · atualizado em {d.get('create_date', '—')} · Fonte: AwesomeAPI")