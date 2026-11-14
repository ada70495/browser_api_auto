from page.base_page import BasePage


class DjPage(BasePage):
    """DJ 音乐播放器业务接口"""

    def get_playlist(self):
        """查询歌单"""
        return self.api.send_request(path="/dj/playlist", method="GET")

    def play(self, song_id):
        """播放指定歌曲"""
        return self.api.send_request(path="/dj/play", method="POST", json_data={"song_id": song_id})

    def set_volume(self, volume):
        """设置音量（0-100）"""
        return self.api.send_request(path="/dj/volume", method="POST", json_data={"volume": volume})

    def set_eq(self, mode):
        """设置均衡器：normal/rock/jazz/vocal"""
        return self.api.send_request(path="/dj/eq", method="POST", json_data={"mode": mode})

    def set_play_mode(self, mode):
        """设置播放模式：sequence/loop/single/random"""
        return self.api.send_request(
            path="/dj/play_mode", method="POST", json_data={"mode": mode}
        )
