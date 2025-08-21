import jwt

def get_uid_from_token(token: str) -> str | None:
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get('sub')
    except Exception as e:
        print(f"Erro ao decodificar token: {e}")
        return None