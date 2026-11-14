from page.base_page import BasePage


class BookmarkPage(BasePage):
    def add_bookmark(self, title, url):
        """新增网页收藏"""
        body = {"title": title, "url": url}
        return self.api.send_request(path="/bookmark/add", method="POST", json_data=body)

    def get_bookmark_list(self, keyword=None):
        """查询收藏列表，keyword 非空时按标题或链接做模糊匹配"""
        params = {"keyword": keyword} if keyword else None
        return self.api.send_request(path="/bookmark/list", method="GET", params=params)

    def delete_bookmark(self, bookmark_id):
        """根据 id 删除单条收藏"""
        body = {"bookmark_id": bookmark_id}
        return self.api.send_request(path="/bookmark/delete", method="DELETE", json_data=body)
