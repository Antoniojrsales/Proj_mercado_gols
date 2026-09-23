import streamlit as st
from utils.auth_check import check_login

check_login()

st.info('Bem-vindo ao Painel de Jogos do Dia!')