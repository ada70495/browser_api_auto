import os

import allure
import pytest

from common.json_util import get_value
from common.yaml_handler import YamlHandler
from page.history_page import HistoryPage
from utils.assert_util import assert_msg_contain, assert_status_code
from utils.file_path import DATA_PATH

history_yaml_path = os.path.join(DATA_PATH, "history_case.yaml")
history_data = YamlHandler(history_yaml_path).read_yaml()["add_history_cases"]


@allure.feature("浏览器-浏览历史模块")
class TestHistoryApi:
    @allure.story("新增浏览记录接口")
    @pytest.mark.parametrize("case", history_data, ids=lambda c: c["case_id"])
    def test_add_history(self, case):
        history = HistoryPage()
        resp = history.add_history(
            title=case["title_name"], url=case["url"], visit_time=case["visit_time"]
        )
        res_json = resp.json()
        assert_status_code(resp)
        assert_msg_contain(res_json, case["expect_msg"])

    @allure.story("查询浏览历史列表")
    def test_get_history_list(self):
        history = HistoryPage()
        history.add_history("列表查询前置", "https://www.example.com", "2026-07-22 12:00:00")

        resp = history.get_history_list()
        res_json = resp.json()

        assert_status_code(resp)
        assert_msg_contain(res_json, "查询成功")
        assert get_value(res_json, "data.total") >= 1, "至少应有一条历史记录"
        assert get_value(res_json, "data.total") == len(get_value(res_json, "data.list")), (
            "total 应与列表长度一致"
        )

    @allure.story("一键清空全部历史记录")
    def test_clear_history(self):
        history = HistoryPage()
        history.add_history("待清空记录", "https://www.example.com", "2026-07-22 12:00:00")

        resp = history.clear_all_history()
        res_json = resp.json()

        assert_status_code(resp)
        assert_msg_contain(res_json, "历史记录已清空")
        assert get_value(res_json, "data.cleared") >= 1, "清空条数应大于 0"

        # 清空后再次查询，列表应为空
        after = history.get_history_list().json()
        assert get_value(after, "data.total") == 0, "清空后历史记录总数应为 0"
