<p align="center">
  <img src="docs/images/logo.png" alt="大肥鱼 · AI 直播" width="920">
</p>

<p align="center">
  一个会自己上网、自己找事做、跟弹幕聊天的 Q 版 AI 主播。<br>
  弹幕进来 → 大脑回话 → 本机 TTS 出声 → 透明 Q 版形象落在客厅里 → OBS 推到 B 站。<br>
  <sub>整条链路都在本机，不依赖云端数字人、不依赖在线 TTS API。</sub>
</p>

<p align="center">
  <a href="https://github.com/yushui2022/dafeiyu-live"><img src="https://img.shields.io/badge/status-live-69d3b0?style=flat-square" alt="status: live"></a>
  <a href="https://github.com/yushui2022/Hippocampus"><img src="https://img.shields.io/badge/brain-Hippocampus-9d7cff?style=flat-square" alt="brain: Hippocampus"></a>
  <img src="https://img.shields.io/badge/runtime-macOS%20%7C%20Apple%20Silicon-7ec7ff?style=flat-square" alt="runtime: macOS Apple Silicon">
  <img src="https://img.shields.io/badge/code-MIT-9aa0b5?style=flat-square" alt="code license: MIT">
</p>

![直播画面](docs/images/live.jpg)

<p align="center"><sub>实际直播画面：Q 版角色、客厅场景、字幕、互动面板和 AI 生成内容标注。</sub></p>

<p align="center">
  <a href="#系统总览">系统总览</a> ·
  <a href="#快速开始">快速开始</a> ·
  <a href="#素材制作">素材制作</a> ·
  <a href="#直播">直播配置</a> ·
  <a href="#授权">授权与署名</a>
</p>

## 系统总览

