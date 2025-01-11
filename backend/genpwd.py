from passlib.context import CryptContext

# 初始化密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 生成哈希密码
plain_password = "123456"  # 替换为您的密码
hashed_password = pwd_context.hash(plain_password)

print(f"Hashed password: {hashed_password}")
