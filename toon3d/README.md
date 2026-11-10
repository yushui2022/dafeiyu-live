# 三渲二 · 离线透明 WebM（A 方案）

把 3D Q 版模型渲染成透明 PNG 序列，再编码成 **1366×768 / 24fps / VP9 alpha WebM**，直接替换直播页里的角色动作。

直播链路不变：大脑 `:6200`、弹幕桥 `:6220`、页面 `:6210`、TTS `:6211`。

## 目录

```text
toon3d/
  render_blender.sh    Blender 批量渲染 PNG 序列
  render_to_webm.py    对齐 + 编码成透明 WebM
  requirements.txt     numpy / Pillow / scipy
```

## 1. 准备模型

需要 `.blend` 或 `.vrm`，包含：

- Q 版头身比例
- Humanoid 骨骼
- 表情 BlendShape
- 头发 / 裙摆 SpringBone

风格目标：Q 版、赛璐璐、粗描边、二分阴影、少高光，不要 PBR。

## 2. Blender 渲染

在 `.blend` 里设置：

```text
分辨率    1366×768
帧率      24fps
背景      Film Transparent
输出      PNG RGBA
```

然后：

```bash
BLENDER=/Applications/Blender.app/Contents/MacOS/Blender \
./toon3d/render_blender.sh scene.blend /tmp/toon_frames
```

## 3. 对齐并编码

```bash
./toon3d/.venv/bin/python toon3d/render_to_webm.py \
  --input /tmp/toon_frames \
  --output assets/toon3d/idle_a.webm \
  --head-width 311 --bottom 671 --center 683
```

默认锚点和现有 2D 素材一致：

```text
头宽 311 / 脚底 671 / 中心 683
```

如果 3D 模型比例不同，先用 `--head-width 0` 让脚本取整条中位数，再确定新的脚底和中心。**同一套动作必须使用同一组锚点，不能和旧素材混用。**

## 4. 在直播页预览

默认仍然使用 `assets/small/`。加 `set=toon3d` 切换到新素材：

```text
http://127.0.0.1:6210/stream/stream.html?audio=1&set=toon3d
```

OBS 里也可以先用这个地址做一次对比，满意后再把 OBS 地址固定过去。

## 5. 第一批只做三条

```text
idle_a    待机循环
talk      说话
wave      挥手
```

先看 10 秒样片：脸像不像、光影融不融、接缝跳不跳。过了再补表情和道具动作。

## 依赖

```bash
python3 -m venv toon3d/.venv
./toon3d/.venv/bin/pip install -r toon3d/requirements.txt
```

需要系统里有 `ffmpeg`。

## 造型草模

`build_blockout.py` 用 Blender 基础体生成第一版 Q 版形状草模，包含三渲二材质、描边和三视图渲染：

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b \
  --python toon3d/build_blockout.py -- \
  --blend /tmp/大肥鱼_blockout.blend \
  --preview-dir /tmp/大肥鱼_preview
```

## VRM 第一课

`toon3d/viewer/` 是一个本地 three.js + three-vrm 学习页：加载 VRM、摇头、眨眼、播放内置动作、切透明背景。

```text
http://127.0.0.1:6210/toon3d/viewer/
```

模型文件放在 `toon3d/viewer/models/`，已被 `.gitignore` 忽略，不进仓库。
