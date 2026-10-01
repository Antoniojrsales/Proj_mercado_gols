from datetime import datetime
import math
from typing import Dict, Optional, Tuple
import pandas as pd

MERCADO = [
    "Over 0.5 FT",
    "Over 0.5 HT",
    "Over 1.5 FT",
    "Over 2.5 FT",
    "BTTS",
]


def poisson_prob(k: int, lmbda: float) -> float:
  """Calcula a probabilidade pontual P(X = k) via Distribuição de Poisson."""
  if lmbda <= 0:
    return 1.0 if k == 0 else 0.0
  return (math.exp(-lmbda) * (lmbda**k)) / math.factorial(k)


def compute_league_stats(
    df_liga: pd.DataFrame,
    sot_db: Optional[dict] = None,
    pais: Optional[str] = None,
) -> Tuple[Dict[str, dict], float, float]:
  """Calcula as médias da liga e a força ofensiva/defensiva de cada clube,

  integrando dados nativos de remates (Plano A), JSON auditado ou Proxy
  calibrado (Plano B).
  """
  times = sorted(
      list(
          set(df_liga["HomeTeam"].dropna().unique())
          | set(df_liga["AwayTeam"].dropna().unique())
      )
  )

  media_c = df_liga["FTHG"].mean() if not df_liga.empty else 1.5
  media_f = df_liga["FTAG"].mean() if not df_liga.empty else 1.2

  # Evita divisão por zero
  media_c = media_c if media_c > 0 else 1.5
  media_f = media_f if media_f > 0 else 1.2

  # 1. Verifica se temos dados nativos reais de remates (Plano A)
  tem_sot_nativo = (
      "HST" in df_liga.columns
      and "AST" in df_liga.columns
      and (df_liga["HST"].sum() + df_liga["AST"].sum() > 0)
  )

  # 2. Identifica o país para consulta ao JSON caso não tenha SoT nativo
  if not pais and "Pais" in df_liga.columns and not df_liga.empty:
    serie_pais = df_liga["Pais"].dropna()
    if not serie_pais.empty:
      pais = str(serie_pais.iloc[0]).strip()

  # Mapeamento de fallback pelo nome da Liga caso 'Pais' não exista
  if not pais and "Liga" in df_liga.columns and not df_liga.empty:
    nome_liga = str(df_liga["Liga"].dropna().iloc[0]).lower()
    mapa_liga_pais = {
        "suica": "Switzerland",
        "suecia": "Sweden",
        "noruega": "Norway",
        "dinamarca": "Denmark",
        "austria": "Austria",
        "brasil": "Brazil",
        "mexico": "Mexico",
        "japao": "Japan",
        "eua": "USA",
    }
    for chave, nome_pais in mapa_liga_pais.items():
      if chave in nome_liga:
        pais = nome_pais
        break

  dados_pais_json = sot_db.get(pais, {}) if (sot_db and pais) else {}

  stats = {}

  for t in times:
    j_casa = df_liga[df_liga["HomeTeam"] == t]
    j_fora = df_liga[df_liga["AwayTeam"] == t]
    tot = len(j_casa) + len(j_fora)

    if tot == 0:
      continue

    gp_c = j_casa["FTHG"].mean() if len(j_casa) > 0 else media_c
    gs_c = j_casa["FTAG"].mean() if len(j_casa) > 0 else media_f
    gp_f = j_fora["FTAG"].mean() if len(j_fora) > 0 else media_f
    gs_f = j_fora["FTHG"].mean() if len(j_fora) > 0 else media_c

    # Média geral de golos do clube para o proxy
    media_gols_feita = (
        (j_casa["FTHG"].sum() + j_fora["FTAG"].sum()) / tot if tot > 0 else 1.2
    )
    media_gols_sofrida = (
        (j_casa["FTAG"].sum() + j_fora["FTHG"].sum()) / tot if tot > 0 else 1.2
    )

    # Determinação do Volume de Remates (SoT pró e SoTA contra)
    origem_sot = "nativo"
    if tem_sot_nativo:
      sot = (j_casa["HST"].sum() + j_fora["AST"].sum()) / tot
      sota = (j_casa["AST"].sum() + j_fora["HST"].sum()) / tot
    elif dados_pais_json and t in dados_pais_json:
      sot = dados_pais_json[t].get("sot_pro", media_gols_feita * 2.80)
      sota = dados_pais_json[t].get("sot_contra", media_gols_sofrida * 2.80)
      origem_sot = "auditado"
    else:
      # Proxy calibrado (Golos * 2.80)
      sot = round(media_gols_feita * 2.80, 2)
      sota = round(media_gols_sofrida * 2.80, 2)
      origem_sot = "proxy"

    stats[t] = {
        "GP_Casa": gp_c,
        "GS_Casa": gs_c,
        "GP_Fora": gp_f,
        "GS_Fora": gs_f,
        "SoT": sot,
        "SoTA": sota,
        "Origem_SoT": origem_sot,
    }

  return stats, media_c, media_f


