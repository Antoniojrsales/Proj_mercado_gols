import io
import os
import pandas as pd
import requests

URL_FIXTURES_A = "https://www.football-data.co.uk/fixtures.csv"
URL_FIXTURES_B = "https://www.football-data.co.uk/new_league_fixtures.csv"
ARQUIVO_SAIDA = os.path.join("data", "jogos_do_dia.csv")

DIVISOES_PLANO_A = {
    "E0": "Inglaterra_Premier",
    "SC0": "Escocia_Premiership",
    "D1": "Alemanha_Bundesliga",
    "I1": "Italia_SerieA",
    "SP1": "Espanha_LaLiga",
    "F1": "Franca_Ligue1",
    "N1": "Holanda_Eredivisie",
    "B1": "Belgica_Jupiler",
    "P1": "Portugal_Primeira",
    "T1": "Turquia_SuperLig",
}

# Mapeamento de País / Liga para as 9 competições do Plano B
LIGAS_PLANO_B = {
    "Norway": "Noruega_Eliteserien",
    "Switzerland": "Suica_SuperLeague",
    "Austria": "Austria_Bundesliga",
    "Denmark": "Dinamarca_Superliga",
    "USA": "EUA_MLS",
    "Sweden": "Suecia_Allsvenskan",
    "Brazil": "Brasil_Serie_A",
    "Mexico": "Mexico_LigaMX",
    "Japan": "Japao_JLeague",
}

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def obter_grade_plano_a() -> pd.DataFrame:
  """Descarrega a grade de partidas futuras das 10 ligas do Plano A."""
  try:
    print("A descarregar jogos futuros do Plano A (fixtures.csv)...")
    resp = requests.get(URL_FIXTURES_A, headers=headers, timeout=15)
    if resp.status_code != 200:
      print(f"Aviso Plano A: Status {resp.status_code}")
      return pd.DataFrame()

    conteudo = resp.content.decode("utf-8-sig", errors="replace")
    df = pd.read_csv(io.StringIO(conteudo))
    df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]

    coluna_div = next((c for c in df.columns if c.lower() == "div"), None)
    if not coluna_div:
      return pd.DataFrame()

    df = df[df[coluna_div].isin(DIVISOES_PLANO_A.keys())].copy()
    df["Liga"] = df[coluna_div].map(DIVISOES_PLANO_A)

    colunas = ["Date", "Time", "Liga", "HomeTeam", "AwayTeam"]
    return df[[c for c in colunas if c in df.columns]].dropna(
        subset=["HomeTeam", "AwayTeam"]
    )
  except Exception as e:
    print(f"Erro ao processar Plano A: {e}")
    return pd.DataFrame()


def obter_grade_plano_b() -> pd.DataFrame:
  """Descarrega a grade de partidas futuras das 9 ligas do Plano B."""
  try:
    print("A descarregar jogos futuros do Plano B (new_league_fixtures.csv)...")
    resp = requests.get(URL_FIXTURES_B, headers=headers, timeout=15)
    if resp.status_code != 200:
      print(f"Aviso Plano B: Status {resp.status_code}")
      return pd.DataFrame()

    try:
      conteudo = resp.content.decode("utf-8-sig")
    except UnicodeDecodeError:
      conteudo = resp.content.decode("latin1", errors="replace")

    df = pd.read_csv(io.StringIO(conteudo))
    df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]

    # Normalização de cabeçalhos do formato /new/
    rename_cols = {
        "Country": "Pais",
        "League": "Liga_Orig",
        "Date": "Date",
        "Time": "Time",
        "Home": "HomeTeam",
        "Away": "AwayTeam",
    }
    df.rename(columns=rename_cols, inplace=True)

    if "Pais" not in df.columns:
      return pd.DataFrame()

    df["Pais"] = df["Pais"].astype(str).str.strip()
    df = df[df["Pais"].isin(LIGAS_PLANO_B.keys())].copy()
    df["Liga"] = df["Pais"].map(LIGAS_PLANO_B)

    if "Time" not in df.columns:
      df["Time"] = "-"

    colunas = ["Date", "Time", "Liga", "HomeTeam", "AwayTeam"]
    return df[[c for c in colunas if c in df.columns]].dropna(
        subset=["HomeTeam", "AwayTeam"]
    )
  except Exception as e:
    print(f"Erro ao processar Plano B: {e}")
    return pd.DataFrame()


def gerar_grade_diaria():
  os.makedirs("data", exist_ok=True)

  df_a = obter_grade_plano_a()
  df_b = obter_grade_plano_b()

  dfs = [d for d in [df_a, df_b] if not d.empty]

  if not dfs:
    print("Nenhum confronto futuro localizado.")
    return

  df_grade = pd.concat(dfs, ignore_index=True)
  df_grade.drop_duplicates(
      subset=["Date", "HomeTeam", "AwayTeam"], inplace=True
  )
  df_grade.to_csv(ARQUIVO_SAIDA, index=False, encoding="utf-8-sig")

  print("\n" + "=" * 50)
  print(f"Sucesso! {len(df_grade)} confrontos gravados em '{ARQUIVO_SAIDA}'.")
  print(f"Total de ligas mapeadas com jogos futuros: {df_grade['Liga'].nunique()}")
  print("=" * 50)


if __name__ == "__main__":
  gerar_grade_diaria()