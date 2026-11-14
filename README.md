# browser_api_test

浏览器后台接口的自动化测试工程，按 POM（Page Object Model）分层，负责接口请求与断言，
覆盖登录、收藏夹、浏览历史、缓存与无痕模式、DJ 音乐播放器五块业务。
技术栈：Python 3.13 + requests + pytest + PyYAML + Allure + loguru，被测服务用 Flask 起在本地。

被测服务是仓库里的一个 Flask 应用（`mock_server/app.py`），13 个业务接口，
路径统一在 `/api/v1` 前缀下。当前用例 27 条，框架代码覆盖率 84%。

## 环境要求

| 项 | 说明 |
| --- | --- |
| Python | 3.10 及以上（验证用的是 3.13） |
| 被测服务 | 仓库内 `mock_server/app.py`，默认监听 9200 端口 |
| Allure 命令行 | 可选，仅生成 HTML 报告时需要 |
| 本地 `.env` | 可选，用于放真实账号；不提供时用 `env.yaml` 里的 Mock 账号 |

## 依赖与用途

| 包 | 用途 | 备注 |
| --- | --- | --- |
| `requests` | HTTP 请求 | 统一走 `common/base_api.py` 的 Session |
| `PyYAML` | 环境配置与用例数据 | `common/yaml_handler.py` 封装了读写和异常日志 |
| `pytest` | 用例执行与参数化 | `pytest.ini` 固定扫描路径和附加参数 |
| `allure-pytest` | 报告 | 每个请求/响应自动作为附件挂到报告上 |
| `loguru` | 日志 | 500MB 切割，保留 10 天，`enqueue=True` 多线程安全 |
| `python-dotenv` | 读 `.env` | 未安装时 `settings.py` 会跳过，不影响运行 |
| `pytest-cov` | 覆盖率 | `pytest.ini` 已启用 `--cov` |
| `pytest-rerunfailures` | 失败重跑 | 最多 1 次，间隔 1 秒 |
| `flask` | 起被测服务 | 仅 `mock_server` 使用 |

安装：

```powershell
pip install -r requirements.txt
```

## 目录与职责

| 路径 | 职责 |
| --- | --- |
| `utils/file_path.py` | 全部路径常量（config / data / logs / reports），启动时自动建目录 |
| `utils/assert_util.py` | 通用断言：状态码、字段存在、字段取值、提示文案包含 |
| `config/settings.py` | 读 `env.yaml` 和 `.env`，暴露 `BASE_URL`、`TIMEOUT`、`GLOBAL_HEADERS`、账号，以及 `set_token()` / `get_token()` |
| `config/env.yaml` | local / ci 两套地址、公共请求头、Mock 账号 |
| `common/base_api.py` | 请求入口：拼地址、注入 token、按方法分发、写 Allure 附件、异常日志 |
| `common/yaml_handler.py` | YAML 读写，读失败时带文件路径打日志再抛 |
| `common/logger.py` | loguru 配置，全局 `log` 对象 |
| `common/allure_attach.py` | 把请求头/请求体/响应体格式化成文本附件 |
| `common/json_util.py` | `to_json` / `get_value(data, "data.list.0.title")` / `extract_list` |
| `page/base_page.py` | POM 父类，所有业务页面共用同一个 `BaseApi` 实例 |
| `page/login_page.py` | 登录接口 |
| `page/bookmark_page.py` | 收藏：新增、列表、删除 |
| `page/history_page.py` | 历史：新增、清空 |
| `page/cache_page.py` | 缓存清理、无痕模式开关 |
| `page/dj_page.py` | DJ：歌单、播放、音量、均衡器、播放模式 |
| `data/*.yaml` | 各模块用例参数与预期，按模块拆分 |
| `testcases/conftest.py` | `login_data`（登录用例数据）、`mock_ready`（复位服务）、`get_login_token`（session 级登录） |
| `testcases/test_*.py` | 参数化执行 + 业务断言，不出现具体 URL 和请求细节 |
| `mock_server/app.py` | 被测服务：13 个业务接口 + `/health` + `/__admin/reset` |
| `run_all.py` | 起服务、跑用例、生成报告的入口 |
| `.coveragerc` | 覆盖率统计范围：只统计 `common` / `page` / `utils` |

