# 直播画面 + 弹幕桥

浏览器里的一整套直播画面：人物、背景、回复框、互动指南、今日榜、字幕。

## 文件

| 文件 | 作用 |
| --- | --- |
| `stream.html` / `stream.css` | 画面结构、布局、日夜配色 |
| `stream.js` | 双 `<video>` 交叉淡入、待机轮换、表情/动作、自动上网、互动 |
| `bridge.py` | 弹幕桥：去重、排队、限速、互动统计、自动上网循环 |
| `control.html` | 场控面板：切场景、15 个动作按钮、手动发弹幕 |
| `feed.py` | 命令行发弹幕 |
| `refresh_obs.py` | 改完前端后强制 OBS 刷新缓存 |
| `start.sh` | 起静态页 + 弹幕桥 |

## 运行

```bash
# 需要先装依赖
../.venv/bin/pip install -r requirements.txt

# 起静态页(:6210) + 弹幕桥(:6220)
./start.sh
```

大脑在 `:6200`（Hippocampus 仓库），TTS 在 `:6211`（`../tts`）。

## 接口

```text
POST :6220/comment   {"user":"小明","text":"在吗"}
POST :6220/gift      {"user":"小明","gift":"小心心","count":1}
POST :6220/event     {"name":"wave"}          # 挥手/点头/思考/比心/鼓掌/摇头/跳一下/伸懒腰/打哈欠/摸头/理头发
POST :6220/scene     {"name":"work"}          # idle / talk / work
GET  :6220/stats     今日 tokens + 互动榜
GET  :6220/health
WS   :6220/ws        stage 客户端
```

## 一次说话发生了什么

```text
POST /comment
  → 弹幕桥去重、排队
  → 大脑回 turn {say, expression, actions, looking_at}
  → 画面：顶部气泡 + 表情 + 动作
  → POST :6211/tts 拿 WAV，用 <audio> 播
  → 播完回待机
```

OBS 的浏览器源要勾选 **「通过 OBS 控制音频」**，否则 `<audio>` 只会从系统扬声器出来。
