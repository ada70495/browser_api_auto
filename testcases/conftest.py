"""全局 fixture：被测服务复位 / 全局登录 / 用例数据"""
import os

import pytest
import requests

from common.yaml_handler import YamlHandler
from config import settings
from page.login_page import LoginPage
from utils.file_path import DATA_PATH


def _service_root() -> str:
    """BASE_URL 形如 http://127.0.0.1:9200/api/v1，运维接口在根路径"""
    return settings.BASE_URL.split("/api/v1")[0]


@pytest.fixture(scope="session")
def login_data():
    """登录用例数据，供 test_login 参数化使用"""
    path = os.path.join(DATA_PATH, "login_case.yaml")
    return YamlHandler(path).read_yaml()["login_cases"]


@pytest.fixture(scope="session", autouse=True)
def mock_ready():
    """执行前复位被测服务数据，保证每次回归从同一初始状态开始"""
    root = _service_root()
    try:
        resp = requests.post(f"{root}/__admin/reset", timeout=5)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(
            f"被测服务未启动：{root}\n请先执行：python mock_server/app.py\n原始错误：{e}"
        )
    yield


@pytest.fixture(scope="session", autouse=True)
def get_login_token():
    """session 级全局登录，登录一次后续接口自动携带 token"""
    login_api = LoginPage()
    resp = login_api.login(settings.TEST_USER, settings.TEST_PWD)
    res_json = resp.json()
    assert res_json.get("code") == 200, f"登录失败，无法继续执行：{res_json}"
    settings.set_token(res_json["data"]["token"])
    yield
    settings.set_token("")
