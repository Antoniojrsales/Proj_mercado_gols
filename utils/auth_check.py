import streamlit as st

def check_login(mostrar_sidebar_user: bool = True):
  """Verifica se o usuário está autenticado.

  Se não estiver, redireciona para a página de login. Se estiver logado, exibe o
  usuário ativo e o botão de logout na barra lateral.
  """
  if not st.session_state.get('logged_in', False):
    st.warning('🔒 Você precisa estar logado para acessar esta página.')

    # Botão de redirecionamento ou redirecionamento automático
    col1, col2 = st.columns([1, 2])
    with col1:
      if st.button('Ir para Login', use_container_width=True, type="primary"):
        st.session_state.clear()
        st.switch_page("1_🗝️_login.py")

    st.stop()

  # Se estiver autenticado e a flag da sidebar estiver ativa
  if mostrar_sidebar_user:
    usuario_ativo = st.session_state.get('username', 'Usuário')
    with st.sidebar:
      st.markdown(f'👤 Conectado como: **{usuario_ativo}**')
      if st.button('🚪 Sair da Conta', key='btn_logout', type="primary", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state['username'] = None
        st.session_state.clear()
        st.switch_page("1_🗝️_login.py")
        st.rerun()