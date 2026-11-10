# 第一课：让 VRM 跑起来

这是本地学习页，不是直播产品。

## 打开

直播静态服务已经占着 `:6210`，直接打开：

```text
http://127.0.0.1:6210/toon3d/viewer/
```

如果 6210 没开：

```bash
cd /Users/orlando/Documents/蓝色大肥鱼/dafeiyu-live
python3 -m http.server 6210
```

## 你会看到什么

- 一个真正的 VRM 3D 角色
- 鼠标拖动旋转，滚轮缩放
- 「摇头 6 秒」直接转头骨
- 「眨眼」驱动 BlendShape
- 「挥手」播放模型内置动作
- 「透明背景」切到 OBS 可用的透明画布

这页不是播放视频，是实时渲染：

```text
VRM 模型
  + MToon 材质
  + Humanoid 骨骼
  + BlendShape 表情
  + SpringBone 物理
  + 动画/程序驱动
  = 实时画面
```

## 换模型

页面上点「换一个 VRM」，选本地 `.vrm` 文件即可。

也可以把模型放进：

```text
toon3d/viewer/models/
```

模型文件被 `.gitignore` 忽略，不会进仓库。

## 当前默认模型

默认加载 `models/BlueFish-StarLite.vrm`，只用于本地学习/评估。

它的授权明确禁止：

- 作为个人形象直播
- 二次分发
- 商用

所以不要把这个模型接进直播，也不要提交到仓库。  
换成我们自己的模型后，才谈上线。

## 代码在哪

```text
toon3d/viewer/index.html   页面结构 + import map
toon3d/viewer/viewer.js    three.js + three-vrm + 摇头/眨眼/挥手
```

关键点：

- `GLTFLoader` + `VRMLoaderPlugin` 读 VRM
- `vrm.humanoid.getNormalizedBoneNode('head')` 拿头骨
- `head.rotation.y` 左右摇头
- `vrm.expressionManager.setValue('blink', 1)` 眨眼
- `AnimationMixer` 播内置 `HappyWave`
- `vrm.update(delta)` 更新 SpringBone
- `renderer alpha + setClearAlpha(0)` 透明背景

## 下一课

1. 把摇头/眨眼/挥手接到弹幕桥事件
2. 加 `?set=vrm`，和旧 2D 素材并存
3. 测试 OBS 浏览器源透明和 30fps
4. 再把模型换成我们自己的大肥鱼