分层的实际约束：`page` 层不写断言，`testcases` 层不写 URL 和 headers，`common` 层不碰业务字段名。

## 跑起来

```powershell
# 方式一：一条命令（自动起服务、跑完自动关）
python run_all.py

# 方式二：分开执行
python mock_server/app.py    # 终端 1
pytest                        # 终端 2

# 只跑 DJ 模块
pytest testcases/test_dj.py
```

正常输出结尾：

```
TOTAL                       179     28    84%
============================= 27 passed in 0.94s ==============================
```

服务单独起时先验证一下：

```powershell
curl http://127.0.0.1:9200/health
# {"service":"mock-browser-api","status":"ok"}
```

## 一次请求的调用链

以「新增收藏」为例：

```
testcases/test_bookmark.py::test_add_bookmark
  → page/bookmark_page.py::BookmarkPage.add_bookmark(title, url)     拼 payload，调 api
  → common/base_api.py::BaseApi.send_request()                      拼 BASE_URL + path，注入 token
  → common/allure_attach.py::attach_request()                       请求详情写进 Allure
  → mock_server/app.py::bookmark_add()                              校验 url / title，写内存状态
  → utils/assert_util.py                                            断言状态码与提示文案
```

## 配置

`config/env.yaml`：

```yaml
env: local

local:
  base_url: "http://127.0.0.1:9200/api/v1"
  timeout: 10

ci:
  base_url: "http://host.docker.internal:9200/api/v1"
  timeout: 15

global_headers:
  Content-Type: "application/json"
  platform: "mobile"
  app_version: "1.0.0"

account:
  username: "testuser"
  password: "123456"
  sign_key: "mock-sign-key-2026"
```

| 字段 | 含义 | 说明 |
| --- | --- | --- |
| `env` | 默认环境名 | 可被 `ENV` 覆盖 |
| `base_url` | 接口根地址，**带 `/api/v1`** | 可被 `BASE_URL` 覆盖；路径拼接是 `BASE_URL + path`，所以这里必须带前缀 |
| `timeout` | 请求超时（秒） | 传进 `requests` |
| `global_headers` | 所有请求共用的头 | `send_request` 里会 `copy` 后再合并自定义头，不改原字典 |
| `account` | 默认账号 | 本地 `.env` 和 `TEST_USER` / `TEST_PWD` 优先 |

生效顺序：环境变量 → `.env` → `env.yaml`。三者都提供时以环境变量为准。

`.env` 是可选的：

```ini
TEST_USER=your_name
TEST_PWD=your_password
```

没装 `python-dotenv` 或没有 `.env` 时，`settings.py` 会退到 `env.yaml` 里的 Mock 账号，框架照常运行。
`.env` 在 `.gitignore` 里，不会进仓库。

## 覆盖的接口

| 模块 | 方法 | 路径 | 主要校验 |
| --- | --- | --- | --- |
| 登录 | POST | `/user/login` | 用户名为空 → HTTP 400；密码错 → `code` 401 |
| 收藏 | POST | `/bookmark/add` | url 空、缺协议头、标题空 |
| 收藏 | GET | `/bookmark/list` | 返回 `total` 与 `list` |
| 收藏 | DELETE | `/bookmark/delete` | 不存在 → 404「收藏不存在」 |
| 历史 | POST | `/history/add` | 标题、url、访问时间三项必填 |
| 历史 | POST | `/history/clear` | 返回清空条数 |
| 缓存 | POST | `/cache/clear` | 类型仅 `all` / `image` / `cookie` |
| 无痕 | POST | `/incognito/switch` | `open` 必须布尔 |
| DJ | GET | `/dj/playlist` | 返回 `total` 与 `list` |
| DJ | POST | `/dj/play` | 歌曲不存在 → 404 |
| DJ | POST | `/dj/volume` | 0–100 整数 |
| DJ | POST | `/dj/eq` | `normal` / `rock` / `jazz` / `vocal` |
| DJ | POST | `/dj/play_mode` | `sequence` / `loop` / `single` / `random` |

