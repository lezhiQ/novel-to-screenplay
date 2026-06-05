import os
from dotenv import load_dotenv

load_dotenv()

# 小米 MiMo API 配置
MIMO_API_BASE = os.getenv("MIMO_API_BASE", "https://token-plan-cn.xiaomimimo.com/v1")
MIMO_API_KEY = os.getenv("MIMO_API_KEY", "")
MIMO_MODEL = os.getenv("MIMO_MODEL", "mimo-v2.5-pro")

# 服务配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
