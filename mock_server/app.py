"""本地被测服务：移动端浏览器接口

覆盖 登录 / 收藏夹 / 浏览历史 / 缓存与无痕 / DJ 音乐播放器，
替代原来指向脱敏域名的测试环境，让 POM 用例可以真实跑通。

启动：
    python mock_server/app.py            # 默认 9200 端口
    $env:PORT=9201; python mock_server/app.py

所有业务接口前缀：/api/v1（与 config/env.yaml 的 base_url 对应）
"""
import os

from flask import Flask, jsonify, request

app = Flask(__name__)
app.json.ensure_ascii = False

PREFIX = "/api/v1"
TOKEN = "mock-token-browser-2026"

CACHE_TYPES = {"all", "image", "cookie"}
EQ_MODES = {"normal", "rock", "jazz", "vocal"}
PLAY_MODES = {"sequence", "loop", "single", "random"}

SONGS = [
    {"song_id": 1, "name": "夜航", "artist": "Mock Band", "duration": 214},
    {"song_id": 2, "name": "霓虹", "artist": "Mock Band", "duration": 188},
    {"song_id": 3, "name": "晚风", "artist": "Mock Band", "duration": 240},
]


def init_state():
    return {
        "bookmarks": {},
        "bookmark_seq": 5000,
        "history": [],
        "cache": {},
        "incognito": False,
        "dj": {"volume": 50, "eq": "normal", "play_mode": "sequence", "playing": None},
    }


STATE = init_state()


def ok(data=None, msg="成功"):
    return jsonify({"code": 200, "msg": msg, "data": data})


def fail(code, msg, http_status=200):
    return jsonify({"code": code, "msg": msg, "data": None}), http_status


def body():
    return request.get_json(silent=True) or {}


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "mock-browser-api"})


@app.post("/__admin/reset")
def reset():
    global STATE
    STATE = init_state()
    return ok({"reset": True}, "数据已复位")


# ---------------- 登录 ----------------
@app.post(PREFIX + "/user/login")
def login():
    data = body()
    username = (data.get("username") or "").strip()
    password = str(data.get("password") or "")
    if not username:
        return fail(400, "用户名不能为空", http_status=400)
    if password != "123456":
        return fail(401, "密码错误")
    return ok({"token": TOKEN, "username": username}, "登录成功")


def _check_token():
    auth = request.headers.get("Authorization", "")
    return bool(auth) and TOKEN in auth


# ---------------- 收藏夹 ----------------
@app.post(PREFIX + "/bookmark/add")
def bookmark_add():
    data = body()
    title = (data.get("title") or "").strip()
    url = (data.get("url") or "").strip()
    if not url:
        return fail(400, "链接地址不能为空")
    if not url.startswith(("http://", "https://")):
        return fail(400, "链接格式不正确，必须以 http/https 开头")
    if not title:
        return fail(400, "标题不能为空")
    STATE["bookmark_seq"] += 1
    bid = STATE["bookmark_seq"]
    STATE["bookmarks"][bid] = {"bookmark_id": bid, "title": title, "url": url}
    return ok({"bookmark_id": bid, "title": title, "url": url}, "收藏添加成功")


@app.get(PREFIX + "/bookmark/list")
def bookmark_list():
    items = list(STATE["bookmarks"].values())
    return ok({"total": len(items), "list": items}, "查询成功")


@app.delete(PREFIX + "/bookmark/delete")
def bookmark_delete():
    data = body()
    bid = data.get("bookmark_id")
    if bid not in STATE["bookmarks"]:
        return fail(404, "收藏不存在")
    STATE["bookmarks"].pop(bid)
    return ok({"bookmark_id": bid}, "收藏删除成功")


# ---------------- 浏览历史 ----------------
@app.post(PREFIX + "/history/add")
def history_add():
    data = body()
    title = (data.get("title") or "").strip()
    url = (data.get("url") or "").strip()
    visit_time = data.get("visit_time")
    if not title:
        return fail(400, "历史标题不能为空")
    if not url:
        return fail(400, "链接地址不能为空")
    if not visit_time:
        return fail(400, "访问时间不能为空")
    STATE["history"].append({"title": title, "url": url, "visit_time": visit_time})
    return ok({"total": len(STATE["history"])}, "记录保存成功")


@app.post(PREFIX + "/history/clear")
def history_clear():
    cleared = len(STATE["history"])
    STATE["history"] = []
    return ok({"cleared": cleared}, f"历史记录已清空，共 {cleared} 条")


# ---------------- 缓存与无痕 ----------------
@app.post(PREFIX + "/cache/clear")
def cache_clear():
    data = body()
    cache_type = data.get("cache_type", "all")
    if cache_type not in CACHE_TYPES:
        return fail(400, "不支持的缓存类型，可选 all/image/cookie")
    STATE["cache"][cache_type] = True
    return ok({"cache_type": cache_type}, "缓存清理完成")


@app.post(PREFIX + "/incognito/switch")
def incognito_switch():
    data = body()
    status = data.get("open")
    if not isinstance(status, bool):
        return fail(400, "open 必须为布尔值")
    STATE["incognito"] = status
    return ok({"open": status}, "无痕模式已开启" if status else "无痕模式已关闭")


# ---------------- DJ 音乐播放器 ----------------
@app.get(PREFIX + "/dj/playlist")
def dj_playlist():
    return ok({"total": len(SONGS), "list": SONGS}, "查询成功")


@app.post(PREFIX + "/dj/play")
def dj_play():
    data = body()
    song_id = data.get("song_id")
    song = next((s for s in SONGS if s["song_id"] == song_id), None)
    if song is None:
        return fail(404, "歌曲不存在")
    STATE["dj"]["playing"] = song_id
    return ok({"song_id": song_id, "playing": True, "duration": song["duration"]}, "开始播放")


@app.post(PREFIX + "/dj/volume")
def dj_volume():
    data = body()
    volume = data.get("volume")
    if not isinstance(volume, int) or isinstance(volume, bool) or not (0 <= volume <= 100):
        return fail(400, "音量必须在 0-100 之间")
    STATE["dj"]["volume"] = volume
    return ok({"volume": volume}, "音量设置成功")


@app.post(PREFIX + "/dj/eq")
def dj_eq():
    data = body()
    mode = data.get("mode")
    if mode not in EQ_MODES:
        return fail(400, "均衡器模式仅支持 normal/rock/jazz/vocal")
    STATE["dj"]["eq"] = mode
    return ok({"mode": mode}, "均衡器设置成功")


@app.post(PREFIX + "/dj/play_mode")
def dj_play_mode():
    data = body()
    mode = data.get("mode")
    if mode not in PLAY_MODES:
        return fail(400, "播放模式仅支持 sequence/loop/single/random")
    STATE["dj"]["play_mode"] = mode
    return ok({"mode": mode}, "播放模式设置成功")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "9200"))
    print(f"Mock 浏览器接口服务启动：http://127.0.0.1:{port}{PREFIX}")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
