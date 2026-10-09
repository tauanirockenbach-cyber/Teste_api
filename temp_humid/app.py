import streamlit as st
import serial
import serial.tools.list_ports
import time
import re
import random
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# CONFIGURAÇÃO DA PÁGINA STREAMLIT
# ==========================================
st.set_page_config(
    page_title="Monitor ESP32 - Temp & Umidade",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# ESTILIZAÇÃO CSS CUSTOMIZADA (CORES VIBRANTES & NEON)
# ==========================================
st.markdown("""
<style>
    /* Fundo principal escuro com brilho vibrante */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #1a0b2e 0%, #090314 100%);
        color: #FFFFFF;
    }
    
    /* Título principal com gradiente chamativo */
    .vibrant-title {
        font-size: 2.8rem !important;
        font-weight: 800 !important;
        background: linear-gradient(90deg, #FF007F, #7928CA, #00F0FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0px 0px 25px rgba(255, 0, 127, 0.4);
        margin-bottom: 0px;
    }
    
    .vibrant-subtitle {
        color: #A0AEC0;
        font-size: 1.1rem;
        margin-bottom: 25px;
    }

    /* Cards Personalizados Neon */
    .card-temp {
        background: rgba(255, 0, 127, 0.1);
        border: 2px solid #FF007F;
        box-shadow: 0 0 20px rgba(255, 0, 127, 0.3);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
    }

    .card-umid {
        background: rgba(0, 240, 255, 0.1);
        border: 2px solid #00F0FF;
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.3);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
    }

    .card-val {
        font-size: 3rem;
        font-weight: 900;
        margin: 10px 0;
    }

    .temp-color {
        color: #FF2A85;
        text-shadow: 0 0 10px rgba(255, 42, 133, 0.6);
    }

    .umid-color {
        color: #00F0FF;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.6);
    }

    /* Estilo do botão vibrante */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #FF007F 0%, #7928CA 100%);
        color: white;
        font-weight: bold;
        font-size: 1.1rem;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        box-shadow: 0 0 15px rgba(255, 0, 127, 0.5);
        transition: all 0.3s ease;
    }
    
    div.stButton > button:first-child:hover {
        transform: scale(1.03);
        box-shadow: 0 0 25px rgba(255, 0, 127, 0.8);
    }

    /* Caixa do Terminal Serial */
    .terminal-box {
        background-color: #05020a;
        border: 1px solid #7928CA;
        border-radius: 10px;
        padding: 12px;
        font-family: 'Courier New', Courier, monospace;
        color: #39FF14;
        height: 180px;
        overflow-y: auto;
        box-shadow: inset 0 0 10px rgba(121, 40, 202, 0.5);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# INICIALIZAÇÃO DO ESTADO DA SESSÃO
# ==========================================
if 'historico' not in st.session_state:
    st.session_state.historico = pd.DataFrame(columns=['Hora', 'Temperatura', 'Umidade'])

if 'logs' not in st.session_state:
    st.session_state.logs = []

# ==========================================
# FUNÇÃO PARA DETECTAR PORTAS COM
# ==========================================
def listar_portas_com():
    portas = [port.device for port in serial.tools.list_ports.comports()]
    return portas if portas else ["COM5"]

# ==========================================
# SIDEBAR / PAINEL DE CONTROLE
# ==========================================
st.sidebar.markdown("<h2 style='color: #00F0FF;'>⚙️ Conexão Serial</h2>", unsafe_allow_html=True)

modo_simulacao = st.sidebar.checkbox("🎮 Modo Simulação (sem ESP32)", value=False)

portas_disponiveis = listar_portas_com()
porta_com = st.sidebar.selectbox("Porta COM:", portas_disponiveis, index=0 if "COM5" not in portas_disponiveis else portas_disponiveis.index("COM5"))
baud_rate = st.sidebar.selectbox("Baud Rate:", [9600, 19200, 38400, 57600, 115200], index=4)

st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color: #FF007F;'>⏱️ Atualização</h3>", unsafe_allow_html=True)
intervalo_leitura = st.sidebar.slider("Intervalo (segundos):", 1, 10, 2)

if st.sidebar.button("🗑️ Limpar Histórico"):
    st.session_state.historico = pd.DataFrame(columns=['Hora', 'Temperatura', 'Umidade'])
    st.session_state.logs = []
    st.rerun()

# ==========================================
# CABEÇALHO DA PÁGINA
# ==========================================
st.markdown('<h1 class="vibrant-title">⚡ ESP32 DASHBOARD</h1>', unsafe_allow_html=True)
st.markdown('<p class="vibrant-subtitle">Monitoramento em Tempo Real via Comunicação Serial USB</p>', unsafe_allow_html=True)

# ==========================================
# FUNÇÃO DE LEITURA SERIAL / SIMULAÇÃO
# ==========================================
def realizar_leitura():
    temp_encontrada = None
    umid_encontrada = None
    linhas_lidas = []

    if modo_simulacao:
        time.sleep(0.3)
        temp_encontrada = round(24.0 + random.uniform(-1.5, 2.5), 1)
        umid_encontrada = round(60.0 + random.uniform(-4.0, 4.0), 1)
        linhas_lidas = [
            f"Temperatura: {temp_encontrada} °C",
            f"Umidade: {umid_encontrada} %"
        ]
        return temp_encontrada, umid_encontrada, linhas_lidas

    try:
        ser = serial.Serial(porta_com, baud_rate, timeout=2)
        time.sleep(0.5)
        ser.reset_input_buffer()

        leituras_encontradas = 0

        for _ in range(20):
            if ser.in_waiting > 0:
                linha = ser.readline().decode('utf-8', errors='ignore').strip()
                if linha:
                    linhas_lidas.append(linha)
                
                # Procura padrões de temperatura e umidade usando Regex
                if "Temperatura:" in linha:
                    match = re.search(r'[\d\.]+', linha)
                    if match:
                        temp_encontrada = float(match.group())
                        leituras_encontradas += 1

                if "Umidade:" in linha:
                    match = re.search(r'[\d\.]+', linha)
                    if match:
                        umid_encontrada = float(match.group())
                        leituras_encontradas += 1

            if leituras_encontradas >= 2:
                break
            time.sleep(0.1)

        ser.close()

    except serial.SerialException as e:
        linhas_lidas.append(f"❌ Erro de Conexão na {porta_com}: {e}")

    return temp_encontrada, umid_encontrada, linhas_lidas

# ==========================================
# BOTÃO PRINCIPAL DE LEITURA
# ==========================================
col_btn, col_blank = st.columns([1, 2])
with col_btn:
    btn_ler = st.button("🔄 LER DADOS DO ESP32")

# ==========================================
# CONTAINERS REUTILIZÁVEIS PARA REFRESH
# ==========================================
kpi_container = st.empty()
charts_container = st.empty()
log_container = st.empty()

def atualizar_dashboard(temp, umid, raw_logs):
    hora_atual = datetime.now().strftime("%H:%M:%S")

    # Salva no histórico se dados válidos forem lidos
    if temp is not None and umid is not None:
        novo_registro = pd.DataFrame([{
            'Hora': hora_atual,
            'Temperatura': temp,
            'Umidade': umid
        }])
        st.session_state.historico = pd.concat([st.session_state.historico, novo_registro], ignore_index=True)

    # Adiciona novos logs
    for line in raw_logs:
        st.session_state.logs.append(f"[{hora_atual}] {line}")
    st.session_state.logs = st.session_state.logs[-15:] # Mantém os últimos 15 logs

    # 1. RENDERIZAR CARDS DE KPI VIBRANTES
    with kpi_container.container():
        col1, col2 = st.columns(2)
        
        val_temp = f"{temp:.1f} °C" if temp is not None else "N/A"
        val_umid = f"{umid:.1f} %" if umid is not None else "N/A"

        with col1:
            st.markdown(f"""
            <div class="card-temp">
                <span style="color: #FF007F; font-size: 1.2rem; font-weight: bold;">🔥 TEMPERATURA</span>
                <div class="card-val temp-color">{val_temp}</div>
                <small style="color: #A0AEC0;">Sensor ESP32</small>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="card-umid">
                <span style="color: #00F0FF; font-size: 1.2rem; font-weight: bold;">💧 UMIDADE</span>
                <div class="card-val umid-color">{val_umid}</div>
                <small style="color: #A0AEC0;">Sensor ESP32</small>
            </div>
            """, unsafe_allow_html=True)

    # 2. RENDERIZAR GRÁFICOS VIBRANTES COM PLOTLY
    with charts_container.container():
        st.markdown("<br>", unsafe_allow_html=True)
        col_g1, col_g2 = st.columns(2)

        df = st.session_state.historico

        # Gráfico de Temperatura
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(
            x=df['Hora'], y=df['Temperatura'],
            mode='lines+markers',
            name='Temp (°C)',
            line=dict(color='#FF007F', width=4),
            marker=dict(size=8, color='#FF5500', symbol='circle')
        ))
        fig_temp.update_layout(
            title="<b>Evolução da Temperatura (°C)</b>",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(15, 8, 30, 0.8)',
            font=dict(color='#FFFFFF'),
            xaxis=dict(showgrid=True, gridcolor='#33145a'),
            yaxis=dict(showgrid=True, gridcolor='#33145a'),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        col_g1.plotly_chart(fig_temp, use_container_width=True)

        # Gráfico de Umidade
        fig_umid = go.Figure()
        fig_umid.add_trace(go.Scatter(
            x=df['Hora'], y=df['Umidade'],
            mode='lines+markers',
            name='Umidade (%)',
            line=dict(color='#00F0FF', width=4),
            marker=dict(size=8, color='#00FF66', symbol='diamond')
        ))
        fig_umid.update_layout(
            title="<b>Evolução da Umidade (%)</b>",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(15, 8, 30, 0.8)',
            font=dict(color='#FFFFFF'),
            xaxis=dict(showgrid=True, gridcolor='#33145a'),
            yaxis=dict(showgrid=True, gridcolor='#33145a'),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        col_g2.plotly_chart(fig_umid, use_container_width=True)

    # 3. RENDERIZAR TERMINAL DE LOGS SERIAL
    with log_container.container():
        st.markdown("<h4 style='color: #39FF14;'>📟 Logs Brutos da Porta Serial</h4>", unsafe_allow_html=True)
        logs_html = "<br>".join(st.session_state.logs) if st.session_state.logs else "Aguardando leitura de dados..."
        st.markdown(f'<div class="terminal-box">{logs_html}</div>', unsafe_allow_html=True)

# Execução ao clicar no botão
if btn_ler:
    with st.spinner("Conectando ao ESP32 e lendo porta serial..."):
        t, u, logs = realizar_leitura()
        atualizar_dashboard(t, u, logs)
else:
    # Mostra o estado atual das métricas e históricos se já houver leituras gravadas
    ult_temp = st.session_state.historico['Temperatura'].iloc[-1] if not st.session_state.historico.empty else None
    ult_umid = st.session_state.historico['Umidade'].iloc[-1] if not st.session_state.historico.empty else None
    atualizar_dashboard(ult_temp, ult_umid, [])

# ==========================================
# EXPORTAÇÃO DE DADOS
# ==========================================
if not st.session_state.historico.empty:
    st.markdown("---")
    csv = st.session_state.historico.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar Histórico de Leituras (CSV)",
        data=csv,
        file_name=f"leituras_esp32_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )