import numpy as np
import pandas as pd
from scipy.stats import poisson
import streamlit as st


def sanitize_daily_fixtures(df: pd.DataFrame) -> pd.DataFrame:
  """Higieniza e padroniza a grade de jogos futuros do dia."""
  if df is None or df.empty:
    return pd.DataFrame()

  df_clean = df.copy()

  # Normaliza nomes de colunas comuns
  if "Hora" in df_clean.columns and "Time" not in df_clean.columns:
    df_clean["Time"] = df_clean["Hora"]
  elif "Time" not in df_clean.columns:
    df_clean["Time"] = "-"

  if "Liga" in df_clean.columns:
    df_clean["Liga"] = (
        df_clean["Liga"].astype(str).str.replace("_", " ").str.strip()
    )

  if "HomeTeam" in df_clean.columns:
    df_clean["HomeTeam"] = df_clean["HomeTeam"].astype(str).str.strip()
  if "AwayTeam" in df_clean.columns:
    df_clean["AwayTeam"] = df_clean["AwayTeam"].astype(str).str.strip()

  # Padronização de Data
  if "Date" in df_clean.columns:
    try:
      df_clean["Date"] = pd.to_datetime(
          df_clean["Date"], dayfirst=True
      ).dt.strftime("%d/%m/%Y")
    except Exception:
      df_clean["Date"] = df_clean["Date"].astype(str).str.strip()

  df_clean["X"] = "x"

  ordem_colunas = [
      c
      for c in ["Date", "Time", "Liga", "HomeTeam", "X", "AwayTeam"]
      if c in df_clean.columns
  ]
  return df_clean[ordem_colunas]


def sanitize_historical_data(df: pd.DataFrame) -> pd.DataFrame:
  """Higieniza os dados históricos consolidados e gera as features analíticas de gols."""
  if df is None or df.empty:
    return pd.DataFrame()

  df_clean = df.copy()

  # Harmoniza o nome da Liga
  if "Liga" in df_clean.columns:
    df_clean["Liga"] = (
        df_clean["Liga"].astype(str).str.replace("_", " ").str.strip()
    )

  # Harmoniza o nome do País (essencial para buscar no JSON de SoT)
  if "Pais" in df_clean.columns:
    df_clean["Pais"] = df_clean["Pais"].astype(str).str.strip()

  if "HomeTeam" in df_clean.columns:
    df_clean["HomeTeam"] = df_clean["HomeTeam"].astype(str).str.strip()

  if "AwayTeam" in df_clean.columns:
    df_clean["AwayTeam"] = df_clean["AwayTeam"].astype(str).str.strip()

  # 1. Tratamento de Datas com ordenação cronológica
  if "Date" in df_clean.columns:
    df_clean["Date"] = pd.to_datetime(
        df_clean["Date"], dayfirst=True, errors="coerce"
    )
    df_clean = df_clean.sort_values(by="Date").reset_index(drop=True)

  # 2. Descarte de partidas sem resultado final
  colunas_essenciais = ["FTHG", "FTAG"]
  for col in colunas_essenciais:
    if col in df_clean.columns:
      df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")

  if all(col in df_clean.columns for col in colunas_essenciais):
    df_clean = df_clean.dropna(subset=colunas_essenciais)

  # 3. Tratamento de placares do intervalo (HT)
  colunas_ht = ["HTHG", "HTAG"]
  for col in colunas_ht:
    if col in df_clean.columns:
      df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce").fillna(0)

  # 4. Tratamento de Chutes a Gol (HST / AST)
  colunas_sot = ["HST", "AST"]
  for col in colunas_sot:
    if col in df_clean.columns:
      df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce").fillna(0)

  # 5. Marcadores de Gols no Intervalo (HT)
  if "HTHG" in df_clean.columns and "HTAG" in df_clean.columns:
    df_clean["TotalGols_HT"] = df_clean["HTHG"] + df_clean["HTAG"]
    df_clean["Over05_HT"] = (df_clean["TotalGols_HT"] > 0.5).astype(int)

  # 6. Marcadores de Gols no Jogo Completo (FT) e Ambas Marcam
  if "FTHG" in df_clean.columns and "FTAG" in df_clean.columns:
    df_clean["TotalGols_FT"] = df_clean["FTHG"] + df_clean["FTAG"]
    df_clean["Over05_FT"] = (df_clean["TotalGols_FT"] > 0.5).astype(int)
    df_clean["Over15_FT"] = (df_clean["TotalGols_FT"] > 1.5).astype(int)
    df_clean["Over25_FT"] = (df_clean["TotalGols_FT"] > 2.5).astype(int)
    df_clean["BTTS"] = (
        (df_clean["FTHG"] > 0) & (df_clean["FTAG"] > 0)
    ).astype(int)

  return df_clean


@st.cache_data(show_spinner=False)
def get_processed_dashboard_data(df_raw: pd.DataFrame) -> pd.DataFrame:
  """Pipeline completo de orquestração do ETL com cache de dados."""
  return sanitize_historical_data(df_raw)