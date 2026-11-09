# 直播运行手册

从零把这套「记忆 + 形象 + 声音 + 弹幕」跑起来。整条链路都在本机，不依赖云端数字人或在线 TTS。

## 端口一览

| 端口 | 是什么 | 在哪 |
| --- | --- | --- |
| 6200 | 大脑（记忆 + 人格 + DeepSeek） | **Hippocampus 仓库**，不在本项目 |
| 6210 | 静态页（画面、场控、素材） | `stream/start.sh` |
| 6211 | 本机 TTS（Qwen3-TTS） | `tts/start.sh` |
| 6220 | 弹幕桥 | `stream/start.sh` |
| 8188 | ComfyUI（只用于烘素材） | 手动 |

## 最短路径

```bash
# 0) 大脑先起来（Hippocampus 仓库，需要 DEEPSEEK_API_KEY）
#    默认 ws://127.0.0.1:6200/ws

# 1) 依赖
python3 -m venv .venv
./.venv/bin/pip install -r stream/requirements.txt
python3 -m venv tts/.venv
./tts/.venv/bin/pip install -r tts/requirements.txt

# 2) 启动
./start.sh

# 3) 打开
open http://127.0.0.1:6210/stream/stream.html
```

## 画面构成

```text
背景     1920×1088 客厅，白天/夜晚按时间自动切
人物     1366×768 透明 WebM，双 video 交叉淡入
顶部     她在说 / 上网中（站点 + 标题 + 摘要）
左侧     互动指南（关键词、礼物对应动作）
右侧     今日互动榜 + 弹幕/互动/礼物数 + 今日 tokens
底部     说话时的字幕
右下     AI 生成内容（合规标注）
```

弹幕不画在页面上：直播平台自己会叠，两份会撞。

## 状态机

```text
待机      四套 idle 轮换，各 5.2 秒；每三轮插一个随机小动作
          （伸懒腰 / 打哈欠 / 摸头 / 理头发 / 摇头）
说话      收到回复 → talk 动画 + 字幕 + TTS
表情      回复附带 expression → 播一次 happy/angry/confused/smirk/shy/sad/laugh/sigh/surprised
动作      回复带动作 → 点头 / 挥手 / 摇头 / 跳一下
手动动作  场控面板可触发 挥手/点头/思考/比心/鼓掌/大笑/叹气/惊讶/委屈/摇头/跳一下/伸懒腰/打哈欠/摸头/理头发
摸鱼      默认状态：掏出手机 → 循环刷 → 收起
思考      弹幕进来立刻托腮，回复到达即切说话，25 秒没回复自动退出
零食/看书  安静 100 秒后自己掏出饼干或书，40 秒循环；有人说话先收起来再开口
自动上网  安静 20 秒后每 15 秒换一个页面，每 4 页嘟囔一句
```

道具动作统一是三段式：`*_in`（掏出来）→ `*_loop`（循环）→ `*_out`（收回去）。
`loop` 用 `in` 的最后一帧当参考图生成，道具才不会在循环时消失。

## 弹幕怎么进来

```text
B 站弹幕      → bilibili/danmaku.py  →  POST :6220/comment
B 站礼物/上舰 → 同一个适配器          →  POST :6220/gift
手动          → stream/feed.py 或场控页
```

画面右侧的互动榜由桥统计，写在 `stream/.stats.json`，按日期自动清零。

B 站适配器需要 `SESSDATA`，做法见 [`bilibili/README.md`](../bilibili/README.md)。

## 推流（OBS）

1. 源类型 **浏览器源**（不要用窗口采集，否则没有透明）
2. 地址 `http://127.0.0.1:6210/stream/stream.html?audio=1`
3. 1920×1080 / 30fps
4. 右键浏览器源 → **属性 → 通过 OBS 控制音频**（Control audio via OBS）必须勾上，
   否则声音会放到系统扬声器，推流里是静音的
5. 推流：服务选「自定义」，填平台给的地址和密钥

`?audio=1` 是必须的：页面默认静音，只有带这个参数才出声，这样你在别的标签页预览时不会和 OBS 撞音。

改完前端后 OBS 会缓存旧页面，用 `stream/refresh_obs.py` 强制刷新。

## B 站开播

B 站从 2025-05-26 起要求第三方开播账号 **≥5000 粉**。低于这个数时：

```bash
cd bilibili
python go_live.py --cookie cookie.txt        # 打印推流地址 + 密钥
python go_live.py --cookie cookie.txt --stop # 结束直播
```

另外两个坑：

- **海外 IP** 会返回 `60045`，开播和推流都要走国内网络
- 每次开播可能需要**人脸认证**，按接口返回的链接在手机 App 里做

## 素材从哪来

形象动画全部由本机 ComfyUI 生成，流程见 [`taozi_chibi/README.md`](../taozi_chibi/README.md)。
关键几条：

- 首帧 = 尾帧 = 同一张图，才有无缝循环
- 过渡动作用 `--no-last`，否则模型会把刚拿出来的道具收回去
- 几何统一用「头宽」，不要用包围盒高度：她抬手、拿手机都会把包围盒撑大，
  按高度缩放会把她整个人压小
- 所有素材统一 `--anchor-head 311 --align-bottom 671 --align-cx 683 --keep-frame`
- `in` 用 `--align-ref last`、`loop`/`out` 用 `--align-ref first`，接缝才不会跳
- 长镜头若有缓慢漂移，加 `--track-top`（只做平移，不缩放）
- `--keep-frame` 必须加：默认的 `compose()` 会再裁切并按总高度缩放到 537，
  把前面的对齐全部抵消
- 单条通过率约三分之一，按 3 倍排产

## 环境变量

| 变量 | 默认 | 作用 |
| --- | --- | --- |
| `CHARACTER_NAME` | 大肥鱼 | 人设里的自称（大脑侧） |
| `CHARACTER_ALIASES` | 桃子姐姐,肥鱼 | 别名（大脑侧） |
| `LOOK_MIN_INTERVAL` | 120 | 主动查资料的最小间隔（秒） |
| `STREAM_BROWSE_TICK` | 15 | 自动上网换页间隔（秒） |
| `STREAM_BROWSE_QUIET` | 20 | 安静多久开始上网 |
| `STREAM_BROWSE_COMMENT_EVERY` | 4 | 每几页嘟囔一次 |
| `TTS_MODEL` | ...CustomVoice-8bit | 换成 bf16 声音更细 |
| `TTS_VOICE` | sohee | 音色 |
| `DEFAULT_MOOD` | brat | 语气 |

## 已知限制

- 直播平台会限流；页面延迟 8–15 秒（DeepSeek 首字延迟 + 联网二次作答）
- 搜索质量一般，B 站/百度/知乎对抓正文有 403，自动上网只用搜索摘要
- 5 秒循环靠多套素材轮换来掩盖，单条看久了仍能看出重复
- 形象是 CC BY-NC-SA 4.0 社区二创，**禁止商用**