def calculate_match_lambdas(
    data: datetime.date,
    home_team: str,
    away_team: str,
    stats_liga: dict,
    media_c: float,
    media_f: float,
) -> Tuple[float, float, float, float, str]:
  """Calcula a expectativa de golos (lambda) para mandante, visitante,

  volume combinado de remates e a origem da métrica.
  """

  def encontrar_stats_time(nome: str):
    if not nome or not stats_liga:
      return None
    nome_alvo = str(nome).strip().lower()

    # 1. Correspondência exata
    for t, dados in stats_liga.items():
      if str(t).strip().lower() == nome_alvo:
        return dados

    # 2. Correspondência parcial
    for t, dados in stats_liga.items():
      nome_historico = str(t).strip().lower()
      if nome_alvo in nome_historico or nome_historico in nome_alvo:
        return dados

    return None

  stats_c = encontrar_stats_time(home_team)
  stats_f = encontrar_stats_time(away_team)

  # Fallback caso o clube seja estreante ou não conste na temporada
  if not stats_c or not stats_f:
    return media_c, media_f, media_c + media_f, 9.0, "proxy"

  l_c = (stats_c["GP_Casa"] / media_c) * (stats_f["GS_Fora"] / media_c) * media_c
  l_f = (stats_f["GP_Fora"] / media_f) * (stats_c["GS_Casa"] / media_f) * media_f
  l_total = l_c + l_f
  vol_sot = stats_c["SoT"] + stats_f["SoTA"]

  origem_sot = stats_c.get("Origem_SoT", "nativo")

  return l_c, l_f, l_total, vol_sot, origem_sot


# =========================================================
# FUNÇÕES ESPECIALIZADAS POR MERCADO
# =========================================================


def calc_over_05_ft(l_c: float, l_f: float) -> float:
  """Calcula probabilidade de Over 0.5 FT (> 0 golos)."""
  p_0_0 = poisson_prob(0, l_c) * poisson_prob(0, l_f)
  return max(0.0, min(1.0, 1.0 - p_0_0))


def calc_over_15_ft(l_c: float, l_f: float) -> float:
  """Calcula probabilidade de Over 1.5 FT (> 1 golo)."""
  p_under = (
      (poisson_prob(0, l_c) * poisson_prob(0, l_f))
      + (poisson_prob(1, l_c) * poisson_prob(0, l_f))
      + (poisson_prob(0, l_c) * poisson_prob(1, l_f))
  )
  return max(0.0, min(1.0, 1.0 - p_under))


def calc_over_25_ft(l_c: float, l_f: float) -> float:
  """Calcula probabilidade de Over 2.5 FT (> 2 golos)."""
  p_under = 0.0
  for i in range(3):
    for j in range(3):
      if i + j <= 2:
        p_under += poisson_prob(i, l_c) * poisson_prob(j, l_f)
  return max(0.0, min(1.0, 1.0 - p_under))


