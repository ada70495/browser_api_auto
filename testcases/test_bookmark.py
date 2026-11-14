import os

import allure
import pytest

from common.json_util import get_value
from common.yaml_handler import YamlHandler
from page.bookmark_page import BookmarkPage
from utils.assert_util import assert_msg_contain, assert_status_code
from utils.file_path import DATA_PATH

bookmark_data = YamlHandler(os.path.join(DATA_PATH, "bookmark_case.yaml")).read_yaml()[
    "add_bookmark_cases"
]


@allure.feature("浏览器-收藏夹模块")
class TestBookmarkApi:

    @allure.story("新增收藏接口")
    @pytest.mark.parametrize("case", bookmark_data, ids=lambda c: c["case_id"])
    def test_add_bookmark(self, case):
        resp = BookmarkPage().add_bookmark(title=case["title_name"], url=case["url"])
        res_json = resp.json()

        assert_status_code(resp)
        assert_msg_contain(res_json, case["expect_msg"])
        if case["expect_msg"] == "收藏添加成功":
            assert get_value(res_json, "data.bookmark_id") is not None, "新增收藏应返回 bookmark_id"
            assert get_value(res_json, "data.url") == case["url"], "返回链接应与入参一致"

    @allure.story("获取收藏列表接口")
    def test_get_bookmark_list(self):
        resp = BookmarkPage().get_bookmark_list()
        res_json = resp.json()

        assert_status_code(resp)
        assert_msg_contain(res_json, "查询成功")
        assert get_value(res_json, "data.total") >= 1, "至少应有一条收藏记录"
        assert isinstance(get_value(res_json, "data.list"), list), "list 字段应为数组"

    @allure.story("删除收藏接口")
    def test_delete_bookmark(self):
        bookmark = BookmarkPage()

        created = bookmark.add_bookmark("待删除", "https://www.example.com").json()
        bookmark_id = get_value(created, "data.bookmark_id")
        assert bookmark_id is not None, "前置新增收藏失败"

        resp = bookmark.delete_bookmark(bookmark_id)
        res_json = resp.json()
        assert_status_code(resp)
        assert_msg_contain(res_json, "收藏删除成功")

        # 再删一次，验证幂等：应提示收藏不存在
        again = bookmark.delete_bookmark(bookmark_id).json()
        assert_msg_contain(again, "收藏不存在")
