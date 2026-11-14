import requests

from common.allure_attach import attach_request, attach_response
from common.logger import log
from config import settings


class BaseApi:
    def __init__(self):
        # 使用 session 保持会话，自动维持 cookie、复用长连接
        self.session = requests.Session()

    def send_request(self, path, method, json_data=None, params=None, headers=None):
        """统一接口请求入口

        :param path: 接口路径，如 /user/login
        :param method: GET / POST / PUT / DELETE
        :param json_data: POST 等请求的 json 入参
        :param params: GET 的 url 参数
        :param headers: 额外请求头
        """
        url = f"{settings.BASE_URL}{path}"
        headers_all = dict(settings.GLOBAL_HEADERS)

        # 从 settings 实时读取 token（不能用 import 的值拷贝，否则永远是空串）
        token = settings.get_token()
        if token:
            headers_all["Authorization"] = f"Bearer {token}"
        if headers:
            headers_all.update(headers)

        log.info(f"【{method.upper()}】{url} | params={params} | json={json_data}")
        attach_request(url, method, headers_all, json_data)

        timeout = settings.TIMEOUT
        try:
            method_upper = method.upper()
            if method_upper == "GET":
                resp = self.session.get(url, headers=headers_all, params=params, timeout=timeout)
            elif method_upper == "POST":
                resp = self.session.post(url, headers=headers_all, json=json_data, timeout=timeout)
            elif method_upper == "PUT":
                resp = self.session.put(url, headers=headers_all, json=json_data, timeout=timeout)
            elif method_upper == "DELETE":
                resp = self.session.delete(url, headers=headers_all, json=json_data, timeout=timeout)
            else:
                raise ValueError(f"框架不支持的请求方式：{method}")

            log.info(f"响应状态码：{resp.status_code} | 内容：{resp.text[:300]}")
            attach_response(resp)
            return resp
        except Exception as e:
            log.error(f"接口请求异常：{e}")
            raise
