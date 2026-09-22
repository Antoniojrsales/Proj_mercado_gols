import streamlit as st

def authenticate_user(username: str, password_input: str) -> bool:
  """Valida se o usuário existe e se a senha confere com o secrets.toml."""
  try:
    users = st.secrets.get("AUTH_USERS", {})
  except Exception:
    return False

  # Se o usuário não existir no arquivo, rejeita
  if username not in users:
    return False

  # Retorna True se a senha bater, False se for incorreta
  return str(users[username]) == str(password_input)
  """Carrega as credenciais em cache."""
  user = get_user_credentials(username)
  if user is not None:
    return user

  st.error(f"Usuário '{username}' não encontrado.")
  return None