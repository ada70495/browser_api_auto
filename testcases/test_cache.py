import os

import allure
import pytest

from common.json_util import get_value
from common.yaml_handler import YamlHandler
from page.cache_page import CachePage
from utils.assert_util import assert_msg_contain, assert_status_code
from utils.file_path import DATA_PATH

cache_data = YamlHandler(os.path.join(DATA_PATH, "cache_case.yaml")).read_yaml()[
    "clear_cache_cases"
]


@allure.feature("浏览器-缓存与无痕模式")
class TestCacheApi:

    @allure.story("清理各类缓存接口")
    @pytest.mark.parametrize("case", cache_data, ids=lambda c: c["case_id"])
    def test_clear_cache(self, case):
        resp = CachePage().clear_cache(cache_type=case["cache_type"])
        res_json = resp.json()

        assert_status_code(resp)
        assert_msg_contain(res_json, case["expect_msg"])
        assert get_value(res_json, "data.cache_type") == case["cache_type"], "清理类型回显不符"

    @allure.story("非法缓存类型校验")
    def test_clear_cache_invalid_type(self):
        resp = CachePage().clear_cache(cache_type="video")
        res_json = resp.json()

        assert_status_code(resp)
        assert_msg_contain(res_json, "不支持的缓存类型")

    @allure.story("切换无痕模式开关")
    def test_switch_incognito(self):
        cache = CachePage()

        resp = cache.set_incognito_mode(status=True)
        res_json = resp.json()
        assert_status_code(resp)
        assert_msg_contain(res_json, "无痕模式已开启")
        assert get_value(res_json, "data.open") is True, "开关状态应为 True"

        resp_off = cache.set_incognito_mode(status=False)
        assert_msg_contain(resp_off.json(), "无痕模式已关闭")
        assert get_value(resp_off.json(), "data.open") is False, "开关状态应为 False"