def calc_over_05_ht(l_c: float, l_f: float, ht_ratio: float = 0.44) -> float:
  """Calcula probabilidade de Over 0.5 HT (golos no 1º tempo)."""
  l_c_ht = l_c * ht_ratio
  l_f_ht = l_f * ht_ratio
  p_0_0_ht = poisson_prob(0, l_c_ht) * poisson_prob(0, l_f_ht)
  return max(0.0, min(1.0, 1.0 - p_0_0_ht))


def calc_btts(l_c: float, l_f: float) -> float:
  """Calcula probabilidade de Ambas as Equipas Marcarem (BTTS)."""
  p_home_scores = 1.0 - poisson_prob(0, l_c)
  p_away_scores = 1.0 - poisson_prob(0, l_f)
  return max(0.0, min(1.0, p_home_scores * p_away_scores))


# =========================================================
# ORQUESTRADOR DE ANÁLISE DE CONFRONTO
# =========================================================


def analyze_match_signal(
    data: datetime.date,
    home_team: str,
    away_team: str,
    mercado: str,
    stats_liga: dict,
    media_c: float,
    media_f: float,
    corte_minimo_pct: float,
    odd_mercado: float = 0.0,
) -> Dict:
  """Processa a probabilidade do mercado escolhido, odd justa e status."""
  l_c, l_f, l_total, vol_sot, origem_sot = calculate_match_lambdas(
      data, home_team, away_team, stats_liga, media_c, media_f
  )

  # Roteamento do Mercado
  if mercado == "Over 0.5 FT":
    prob = calc_over_05_ft(l_c, l_f)
    min_exp_gols = 1.35
  elif mercado == "Over 1.5 FT":
    prob = calc_over_15_ft(l_c, l_f)
    min_exp_gols = 2.65
  elif mercado == "Over 2.5 FT":
    prob = calc_over_25_ft(l_c, l_f)
    min_exp_gols = 2.85
  elif mercado == "Over 0.5 HT":
    prob = calc_over_05_ht(l_c, l_f)
    min_exp_gols = 2.35
  elif mercado in ["BTTS", "BTTS (Ambas Marcam)"]:
    prob = calc_btts(l_c, l_f)
    min_exp_gols = 2.55
  else:
    prob = calc_over_15_ft(l_c, l_f)
    min_exp_gols = 2.65

  prob_pct = prob * 100.0
  odd_justa = (1.0 / prob) if prob > 0 else 0.0
  ev_pct = ((prob * odd_mercado) - 1.0) * 100.0 if odd_mercado > 1.0 else 0.0

  # Regra de Aprovação
  aprovado = (prob_pct >= corte_minimo_pct) and (l_total >= min_exp_gols)

  # Sufixo para transparência de dados
  rotulo_origem = " (ESTIMADO)" if origem_sot == "proxy" else ""

  if not aprovado:
    status = "REPROVADO"
  elif vol_sot < 9.5:
    status = "ALERTA (VOLUME BAIXO)"
  elif odd_mercado > 1.0 and ev_pct <= 0:
    status = "ALERTA (ODD BAIXA)"
  elif odd_mercado > 1.0 and ev_pct > 0:
    status = f"APROVADO 100% (+EV){rotulo_origem}"
  else:
    status = f"APROVADO (SEM ODD){rotulo_origem}"

  ev_str = (
      f"+{ev_pct:.1f}%"
      if ev_pct > 0
      else (f"{ev_pct:.1f}%" if odd_mercado > 1.0 else "-")
  )

  return {
      "Confronto": f"{home_team} x {away_team}",
      "Mandante": home_team,
      "Visitante": away_team,
      "Data": data,
      "Prob (%)": round(prob_pct, 1),
      "Odd Justa": round(odd_justa, 2),
      "Odd Casa": odd_mercado if odd_mercado > 0 else "-",
      "Chutes (SoT)": round(vol_sot, 1),
      "Gols Esp.": round(l_total, 2),
      "+EV (%)": ev_str,
      "Status": status,
  }