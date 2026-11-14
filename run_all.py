"""一键执行：拉起本地被测服务 → 跑全部用例 → 生成 Allure 报告

用法：
    python run_all.py                         # 全部用例
    python run_all.py testcases/test_dj.py    # 只跑 DJ 模块
"""
import os
import shutil
import subprocess
import sys
import time

import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = os.getenv("PORT", "9200")
SERVICE_URL = f"http://127.0.0.1:{PORT}"

sys.path.insert(0, ROOT)

from common.logger import log
from utils.file_path import ALLURE_HTML_PATH, ALLURE_RAW_PATH


def start_service():
    """本地被测服务没起就拉起来"""
    try:
        requests.get(f"{SERVICE_URL}/health", timeout=1)
        log.info(f"被测服务已在运行：{SERVICE_URL}")
        return None
    except Exception:
        pass

    log.info(f"启动本地被测服务：{SERVICE_URL}")
    proc = subprocess.Popen(
        [sys.executable, os.path.join(ROOT, "mock_server", "app.py")],
        cwd=ROOT,
        env={**os.environ, "PORT": PORT},
    )
    for _ in range(30):
        try:
            requests.get(f"{SERVICE_URL}/health", timeout=1)
            log.info("被测服务启动成功")
            return proc
        except Exception:
            time.sleep(1)
    proc.terminate()
    raise RuntimeError("被测服务启动失败，请手动执行：python mock_server/app.py")


def gen_allure_report():
    allure = shutil.which("allure")
    if not allure:
        log.warning("未检测到 allure 命令，跳过 HTML 报告生成（原始数据在 reports/allure_raw）")
        return None
    rc = subprocess.call(
        [allure, "generate", ALLURE_RAW_PATH, "-o", ALLURE_HTML_PATH, "--clean"], cwd=ROOT
    )
    if rc == 0:
        log.info(f"Allure 报告已生成：{ALLURE_HTML_PATH}/index.html")
    else:
        log.error("Allure 报告生成失败，请检查 allure 安装")
    return rc


def run_auto_test():
    log.info("===== 浏览器接口自动化测试开始 =====")
    os.chdir(ROOT)
    service = start_service()
    try:
        rc = pytest_main(sys.argv[1:])
        gen_allure_report()
        log.info(f"===== 执行结束，pytest 退出码 = {rc} =====")
        sys.exit(rc)
    finally:
        if service:
            service.terminate()
            log.info("被测服务已关闭")


def pytest_main(args):
    import pytest

    return pytest.main(args)


if __name__ == "__main__":
    run_auto_test()
