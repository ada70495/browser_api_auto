import os

import allure
import pytest

from common.json_util import get_value
from common.yaml_handler import YamlHandler
from page.dj_page import DjPage
from utils.assert_util import assert_msg_contain, assert_status_code
from utils.file_path import DATA_PATH

dj_data = YamlHandler(os.path.join(DATA_PATH, "dj_case.yaml")).read_yaml()


@allure.feature("DJ音乐播放器")
class TestDjApi:

    @allure.story("歌单查询接口")
    @pytest.mark.parametrize("case", dj_data["dj_playlist_cases"], ids=lambda c: c["case_id"])
    def test_playlist(self, case):
        resp = DjPage().get_playlist()
        res_json = resp.json()

        assert_status_code(resp)
        assert_msg_contain(res_json, case["expect_msg"])
        assert get_value(res_json, "data.total") == case["expect_total"], "歌曲总数不符"
        assert len(get_value(res_json, "data.list", [])) == case["expect_total"], "列表长度不符"

    @allure.story("播放控制接口")
    @pytest.mark.parametrize("case", dj_data["dj_play_cases"], ids=lambda c: c["case_id"])
    def test_play(self, case):
        resp = DjPage().play(case["song_id"])
        res_json = resp.json()

        assert_status_code(resp)
        assert_msg_contain(res_json, case["expect_msg"])
        if case["expect_msg"] == "开始播放":
            assert get_value(res_json, "data.playing") is True, "播放状态应为 True"
            assert get_value(res_json, "data.song_id") == case["song_id"], "返回歌曲ID不符"

    @allure.story("音量调节接口")
    @pytest.mark.parametrize("case", dj_data["dj_volume_cases"], ids=lambda c: c["case_id"])
    def test_volume(self, case):
        resp = DjPage().set_volume(case["volume"])
        res_json = resp.json()

        assert_status_code(resp)
        assert_msg_contain(res_json, case["expect_msg"])
        if case["expect_msg"] == "音量设置成功":
            assert get_value(res_json, "data.volume") == case["volume"], "音量回显不符"

    @allure.story("均衡器接口")
    @pytest.mark.parametrize("case", dj_data["dj_eq_cases"], ids=lambda c: c["case_id"])
    def test_eq(self, case):
        resp = DjPage().set_eq(case["mode"])
        res_json = resp.json()

        assert_status_code(resp)
        assert_msg_contain(res_json, case["expect_msg"])
        if case["expect_msg"] == "均衡器设置成功":
            assert get_value(res_json, "data.mode") == case["mode"], "均衡器回显不符"

    @allure.story("播放模式接口")
    @pytest.mark.parametrize("case", dj_data["dj_play_mode_cases"], ids=lambda c: c["case_id"])
    def test_play_mode(self, case):
        resp = DjPage().set_play_mode(case["mode"])
        res_json = resp.json()

        assert_status_code(resp)
        assert_msg_contain(res_json, case["expect_msg"])
        if case["expect_msg"] == "播放模式设置成功":
            assert get_value(res_json, "data.mode") == case["mode"], "播放模式回显不符"