**这个仓库只负责「怎么播」。** 角色的记忆、人格和 DeepSeek 调用在
[Hippocampus](https://github.com/yushui2022/Hippocampus)（海马体记忆系统）里，
本项目通过 WebSocket 连它的 `:6200`。

| Hippocampus | 这个仓库 |
| --- | --- |
| 记忆、人格、模型调用 | 画面、动作素材、TTS、弹幕、推流 |
| `:6200` 大脑 | `:6210` 画面 · `:6211` 语音 · `:6220` 弹幕桥 |

这样拆开的原因：记忆系统是通用的，直播只是它的一个出口。
换平台、换形象、换音色，大脑都不用动。

![系统架构](docs/images/architecture.png)

<p align="center"><sub>运行时数据流：B 站事件 → 直播编排 → Hippocampus → 画面与语音 → OBS。</sub></p>

## 直播行为

```text
默认      掏出手机刷 → 顶部滚动「上网中 · 站点 + 标题 + 摘要」
有人说话  立刻收好手机 → 托腮思考 → 开口回复 → 点头/表情
安静 100 秒 自己找点事：吃饼干 / 看书，40 秒后收起来
收礼物    小心心→比心，辣条→大笑，上舰→鼓掌
关键词    发「比心 / 贴贴 / 跳一个 / 笑一个 / 摸头」会触发对应动作
```

## 仓库地图

| 路径 | 负责什么 |
| --- | --- |
| [`stream/`](stream/README.md) | 直播画面、场控、弹幕桥、互动统计、OBS 刷新 |
| [`assets/`](assets/) | 客厅背景；[`assets/small/`](assets/small/) 是 35 条透明动作 |
| [`tts/`](tts/README.md) | 本机 Qwen3-TTS，Sohee 音色与语气控制 |
| [`taozi_chibi/`](taozi_chibi/README.md) | ComfyUI + MiniMax-H3 动作生成、抠像、几何统一 |
| [`bilibili/`](bilibili/README.md) | B 站弹幕/礼物适配器与低粉开播脚本 |
| [`docs/LIVE.md`](docs/LIVE.md) | 端口、启动、OBS、B 站、环境变量和故障排查 |

## 快速开始

### 运行前准备

| 组件 | 用途 | 必需 |
| --- | --- | --- |
| Hippocampus | 记忆、人格、DeepSeek，监听 `:6200` | 是 |
| Python 3.10+ | 直播桥与脚本 | 是 |
| Apple Silicon + MLX | 本机 Qwen3-TTS | 语音必需 |
| OBS | 浏览器源与 RTMP 推流 | 开播必需 |
| ComfyUI | 只在制作新动作时使用 | 运行直播不需要 |

### 启动

```bash
# 0) 先启动 Hippocampus 的 companion
#    需要 DEEPSEEK_API_KEY；默认地址 ws://127.0.0.1:6200/ws

# 1) 安装直播桥依赖
python3 -m venv .venv
./.venv/bin/pip install -r stream/requirements.txt

# 2) 安装 TTS 依赖（Apple Silicon / mlx-audio）
python3 -m venv tts/.venv
./tts/.venv/bin/pip install -r tts/requirements.txt

# 3) 启动 :6210 / :6211 / :6220
./start.sh
```

### 验证

```bash
curl http://127.0.0.1:6200/health   # Hippocampus
curl http://127.0.0.1:6211/health   # TTS
curl http://127.0.0.1:6220/health   # 弹幕桥
open http://127.0.0.1:6210/stream/stream.html
open http://127.0.0.1:6210/stream/control.html
```

OBS 使用带 `?audio=1` 的地址，场控页用于手动触发动作和测试对话。

### 停止

```bash
./stop.sh
```

凭证只放在本机：`.env`、B 站 Cookie、推流密钥、统计文件和虚拟环境都不会进入仓库。

---

## 素材制作

这部分是整套东西里最花时间的：**35 条动作，全是本机生成的，一条大约 8–12 分钟，通过率约三分之一。**

### 1. 总览

```text
一张 Q 版立绘
  → 合成到纯绿 #00FF00 画布（1344×768）
  → MiniMax-H3 FL2V：首帧=尾帧，4 步 turbo LoRA
  → 24fps / 73 帧（约 3 秒）绿幕 mp4
  → 质检（构图是否稳定、有没有贴边）
  → HSV 绿幕抠像 + 溢色清理
  → 统一几何（头宽 / 脚底 / 中心）
  → VP9 alpha WebM（约 1–2 MB）
  → assets/small/
```

![三段流水线](docs/images/pipeline.jpg)

*左：模型出的绿幕原片。中：抠掉背景后的透明帧。右：合成到客厅、真正推流的画面。*

### 2. 环境

| 项 | 值 |
| --- | --- |
| ComfyUI | `127.0.0.1:8188` |
| 视频模型 | `MiniMax-H3-FL2VA-Pruned-Q5_K_M.gguf` |
| LoRA | `minimax_h3_fl2v_turbo_4step_v1.0_768p` |
| 文本编码器 | `qwen3vl_32b_minimax_h3-Q4_K_M.gguf` |
| VAE | `minimax_h3_video_vae_fp16` |
| 分辨率 | 1344×768 |
| 帧数 | 73（约 3 秒 @24fps） |
| 步数 / cfg | 4 / 1.0 |

> 只有 Q5 那份 GGUF 能用。Q6/Q8 没有 KV 元数据，ComfyUI 会报
> `Unknown model architecture`；Abiray 的 Q8 没剪枝，36 GB 跑不动。

### 3. 种子图

```text
taozi_chibi/seed/q_stream_768.png   ← 站姿立绘
```

把它复制到 ComfyUI 的 `input/` 目录，`h3_clip.py` 默认就用 `q_stream_768.png`。
模型会把首帧**拉伸**到 1344×768，所以这张图本身必须是 16:9 附近的比例，否则人物会被压扁。

### 4. 一条动作：出片

在仓库根目录执行：

```bash
# 1) 出片（首帧 = 尾帧，天然循环）
python taozi_chibi/h3_clip.py \
  --name idle_a \
  --prompt taozi_chibi/prompts/idle.txt \
  --seed 771003 \
  --length 124 \
  --steps 4 --cfg 1.0

# 2) 质检
python taozi_chibi/qc_clip.py reference/h3_idle_a.mp4

# 3) 抠像 + 统一几何 + 编码
python taozi_chibi/h3_to_webm.py reference/h3_idle_a.mp4 assets/small \
  --name idle_a --height 768 --crf 20 \
  --anchor-head 311 --align-bottom 671 --align-cx 683 --keep-frame
```

过渡动作（掏出 / 收回）要加 `--no-last`，并把结束帧裁到和下一段共用的那一帧。

![绿幕源分帧](docs/images/source_frames.jpg)

*一条 3 秒源片抽 6 帧。质检就是看这种连续帧：人物大小、位置、双脚有没有漂。*

### 5. 质检在看什么

`qc_clip.py` 量的是绿幕里人物的边距：

```text
margins first  top=140  bottom=96
margins min    top=140  bottom=96
OK: framing stable
```

- `FAIL: character reaches the frame edge` → 模型把镜头推近了，整条作废
- `WARN: framing drifts vertically by N px` → 先判断是镜头漂移还是人物自己的动作：
  量脚底，脚底不动就是她在低头/塌肩，属于表演，不要做稳定化
- 贴边、文字、第二个人的脸，都是硬伤，直接重跑

### 6. 几何统一：最容易踩的坑

#### 用「头宽」当锚点，不要用包围盒高度

她抬手、拿手机都会把包围盒撑大。按高度缩放会把她整个人压小：

```text
待机头宽   311
拿手机     339   ← 只大 9%，不是她变小
```

所以缩放锚点是 **头宽 311**，测量时只取**最大连通块**的上 42% 区域——
符号、手机、粒子都是独立连通块，不能算进头宽。

![几何锚点](docs/images/geometry.jpg)

*这是 think 的一条：符号把包围盒撑到 587px，人物本体只有 515px。按包围盒缩放会把她压小，按头宽 307px 就不会。*

#### `--keep-frame` 必须加

`h3_to_webm.py` 默认的 `compose()` 会再裁切一次，并按总高度缩放到 537。
它会把前面做的对齐全部抵消，拿手机的素材会被压小 12%。`--keep-frame` 跳过这一步。

#### 三段式素材要对齐共用帧

```text
*_in     --align-ref last    按最后一帧对齐
*_loop   --align-ref first   按第一帧对齐
*_out    --align-ref first   按第一帧对齐
```

这样 `in → loop → out` 的接缝脚底误差能压到 1px 以内。
普通待机和表情用默认（整条中位数）即可。

#### 两个补丁

- `--track-top`：只做平移，用滑动平均去掉缓慢漂移，不缩放。人物自己点头不会被动
- `--floor 740`：把 y=740 以下的 alpha 清零，防止道具/爱心从画面底部滑出时留一条边

### 7. 循环、过渡、道具链

| 类型 | 怎么生成 | 用什么 |
| --- | --- | --- |
| 循环（待机、表情） | 首帧 = 尾帧 = 同一张图 | 默认 |
| 过渡（掏出、收回） | 只锁首帧，末帧自由 | `--no-last` |
| 道具循环 | **用 `in` 的最后一帧当参考图** | 默认 |

道具三段式最容易翻车：如果 `eat_in` 结尾把饼干吃完了，`eat_loop` 就会变成空手嚼。
解法是**截到饼干还在手里的那一帧**（这次是第 45 帧）当循环的参考图，
`eat_in` 本身也裁到那一帧结束。

看书更严格：`read_in` 第 58 帧书还开着，`read_loop` / `read_out` 都从这一帧生成，
三段的首尾帧完全重合，切换零跳变。

![道具三段式](docs/images/prop_chain.jpg)

*吃东西的三段：掏出（末帧饼干在手）→ 循环（饼干一直在）→ 收回（空手）。循环的参考图就是中间那一帧。*

### 8. 提示词模板

```text
这是用于视频抠像的绿幕素材。

背景必须自始至终是完全均匀的纯绿色 #00FF00 色块。绿色区域保持空白，
不出现任何东西：没有人脸、没有第二个人物、没有图案、没有渐变、没有阴影、没有边框。

画面里只有这一位 Q 版蓝发鲸鱼女仆，保持参考图中的画风、配色、比例、发型和五官完全不变。

镜头完全固定的全身中景，全程不推近、不拉远、不切换。
人物的大小、位置、双脚的位置从头到尾都不变。

画面里绝对不要出现任何文字、汉字、字母、数字、标志、logo、字幕或符号。

动作：<一句话，只写要发生什么>

首帧和末帧是同一个站姿。
```

#### 雷区

- **否定词会反噬。** 写「不要出现问号」反而容易画出问号。只描述想要的状态。
- **「想事情 / 疑惑 / 生气」很容易生成问号、感叹号、怒气蒸汽、星星。**
  符号本身可以接受（她也挺可爱），但人物尺寸不能变。
- **文字会被烘进像素。** 委屈那条两次在画面里生成了乱码汉字，整条作废。
- **坐姿会被镜头拉远。** 想让坐垫落地，模型直接把镜头拉远、人物缩成三分之一。
  坐着这条路线放弃，改成站着掏道具。
- **手部精细动作很难。** 胸前比心两次都只是合掌；改成**双手举过头顶围一个大爱心**才成。
- **爱心会往下掉。** 飞吻那条爱心一路沉到画面底边，只能重跑；提示词要写「向上飘」。

### 9. 失败模式

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 人物贴到画面边缘 | 模型推近成特写 | 弃用重跑 |
| 人物忽大忽小 | 按包围盒缩放了 | 改头宽锚点 + `--keep-frame` |
| 首尾不一致 | 循环参考图选错 | 用道具还在手里的那帧 |
| 画面里有乱码字 | 文字被烘进像素 | 弃用，提示词加禁止文字 |
| 爱心/道具从底部滑出 | 运动方向错了 | 重跑；或 `--floor` 兜底 |
| 循环一次闪一下 | 首帧和末帧不同 | 检查参考图，必要时裁到共用帧 |

### 10. 产能

```text
单条出片     8–12 分钟（4 步 / 73 帧 / 1344×768）
通过率       约 1/3
一条动作     平均要跑 3 次
35 条素材    前后跑了整整几天
```

想提高画质就加步数或上 1080p，但时间会翻倍。直播 1080p 的输出下，
768p 的素材已经够用，瓶颈在模型的动作稳定性，不在分辨率。

### 11. 编码与命名

```text
编码     VP9 alpha（yuva420p），CRF 20，24fps
输出     1366×768 画布（源 1344×768 + 左右各 11px）
体积     每条 1–2 MB
```

![透明分帧](docs/images/alpha_frames.jpg)

*编码后的 WebM 抽帧。棋盘格是透明区域，直接叠在直播画面上。*

### 12. 35 条成品

![动作总览](docs/images/action_grid.jpg)

*全部素材同一套几何：头宽 311 / 脚底 671 / 中心 683。*

命名约定：

```text
idle_a … idle_d        待机轮换
talk / click           说话 / 点击
expr_*                 表情
think / nod / wave     思考 / 点头 / 挥手
shake_head / jump / stretch / yawn / touch_head / fix_hair
work_in|loop|out       摸鱼（手机）
eat_in|loop|out        吃东西（饼干）
read_in|loop|out       看书
```

完整命令和参数表见 [`taozi_chibi/README.md`](taozi_chibi/README.md)。

---

## 直播

### OBS

1. 源类型 **浏览器源**
2. 地址 `http://127.0.0.1:6210/stream/stream.html?audio=1`
3. 1920×1080 / 30fps
4. 右键源 → **属性 → 通过 OBS 控制音频** 必须勾上
5. 推流：服务选「自定义」

`?audio=1` 是必须的：页面默认静音，只有 OBS 这个源带参数才出声，
这样你在别的标签页预览时不会和 OBS 撞音。

### B 站

```text
粉丝 ≥ 5000   网页开播设置里直接拿地址
粉丝 < 5000   bilibili/go_live.py（走直播姬的 pc_link 通道）
海外 IP       会返回 60045，必须走国内网络
每次开播      可能需要手机 App 做人脸认证
```

细节见 [`docs/LIVE.md`](docs/LIVE.md) 和 [`bilibili/README.md`](bilibili/README.md)。

## 踩过的坑

- **声音重叠**：Chrome 预览页和 OBS 同时播 TTS。改成默认静音 + `?audio=1`。
- **推流没声音**：OBS 浏览器源没开「通过 OBS 控制音频」，声音只进了系统扬声器。
- **网页里嘴动没声**：OBS 的 CEF 会挂起 Web Audio；TTS 改用 `<audio>` 元素播放。
- **切镜头跳动**：每条素材按整条中位数对齐，`in` 的最后一帧和 `loop` 的第一帧差十几像素；
  改成按共用帧对齐。
- **页面变糊**：早期 CSS 每帧对视频做 `rotate + scaleY` 和滤镜链，导致每帧重采样；
  改成整数平移后页面锐度从 499 提到 858。现在只保留 `translateX(-50%)`。
- **抖音人脸核验死循环**：默认摄像头被设成 OBS Virtual Camera，拍到的是大肥鱼。
  人脸核验必须用手机端，并先停掉虚拟摄像头。最后因为账号风控转到了 B 站。

## 授权

- **代码**：MIT
- **形象素材**：CC BY-NC-SA 4.0，**禁止商用**，署名见 [`ASSETS.md`](ASSETS.md)
- 画面常驻「AI 生成内容」标注
