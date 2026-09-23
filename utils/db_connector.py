import hashlib
import hmac
import streamlit as st


def authenticate_user(username: str, password_input: str) -> bool:
  """Valida as credenciais comparando o hash SHA-256 com tempo constante (anti-timing attack)."""
  if not username or not password_input:
    return False

  try:
    users = st.secrets.get("AUTH_USERS", {})
  except Exception:
    return False

  if username not in users:
    return False

  stored_hash = str(users[username]).strip()
  input_hash = hashlib.sha256(password_input.encode("utf-8")).hexdigest()

  return hmac.compare_digest(input_hash, stored_hash)       
  