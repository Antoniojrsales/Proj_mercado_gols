import pandas as pd
import streamlit as st
from utils.auth_check import check_login
from utils.data_loader import (
    load_daily_fixtures,
    load_historical_data,
    load_sot_database,  # <-- 1. Importa a base auditada de remates
)
from utils.data_processing import (
    sanitize_daily_fixtures,
    sanitize_historical_data,
)
from utils.engine import MERCADO, analyze_match_signal, compute_league_stats

# ---------------------------------------------------------
# ⚙️ CONFIGURAÇÕES DE INTERFACE
# ---------------------------------------------------------
st.set_page_config(
    page_title="Tendências | Inteligência Mercado de Gols",
    page_icon="📊",
    layout="wide",
)

# 1. Barreira de Segurança
check_login()

with st.sidebar:
  with st.expander("ℹ️ Sobre o Mercado de Gols", expanded=False):
    st.markdown("""
            Abaixo segue algumas parâmetros mínimos sugeridos para o Mercado de Gols.

            **Mercados Analisados:**
            * **Over 0.5 FT:** a partir de **90%** (mercado de altíssima frequência)
            * **Over 1.5 FT:** a partir de **80%** (padrão equilibrado para gols)
            * **Over 2.5 FT:** a partir de **70%** (jogos com perfil ofensivo aberto)
            * **Over 0.5 HT:** a partir de **65% a 70%** (foco em gols na 1ª etapa)
            * **BTTS (Ambos Marcam):** a partir de **60% a 65%** (ambas as equipas marcam)

            **Observações:**
            * Quanto mais próximo de **100%** for a linha de corte, maior a probabilidade teórica do sinal, porém menor será a Odd oferecida pela casa.      
            """)

st.sidebar.markdown(
    "Desenvolvido por"
    " [AntonioJrSales](https://antoniojrsales.github.io/Proj_PunterSomenteMercadoGols/)"
)

# ---------------------------------------------------------
# 📥 CARREGAMENTO E HIGIENIZAÇÃO DE DADOS
# ---------------------------------------------------------
df_historico_raw = load_historical_data()
df_jogos_raw = load_daily_fixtures()
sot_db = load_sot_database()  # <-- 2. Carrega o dicionário JSON em cache

if df_historico_raw.empty or df_jogos_raw.empty:
  st.warning(
      "⚠️ Dados históricos ou grade de jogos indisponíveis para processamento."
  )
  st.stop()

df_historico = sanitize_historical_data(df_historico_raw)
df_jogos = sanitize_daily_fixtures(df_jogos_raw)

# ---------------------------------------------------------
# 🎛️ CONTROLES E PARÂMETROS NA SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
  st.markdown("### ⚙️ Filtros Analíticos")

  datas_disponiveis = sorted(df_jogos["Date"].dropna().unique())
  filtro_datas = st.multiselect(
      "Datas da Rodada:",
      options=datas_disponiveis,
      default=[],  # Vazio = todas as datas
      placeholder="Todas as Datas",
      help="Selecione um ou mais dias específicos da rodada para filtrar.",
  )

  # Filtro de Liga
  ligas_disponiveis = sorted(df_jogos["Liga"].dropna().unique())
  filtro_ligas = st.multiselect(
      "Campeonatos:", options=ligas_disponiveis, placeholder="Todas as Ligas"
  )

  filtro_mercados = st.selectbox(
      "Mercados:",
      options=MERCADO,
      index=0,
  )

  sugestao_corte = {
      "Over 0.5 FT": 90,
      "Over 0.5 HT": 65,
      "Over 1.5 FT": 80,
      "Over 2.5 FT": 70,
      "BTTS": 65,
  }
  valor_padrao = sugestao_corte.get(filtro_mercados, 80)

  corte_minimo = st.slider(
      "Probabilidade Mínima (%):",
      min_value=50,
      max_value=99,
      value=valor_padrao,
      step=1,
      help=(
          "Exibe apenas jogos com probabilidade matemática igual ou superior ao"
          " corte."
      ),
  )

  total_partidas = max(len(df_jogos), 1)
  top_n = st.number_input(
      "Top Oportunidades:",
      min_value=1,
      max_value=total_partidas,
      value=min(10, total_partidas),
      step=1,
      help="Quantidade de melhores sinais a exibir no ranking.",
  )