HTTP 状态码与业务码混用：登录用户名为空返回 HTTP 400，其余业务错误返回 HTTP 200 并在响应体 `code` 里区分。
用例参数里的 `expect_code` 指的是 HTTP 状态码，`expect_msg` 校验提示文案。

## 新增一条用例

### 只加场景

在对应 `data/*.yaml` 里追加一项，代码不动：

```yaml
# data/cache_case.yaml
clear_cache_cases:
  - case_id: cache_003
    title: 仅清理 Cookie
    cache_type: "cookie"
    expect_msg: "缓存清理完成"
```

```powershell
pytest testcases/test_cache.py -k cache_003
```

`case_id` 同时用作 pytest 的参数化 id，尽量保持 ASCII 且唯一，这样控制台和报告里的用例名可读。

### 加一个接口

三步：

1. `page/` 下对应模块加方法，只拼参数：

```python
def rename_bookmark(self, bookmark_id, title):
    return self.api.send_request(
        path="/bookmark/rename",
        method="PUT",
        json_data={"bookmark_id": bookmark_id, "title": title},
    )
```

2. `data/` 加用例数据（`case_id` / 入参 / `expect_msg`）。
3. `testcases/` 加参数化用例，用 `assert_status_code` + `assert_msg_contain`，成功场景再加字段断言。

新增 HTTP 方法时才需要动 `common/base_api.py`，目前支持 GET / POST / PUT / DELETE。

### 断言怎么写

基础三件套在 `utils/assert_util.py`：

```python
assert_status_code(resp)                       # 默认 200
assert_msg_contain(res_json, "收藏添加成功")     # 提示文案包含
assert_json_contain(res_json["data"], "token")  # 字段存在
```

要看深层字段，用 `json_util.get_value`：

```python
assert get_value(res_json, "data.total") >= 1
assert get_value(res_json, "data.list.0.url") == "https://www.baidu.com"
```

`get_value` 取不到时返回 `default`（默认为 `None`），不会抛 KeyError，但要记得在断言里处理 `None` 的情况。

## 关于 token

登录成功后，`conftest.py` 调 `settings.set_token()` 把 token 写进模块变量，`BaseApi` 每次请求前
调 `settings.get_token()` 读出来加 `Authorization: Bearer`。

这里原本有个问题：旧写法是 `from config.settings import TOKEN`，然后在 conftest 里
`settings.TOKEN = token`。这样做 token 永远加不上，原因是 `from ... import NAME` 在导入时
把值绑定到当前模块的命名空间，之后再改 `settings.TOKEN` 改的是 `settings` 模块的属性，
`BaseApi` 里的 `TOKEN` 仍指向导入时的空字符串。改成函数读写后正常。

同类写法（模块级可变配置）都建议用函数或容器对象承载，不要靠模块属性重新赋值。

## 覆盖率

`pytest.ini` 已启用 `--cov=common --cov=page --cov=utils`，`.coveragerc` 限定统计范围、排除用例和 Mock 服务。
最近一次执行结果：

```
Name                      Stmts   Miss  Cover   Missing
-------------------------------------------------------
common\allure_attach.py      13      2    85%   23-24
common\base_api.py           35      6    83%   30, 43, 47, 52-54
common\json_util.py          23     12    48%   11-14, 25-28, 31, 34, 40-41
common\logger.py              6      0   100%
common\yaml_handler.py       16      5    69%   15-17, 21-22
page\base_page.py             4      0   100%
page\bookmark_page.py        16      0   100%
page\cache_page.py           12      0   100%
page\dj_page.py              12      0   100%
page\history_page.py         11      0   100%
page\login_page.py            7      0   100%
utils\assert_util.py         11      2    82%   14-15
utils\file_path.py           13      1    92%   17
-------------------------------------------------------
TOTAL                       179     28    84%
```

