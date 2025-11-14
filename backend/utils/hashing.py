from passlib.context import CryptContext

# Use bcrypt_sha256 scheme instead of bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    print("------------------------------------------------------------------------------------")
    
    return pwd_context.verify(plain, hashed)