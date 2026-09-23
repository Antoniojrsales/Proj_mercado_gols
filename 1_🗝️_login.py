# ---------------------------------------------------------
# 📚 BIBLIOTECAS E RECURSOS INTERNOS
# ---------------------------------------------------------
import streamlit as st
from utils.db_connector import authenticate_user

# ---------------------------------------------------------
# ⚙️ CONFIGURAÇÕES INICIAIS DA INTERFACE (STREAMLIT)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Login | Intengencia Mercado de Gols", 
    page_icon="🔐", 
    layout="centered")

with st.sidebar:
    with st.expander("ℹ️ Sobre o Sistema"):
        st.markdown(
            """
            Plataforma de análise quantitativa para acompanhamento de tendências e métricas no mercado de futebol.

            **Mercados Analisados:**
            * **Over 0.5 HT:** +0.5 gols no 1º tempo.
            * **Over 0.5 FT:** +0.5 gols na partida.
            * **Over 1.5 FT:** +1.5 gols na partida.
            * **Over 2.5 FT:** +2.5 gols na partida.
            * **BTTS:** Ambas as equipes marcam.        
            """
        )

st.sidebar.markdown('Desenvolvido por [AntonioJrSales](https://antoniojrsales.github.io/meu_portfolio/)')

# ---------------------------------------------------------
# 🎨 UTILITÁRIOS DE ESTILIZAÇÃO (CSS)
# ---------------------------------------------------------
def local_css(file_name):
    try:
        with open(file_name) as f:
           st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

# ---------------------------------------------------------
# 🔐 SE O USUÁRIO JÁ ESTIVER LOGADO
# ---------------------------------------------------------
ROTA_DESTINO = "pages/2_⚽_jogosdia.py"

if st.session_state.get("logged_in", False):
  st.success(
      f"Você já está conectado como **{st.session_state.get('username')}**."
  )
  if st.button("Acessar Painel de Jogos", use_container_width=True):
    st.switch_page(ROTA_DESTINO)
  st.stop()

local_css('css/style_button_login.css')

# ---------------------------------------------------------
# 🎨 RENDERIZAÇÃO DO FORMULÁRIO DE LOGIN
# ---------------------------------------------------------
with st.form("login_form"):
    st.markdown("<h1 style='text-align: center;'>🔐 Login</h1>", unsafe_allow_html=True)
    st.caption("Acesso restrito para analistas e assinantes", unsafe_allow_html=True)
    st.divider()

    username = st.text_input("👤 Usuário").strip()
    password = st.text_input("🔒 Senha", type="password").strip()

    submit = st.form_submit_button("Entrar", use_container_width=True)

# ---------------------------------------------------------
# 🚀 VALIDAÇÃO E PROCESSAMENTO DO LOGIN
# ---------------------------------------------------------
if submit:
    if not username or not password:
        st.warning("Por favor, preencha todos os campos.")
    else:
        if authenticate_user(username, password):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.success(f"Bem-vindo(a), **{username}**! Login realizado com sucesso.")
            st.switch_page("pages/2_⚽_jogosdia.py")
        else:
            st.error("Usuário ou senha inválidos. Tente novamente.")    