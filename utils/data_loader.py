import json
import os
import pandas as pd
import streamlit as st

CAMINHO_HISTORICO_A = "data/base_gols_consolidada.csv"
CAMINHO_HISTORICO_B = "data/base_gols_plano_b.csv"
CAMINHO_JOGOS_DIA = "data/jogos_do_dia.csv"
CAMINHO_SOT_JSON = "data/sot_plano_b.json"


@st.cache_data(show_spinner=False)
def load_historical_data() -> pd.DataFrame:
  """Carrega e unifica o histórico de gols (Plano A e Plano B) em cache."""
  dfs = []

  # Base Plano A (10 Ligas Clássicas)
  if os.path.exists(CAMINHO_HISTORICO_A):
    df_a = pd.read_csv(CAMINHO_HISTORICO_A)
    dfs.append(df_a)
  else:
    st.warning(f"Arquivo não encontrado: '{CAMINHO_HISTORICO_A}'")

  # Base Plano B (9 Ligas Selecionadas)
  if os.path.exists(CAMINHO_HISTORICO_B):
    df_b = pd.read_csv(CAMINHO_HISTORICO_B)
    dfs.append(df_b)
  else:
    st.warning(f"Arquivo não encontrado: '{CAMINHO_HISTORICO_B}'")

  if dfs:
    df_unificado = pd.concat(dfs, ignore_index=True)
    return df_unificado

  st.error("Nenhuma base histórica foi encontrada na pasta 'data/'.")
  return pd.DataFrame()


@st.cache_data(ttl=600, show_spinner=False)
def load_daily_fixtures() -> pd.DataFrame:
  """Carrega a grade de jogos do dia."""
  if os.path.exists(CAMINHO_JOGOS_DIA):
    return pd.read_csv(CAMINHO_JOGOS_DIA)
  st.warning(f"Grade do dia ainda não gerada: '{CAMINHO_JOGOS_DIA}'")
  return pd.DataFrame()


@st.cache_data(ttl=86400, show_spinner=False)
def load_sot_database() -> dict:
  """Carrega o dicionário com as métricas de SoT auditadas para o Plano B."""
  if os.path.exists(CAMINHO_SOT_JSON):
    try:
      with open(CAMINHO_SOT_JSON, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception as e:
      st.error(f"Erro ao carregar '{CAMINHO_SOT_JSON}': {e}")
      return {}
  return {}