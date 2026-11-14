"""全局配置：环境、地址、超时、公共请求头、登录凭证

关键修复：token 不再用 `from config.settings import TOKEN` 这种值拷贝方式传递。
那样赋值 settings.TOKEN 之后，BaseApi 里拿到的仍是导入时的空字符串，鉴权永远不生效。
现在统一用 set_token / get_token 读写模块内变量，任何模块调用 get_token 都能拿到最新值。
"""
import os

from common.yaml_handler import YamlHandler
from utils.file_path import CONFIG_PATH

# 本地 .env 存在时加载（.env 不入库，用于放真实账号），没装 python-dotenv 也能跑
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

ENV_FILE = os.path.join(CONFIG_PATH, "env.yaml")
env_config = YamlHandler(ENV_FILE).read_yaml()

# 当前生效环境：环境变量 ENV 优先，其次 env.yaml 的 env 字段
CURRENT_ENV = os.getenv("ENV") or env_config.get("env", "local")
if CURRENT_ENV not in env_config:
    raise ValueError(f"环境 {CURRENT_ENV} 未在 config/env.yaml 中定义")
_env = env_config[CURRENT_ENV]

# 接口根地址：CI 可通过 BASE_URL 注入
BASE_URL = (os.getenv("BASE_URL") or _env["base_url"]).rstrip("/")
TIMEOUT = _env.get("timeout", 10)
GLOBAL_HEADERS = env_config.get("global_headers", {})

_account = env_config.get("account", {})
TEST_USER = os.getenv("TEST_USER") or _account.get("username")
TEST_PWD = os.getenv("TEST_PWD") or _account.get("password")
SIGN_KEY = os.getenv("SIGN_KEY") or _account.get("sign_key", "")

# 全局 token：由 conftest 登录后写入，BaseApi 每次请求前读取
_TOKEN = ""


def set_token(token: str):
    global _TOKEN
    _TOKEN = token or ""


def get_token() -> str:
    return _TOKEN
