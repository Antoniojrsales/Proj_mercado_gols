import math
from typing import Dict, Optional, Tuple
import pandas as pd
from datetime import datetime

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
) -> Tuple[Dict[str, dict], float, float]:
  """Calcula as médias da liga e força ofensiva/defensiva de cada clube."""
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

  stats = {}
  tem_sot = "HST" in df_liga.columns and "AST" in df_liga.columns

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

    sot = (
        (j_casa["HST"].sum() + j_fora["AST"].sum()) / tot if tem_sot else 4.5
    )
    sota = (
        (j_casa["AST"].sum() + j_fora["HST"].sum()) / tot if tem_sot else 4.5
    )

    stats[t] = {
        "GP_Casa": gp_c,
        "GS_Casa": gs_c,
        "GP_Fora": gp_f,
        "GS_Fora": gs_f,
        "SoT": sot,
        "SoTA": sota,
    }

  return stats, media_c, media_f


def calculate_match_lambdas(
    data: datetime.date,
    home_team: str,
    away_team: str,
    stats_liga: dict,
    media_c: float,
    media_f: float,
) -> Tuple[float, float, float, float]:
    """Calcula a expectativa de gols (lambda) para mandante, visitante e volume de chutes."""
    
    # Função auxiliar para buscar time ignorando maiúsculas e aceitando correspondência parcial
    def encontrar_stats_time(nome: str):
        if not nome or not stats_liga:
            return None
        nome_alvo = str(nome).strip().lower()
        
        # 1. Busca exata (ignorando case/espaços)
        for t, dados in stats_liga.items():
            if str(t).strip().lower() == nome_alvo:
                return dados
                
        # 2. Busca parcial (ex: "Standard" dentro de "Standard Liege")
        for t, dados in stats_liga.items():
            nome_historico = str(t).strip().lower()
            if nome_alvo in nome_historico or nome_historico in nome_alvo:
                return dados
                
        return None

    stats_c = encontrar_stats_time(home_team)
    stats_f = encontrar_stats_time(away_team)

    # Fallback caso o clube seja estreante ou não conste no histórico da temporada
    if not stats_c or not stats_f:
        return media_c, media_f, media_c + media_f, 9.0

    l_c = (stats_c["GP_Casa"] / media_c) * (stats_f["GS_Fora"] / media_c) * media_c
    l_f = (stats_f["GP_Fora"] / media_f) * (stats_c["GS_Casa"] / media_f) * media_f
    l_total = l_c + l_f
    vol_sot = stats_c["SoT"] + stats_f["SoTA"]

    return l_c, l_f, l_total, vol_sot


# =========================================================
# FUNÇÕES ESPECIALIZADAS POR MERCADO
# =========================================================


def calc_over_05_ft(l_c: float, l_f: float) -> float:
  """Calcula probabilidade de Over 0.5 FT (> 0 gols)."""
  p_0_0 = poisson_prob(0, l_c) * poisson_prob(0, l_f)
  return max(0.0, min(1.0, 1.0 - p_0_0))


def calc_over_15_ft(l_c: float, l_f: float) -> float:
  """Calcula probabilidade de Over 1.5 FT (> 1 gol)."""
  p_under = (
      (poisson_prob(0, l_c) * poisson_prob(0, l_f))
      + (poisson_prob(1, l_c) * poisson_prob(0, l_f))
      + (poisson_prob(0, l_c) * poisson_prob(1, l_f))
  )
  return max(0.0, min(1.0, 1.0 - p_under))


def calc_over_25_ft(l_c: float, l_f: float) -> float:
  """Calcula probabilidade de Over 2.5 FT (> 2 gols)."""
  p_under = 0.0
  for i in range(3):
    for j in range(3):
      if i + j <= 2:
        p_under += poisson_prob(i, l_c) * poisson_prob(j, l_f)
  return max(0.0, min(1.0, 1.0 - p_under))


def calc_over_05_ht(
    l_c: float, l_f: float, ht_ratio: float = 0.44
) -> float:
  """Calcula probabilidade de Over 0.5 HT (gols no 1º tempo)."""
  l_c_ht = l_c * ht_ratio
  l_f_ht = l_f * ht_ratio
  p_0_0_ht = poisson_prob(0, l_c_ht) * poisson_prob(0, l_f_ht)
  return max(0.0, min(1.0, 1.0 - p_0_0_ht))


def calc_btts(l_c: float, l_f: float) -> float:
  """Calcula probabilidade de Ambas as Equipes Marcarem (BTTS)."""
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
  """Processa a probabilidade do mercado escolhido, odd justa e status +EV."""
  l_c, l_f, l_total, vol_sot = calculate_match_lambdas(
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

  # Regra de Aprovação com corte do usuário
  aprovado = (prob_pct >= corte_minimo_pct) and (l_total >= min_exp_gols)

  if not aprovado:
    status = "REPROVADO"
  elif vol_sot < 9.5:
    status = "ALERTA (VOLUME BAIXO)"
  elif odd_mercado > 1.0 and ev_pct <= 0:
    status = "ALERTA (ODD BAIXA)"
  elif odd_mercado > 1.0 and ev_pct > 0:
    status = "APROVADO 100% (+EV)"
  else:
    status = "APROVADO (SEM ODD)"

  ev_str = f"+{ev_pct:.1f}%" if ev_pct > 0 else (f"{ev_pct:.1f}%" if odd_mercado > 1.0 else "-")

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