# ---------------------------------------------------------
# 🧠 PROCESSAMENTO DO MOTOR QUANTITATIVO
# ---------------------------------------------------------
df_alvo = df_jogos.copy()

if filtro_datas:
  df_alvo = df_alvo[df_alvo["Date"].isin(filtro_datas)]

if filtro_ligas:
  df_alvo = df_alvo[df_alvo["Liga"].isin(filtro_ligas)]

resultados = []
cache_stats_ligas = {}

for _, row in df_alvo.iterrows():
  liga_jogo = str(row.get("Liga")).replace("_", " ").strip()
  time_casa = row.get("HomeTeam")
  time_fora = row.get("AwayTeam")
  data_jogo = row.get("Date")
  hora_jogo = row.get("Time", "-")

  # 1. Carrega as estatísticas da liga passando o sot_db
  if liga_jogo not in cache_stats_ligas:
    df_sub_liga = df_historico[
        df_historico["Liga"].astype(str).str.replace("_", " ").str.strip()
        == liga_jogo
    ]
    if not df_sub_liga.empty:
      # Passa o sot_db para buscar as médias auditadas do FBref
      stats_l, med_c, med_f = compute_league_stats(
          df_sub_liga, sot_db=sot_db
      )
      cache_stats_ligas[liga_jogo] = (stats_l, med_c, med_f)
    else:
      cache_stats_ligas[liga_jogo] = ({}, 1.5, 1.2)

  stats_l, med_c, med_f = cache_stats_ligas[liga_jogo]

  # 2. Executa a inferência passando a data correta da partida
  analise = analyze_match_signal(
      data=data_jogo,
      home_team=time_casa,
      away_team=time_fora,
      mercado=filtro_mercados,
      stats_liga=stats_l,
      media_c=med_c,
      media_f=med_f,
      corte_minimo_pct=corte_minimo,
      odd_mercado=0.0,
  )

  analise["Data"] = data_jogo
  analise["Hora"] = hora_jogo
  analise["Liga"] = liga_jogo

  resultados.append(analise)

df_resultado = pd.DataFrame(resultados)

# ---------------------------------------------------------
# 📊 APRESENTAÇÃO DA INTERFACE
# ---------------------------------------------------------
st.title("📈 Tendências & Sinais: Inteligência Mercado de Gols")
st.caption(
    "Classificação quantitativa por modelo de Poisson e expectativa de gols."
)
st.divider()

if df_resultado.empty:
  st.info("Nenhuma partida encontrada para os critérios selecionados.")
  st.stop()

# Filtro de corte e ordenação
df_filtrado_corte = df_resultado[
    df_resultado["Prob (%)"] >= corte_minimo
].copy()

df_ranking = df_filtrado_corte.sort_values(
    by=["Prob (%)", "Gols Esp."], ascending=[False, False]
).head(int(top_n))

# Métricas de Cabeçalho
m1, m2, m3 = st.columns(3)
m1.metric("Jogos Analisados", len(df_alvo))
m2.metric("Qualificados no Corte", len(df_filtrado_corte))
m3.metric("Exibindo Top", len(df_ranking))

st.write("")

# Configuração e Exibição da Tabela
colunas_ordem = [
    "Data",
    "Hora",
    "Liga",
    "Confronto",
    "Prob (%)",
    "Odd Justa",
    "Gols Esp.",
    "Chutes (SoT)",
    "Status",
]
df_exibicao = df_ranking[
    [col for col in colunas_ordem if col in df_ranking.columns]
]

st.dataframe(
    df_exibicao,
    width="stretch",
    hide_index=True,
    column_config={
        "Prob (%)": st.column_config.ProgressColumn(
            "Probabilidade", format="%.1f%%", min_value=50, max_value=100
        ),
        "Odd Justa": st.column_config.NumberColumn("Odd Justa", format="%.2f"),
        "Gols Esp.": st.column_config.NumberColumn(
            "Expectativa (xG)", format="%.2f"
        ),
        "Chutes (SoT)": st.column_config.NumberColumn(
            "Volume SoT", format="%.1f"
        ),
    },
)