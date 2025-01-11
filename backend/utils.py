from passlib.context import CryptContext
from jose import JWTError, jwt


# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)



def verify_access_token(token: str):
    """
    验证 JWT Token 并返回解码后的数据
    """
    try:
        # 解码 Token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # 返回解码后的数据，通常包含用户信息
    except JWTError as e:
        print(f"Token verification failed: {e}")
        return None