两个入口跑出来的覆盖率不一样，这点在排查数据时要留意：`run_all.py` 用 `subprocess` 启动 pytest，
coverage 在子进程里才生效，`logger.py`、`file_path.py` 这种在 import 阶段就执行完的模块统计不到，
TOTAL 会显示 74%（这两个文件显示 0%）。需要准确的覆盖率数字，在项目根目录直接执行 `pytest`。

这个数字衡量的是「框架自身的代码有多少分支被用例走到」，不等于业务接口覆盖率。
`json_util.py` 偏低是因为部分工具函数没有用例调用，属于预期。

只看某个模块：

```powershell
pytest --cov=page --cov-report=term-missing
```

生成 HTML：

```powershell
pytest --cov-report=html:reports/coverage_html
```

## 报告与日志

```powershell
pytest
allure generate reports/allure_raw -o reports/allure_html --clean
allure open reports/allure_html
```

- Allure 里每个请求都有「接口请求详情」「接口响应详情」两个文本附件，失败时不用翻代码就能看到实际返回
- 日志：`logs/browser_api_test.log`，记录每条请求的 URL、参数、状态码和响应片段
- `reports/` 和 `logs/` 都在 `.gitignore` 里

## CI

`docker-compose.yml`：服务容器跑 `mock_server/app.py`，用例容器的 `BASE_URL` 指向服务名
`http://browser-api:9200/api/v1`；用例容器加 `--no-cov`，避免容器内缺少覆盖率依赖时影响执行。

`Jenkinsfile`：拉代码 → 用 `sed` 去掉 `/api/v1` 得到根地址轮询 `/health` → 装依赖 →
执行 pytest 并额外传 `--junitxml=reports/junit-result.xml`、`--cov-report=xml:reports/coverage.xml`
（这两项没有写进 `pytest.ini`，只在流水线里需要）→ 发布报告。
宿主机起服务时用 `host.docker.internal:9200`。

## 排错对照

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 所有请求 401 或没有 `Authorization` 头 | token 没写进 `settings`，或用了旧的模块级导入写法 | 确认 conftest 调的是 `settings.set_token()`，`BaseApi` 里调 `get_token()` |
| `requests.exceptions.MissingSchema` / 404 全红 | `base_url` 少了 `/api/v1` | `BASE_URL` 是根地址，路径拼接直接相加，前缀必须写在配置里 |
| `RuntimeError: 被测服务未启动` | `mock_server` 没起 | `python mock_server/app.py`，或 `python run_all.py` |
| 登录用例报「密码错误」但密码是对的 | YAML 把 `123456` 解析成整数，服务端按字符串比较 | 密码加引号写成 `"123456"`；服务端也做了 `str()` 兼容 |
| 删除类用例第二次跑失败 | 数据已被上一次删掉 | 用例内部自建数据（当前已这样处理），或调 `/__admin/reset` |
| 提示文案断言失败 | 同一个字段被别的操作改写过 | 用 `assert_msg_contain` 判断包含，不要全等 |
| `--cov` 报 `unrecognized arguments` | 没装 `pytest-cov` | `pip install pytest-cov`，或临时加 `--no-cov` |

## 已知限制

- 服务端状态在内存里，重启清空；不支持并发执行。
- 登录接口只校验固定账号，没有用户表和权限模型。
- 覆盖率只覆盖框架代码，业务接口的参数组合没有逐条穷举。
- 断言基于状态码和文案，没有做响应结构（jsonschema）校验，字段类型变了不一定能发现。
