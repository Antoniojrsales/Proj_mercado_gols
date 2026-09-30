import streamlit as st
from utils.auth_check import check_login
from utils.data_loader import load_daily_fixtures
from utils.data_processing import sanitize_daily_fixtures

st.set_page_config(
    page_title='Tabela | Jogos do Dia', 
    page_icon='⚽', 
    layout='centered')

check_login()

st.sidebar.markdown('Desenvolvido por [AntonioJrSales](https://antoniojrsales.github.io/Proj_PunterSomenteMercadoGols/)')


st.title('⚽ Grade de Jogos do Dia')
st.caption('Visão geral das partidas programadas para a data e segmentação por liga.', unsafe_allow_html=True)
st.divider()

# 3. Carregamento dos Dados
df_bruto = load_daily_fixtures()
df_jogos_dia = sanitize_daily_fixtures(df_bruto)

if df_jogos_dia.empty:
    st.warning('Nenhum jogo encontrado ou arquivo da grade ainda não atualizado.') 
    st.stop()

col1, col2 = st.columns(2)
col1.metric('Total de Jogos', len(df_jogos_dia))

# Assume que a coluna de liga se chame 'campeonato' ou 'league' (ajustar conforme seu CSV)
col_campeonato = 'Liga' if 'Liga' in df_jogos_dia.columns else df_jogos_dia.columns[0]
ligas = df_jogos_dia[col_campeonato].nunique()
col2.metric('Total de Ligas', ligas)

st.write('---')

# 5. Filtros Interativos
with st.sidebar:
    st.header('Filtros de Pesquisa')
    st.caption('Selecione a Liga desejada para filtrar os jogos do dia.', unsafe_allow_html=True)
    campeonatos_disponiveis = sorted(df_jogos_dia[col_campeonato].dropna().unique())
    filtro_liga = st.multiselect('Selecione a Liga', options=campeonatos_disponiveis, placeholder='Selecione um ou mais campeonatos (deixe vazio para ver todos)', default=campeonatos_disponiveis)

# Aplicação do Filtro
df_jogos_filtrados = df_jogos_dia.copy()
if filtro_liga:
    df_jogos_filtrados = df_jogos_filtrados[df_jogos_filtrados[col_campeonato].isin(filtro_liga)]

# 6. Exibição da Grade
st.dataframe(
    df_jogos_filtrados,
    width='stretch',
    hide_index=True
)