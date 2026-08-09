import os
from urllib.parse import urlparse

url = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://fitness_user:fitness_password@localhost:5432/fitness_test_db")
p = urlparse(url)
print("USER:", p.username)
print("PASSWORD:", p.password)
