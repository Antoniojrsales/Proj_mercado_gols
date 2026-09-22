import os
import pandas as pd
import streamlit as st

CAMINHO_HISTORICO = "data/base_gols_consolidada.csv"
CAMINHO_JOGOS_DIA = "data/jogos_do_dia.csv"

@st.cache_data(show_spinner=False)
def load_historical_data() -> pd.DataFrame:
    """Carrega o histórico consolidado de gols em cache duradouro."""
    if os.path.exists(CAMINHO_HISTORICO):
        return pd.read_csv(CAMINHO_HISTORICO)
    st.error(f"Arquivo não encontrado: '{CAMINHO_HISTORICO}'")
    return pd.DataFrame()

@st.cache_data(ttl=600, show_spinner=False)
def load_daily_fixtures() -> pd.DataFrame:
    """Carrega a grade de jogos do dia."""
    if os.path.exists(CAMINHO_JOGOS_DIA):
        return pd.read_csv(CAMINHO_JOGOS_DIA)
    st.warning(f"Grade do dia ainda não gerada: '{CAMINHO_JOGOS_DIA}'")
    return pd.DataFrame()