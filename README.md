# browser_api_test

标准 **POM 分层**的接口自动化测试框架，面向移动端浏览器后台接口，覆盖
**登录 / 收藏夹 / 浏览历史 / 缓存与无痕模式 / DJ 音乐播放器** 五大模块。

仓库内自带本地被测服务（`mock_server/`），克隆后无需任何内网环境即可跑通全部 27 条用例，
框架自身代码覆盖率 **84%**。

---

## 一、技术栈

| 类别 | 选型 |
| --- | --- |
| 语言 | Python 3.10+ |
| 请求 | requests（Session 会话保持） |
| 框架 | pytest + YAML 数据驱动 + 参数化 |
| 报告 | Allure（自动挂载请求/响应详情）+ JUnit XML |
| 日志 | loguru（按大小切割、按天保留） |
| 覆盖率 | pytest-cov（`--cov` 已配置，报告 84%） |
| 稳定性 | pytest-rerunfailures（失败重跑） |
| 被测服务 | Flask（本地 Mock，17 个接口） |

## 二、分层架构

```
utils/        工具层：全局路径管理、通用断言封装
config/       配置层：多环境地址、超时、公共请求头、token 读写
common/       基础层：请求封装、日志、YAML 读写、Allure 附件、JSON 工具
page/         POM 业务层：按模块封装接口调用，不做断言
data/         数据层：YAML 存放全部用例参数，改参数不改代码
testcases/    用例层：参数化执行 + 业务断言
mock_server/  本地被测服务（Flask），替代脱敏域名
logs/ reports/ 运行产物（日志、Allure 原始数据与 HTML）
```

目录说明：

| 路径 | 作用 |
| --- | --- |
| `common/base_api.py` | 统一请求入口：拼地址、带 token、Allure 附件、异常日志 |
| `common/json_util.py` | 响应解析与路径取值（`get_value(res, "data.list")`） |
| `page/base_page.py` | POM 父类，业务页面复用同一个请求对象 |
| `page/dj_page.py` | DJ 播放器接口（歌单/播放/音量/均衡器/播放模式） |
| `data/dj_case.yaml` | DJ 模块 12 条参数化用例数据 |

## 三、覆盖模块

| 模块 | 接口 | 用例覆盖 |
| --- | --- | --- |
| 登录 | `POST /user/login` | 正常登录、密码错误、空用户名 |
| 收藏夹 | `POST /bookmark/add`、`GET /bookmark/list`、`DELETE /bookmark/delete` | 新增（正常/空链接）、列表查询、删除 + 重复删除幂等 |
| 浏览历史 | `POST /history/add`、`POST /history/clear` | 正常新增、空链接、空访问时间、一键清空 |
| 缓存 & 无痕 | `POST /cache/clear`、`POST /incognito/switch` | 全部/图片缓存清理、非法类型、无痕开→关 |
| DJ 播放器 | `/dj/playlist`、`/dj/play`、`/dj/volume`、`/dj/eq`、`/dj/play_mode` | 歌单查询、播放存在/不存在歌曲、音量边界（0/60/101/-1）、均衡器、播放模式 |

## 四、本地运行

```powershell
# 1. 安装依赖
pip install -r requirements.txt

# 2. 一键执行（自动拉起被测服务 → 跑用例 → 生成 Allure 报告）
python run_all.py

# 或分开执行
python mock_server/app.py        # 另开终端，默认 9200 端口
pytest
```

只跑 DJ 模块：

```powershell
pytest testcases/test_dj.py
```

## 五、环境与配置

`config/env.yaml`：

```yaml
env: local
local:
  base_url: "http://127.0.0.1:9200/api/v1"
  timeout: 10
ci:
  base_url: "http://host.docker.internal:9200/api/v1"
  timeout: 15
account:
  username: "testuser"
  password: "123456"
```

优先级：**环境变量 `ENV` / `BASE_URL` / `TEST_USER` / `TEST_PWD` > 本地 `.env` > `env.yaml`**。
真实账号写本地 `.env`（已在 `.gitignore` 排除），仓库里只有 Mock 服务的固定账号。

## 六、关键修复说明

1. **token 不生效**（严重）：原代码 `from config.settings import TOKEN` 是值拷贝，
   conftest 里 `settings.TOKEN = token` 之后，`BaseApi` 拿到的仍是导入时的空字符串，鉴权永远为空。
   现已改为 `settings.set_token() / get_token()` 读写模块变量，BaseApi 每次请求前实时读取。
2. **`data/history_case.yaml` 重复 `title` 键**：同一节点下两个 `title`，YAML 解析时后者覆盖前者，
   用例标题变成歌曲名、记录的标题也取错。现已统一为 `title`（用例名）+ `title_name`（记录标题）。
3. **`common/json_util.py` 是 0 字节文件**：框架引用了却没有实现。现已补齐 `to_json` / `get_value` / `extract_list`。
4. **脱敏域名无法访问**：新增 `mock_server/app.py`，本地即可真实回归；`config/env.yaml` 改为 local/ci 双环境。
5. **`.env` 缺失导致账号为 None**：`settings` 里给了 Mock 固定账号兜底，`.env` 变为可选增强而非必需。

## 七、CI 说明

- `docker-compose.yml`：一键拉起被测服务 + 执行用例容器（`docker compose run --rm api-test`）
- `Jenkinsfile`：拉代码 → 等待服务就绪 → 装依赖 → 跑 pytest → 发布 JUnit + Allure

容器内访问宿主机服务统一用 `host.docker.internal`，`BASE_URL` 由流水线环境变量注入。

## 八、安全说明

仓库内地址、账号、密钥均为本地 Mock 服务固定值，不含公司真实环境信息；
真实配置通过 `.env` 或环境变量注入，不入库。
