# Path: fastapi/scripts/hash_password.py

from auth.utils import hash_password # path: fastapi/auth/utils.py

def generate_hashed_password(plain_password: str):
    hashed_password = hash_password(plain_password)
    print(f"Hashed Password: {hashed_password}")

if __name__ == "__main__":
    password = input("Enter the password you want to hash: ")
    generate_hashed_password(password)
