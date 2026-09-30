import streamlit as st
import pandas as pd
from utils.auth_check import check_login
from utils.data_loader import load_daily_fixtures, load_historical_data
from utils.data_processing import sanitize_daily_fixtures, sanitize_historical_data
from utils.engine import analyze_match_signal, MERCADO, compute_league_stats
from datetime import date

st.set_page_config(
    page_title="Análise Individual | Inteligência Mercado de Gols",
    page_icon="🎯",
    layout="wide"
)

check_login()

st.sidebar.markdown('Desenvolvido por [AntonioJrSales](https://antoniojrsales.github.io/Proj_PunterSomenteMercadoGols/)')

st.title("🎯 Análise Quantitativa Individual")
st.caption("Simule confrontos específicos e calcule probabilidades com base no histórico consolidado.")

# 1. Inicializar Lista no Session State
if 'jogos_selecionados' not in st.session_state:
    st.session_state['jogos_selecionados'] = []

# 2. Carregamento dos dados históricos
@st.cache_data
def carregar_dados():
    df = pd.read_csv('data/base_gols_consolidada.csv')
    return sanitize_historical_data(df)

df_historico = carregar_dados()
ligas_disponiveis = sorted(df_historico['Liga'].dropna().unique())

# 3. Formulário de Entrada
with st.container():
    col1, col2, col3 = st.columns(3)

    with col1:
        liga_sel = st.selectbox('Campeonato / Liga:', options=ligas_disponiveis)

        df_liga = df_historico[df_historico['Liga'] == liga_sel]
        times_disponiveis = sorted(set(df_liga['HomeTeam'].dropna().unique()) | set(df_liga['AwayTeam'].dropna().unique()))

    with col2:
        mandante = st.selectbox('Equipa Mandante (Home):', options=times_disponiveis, index=0)
        mercado_sel = st.selectbox('Mercado de Interesse:', options=MERCADO)

    with col3:
        # Evita selecionar o mesmo time em mandante e visitante
        visitantes_opcoes = [t for t in times_disponiveis if t != mandante]
        visitante = st.selectbox("Equipa Visitante (Away):", options=visitantes_opcoes, index=0 if visitantes_opcoes else None)
        odd_mercado = st.number_input("Odd da Casa (Opcional para cálculo de +EV):", min_value=1.0, value=1.0, step=0.01)

    # 4. Ações
    col_btn1, col_btn2, _ = st.columns([1, 1, 3])

    with col_btn1:
        btn_analisar = st.button("⚡ Analisar Confronto", use_container_width=True, type='primary')

    with col_btn2:
        btn_adicionar = st.button("➕ Adicionar à Minha Lista", use_container_width=True, type='primary')

    # 5. Processamento dos Cálculos
    stats_l, med_c, med_f = compute_league_stats(df_liga)

    if btn_analisar or btn_adicionar:
        resultado = analyze_match_signal(
            data=date.today(),
            home_team=mandante,
            away_team=visitante,
            mercado=mercado_sel,
            stats_liga=stats_l,
            media_c=med_c,
            media_f=med_f,
            corte_minimo_pct=0.0, # Sem corte mínimo para análise aberta
            odd_mercado=odd_mercado
        )
        resultado["Liga"] = liga_sel
        resultado["Mercado"] = mercado_sel

        if btn_analisar:
            st.divider()
            st.subheader(f"📊 Relatório: {mandante} x {visitante}")
            
            c1, c2, c3, c4, c5 = st.columns([.7, .7, .7, .7, 2.2])
            c1.metric("Probabilidade Poisson", f"{resultado['Prob (%)']}%")
            c2.metric("Odd Justa Estimada", resultado["Odd Justa"])
            c3.metric("Expectativa Total (xG)", resultado["Gols Esp."])
            c4.metric("Volume (SoT)", resultado["Chutes (SoT)"])
            c5.metric("Status Operacional", resultado["Status"])

        if btn_adicionar:
            st.session_state["jogos_selecionados"].append(resultado)
            st.success(f"Confronto {mandante} x {visitante} adicionado à lista!")

    # 6. Exibição da Lista Acumulada
    if st.session_state["jogos_selecionados"]:
        st.divider()
        st.subheader("📋 Lista de Confrontos Selecionados")
        df_lista = pd.DataFrame(st.session_state["jogos_selecionados"])
        st.dataframe(df_lista, use_container_width=True, hide_index=True)
        
        if st.button("🗑️ Limpar Lista"):
            st.session_state["jogos_selecionados"] = []
            st.rerun()