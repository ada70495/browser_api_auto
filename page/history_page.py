from page.base_page import BasePage


class HistoryPage(BasePage):
    def add_history(self, title, url, visit_time):
        """新增一条浏览历史记录"""
        body = {"title": title, "url": url, "visit_time": visit_time}
        return self.api.send_request(path="/history/add", method="POST", json_data=body)

    def get_history_list(self):
        """查询全部浏览历史记录"""
        return self.api.send_request(path="/history/list", method="GET")

    def clear_all_history(self):
        """一键清空全部浏览历史"""
        return self.api.send_request(path="/history/clear", method="POST")
