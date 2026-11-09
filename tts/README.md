# TTS 服务

本机常驻的 Qwen3-TTS，加载一次模型，HTTP 出 WAV。没有 API key，不上云。

## 运行

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./start.sh          # :6211
curl http://127.0.0.1:6211/health
```

只支持 Apple Silicon（mlx-audio）。

## 接口

```text
POST /tts     {"text":"...","mood":"auto"}
GET  /health
```

`mood` 可选 `auto / lively / soft / warm`，`auto` 会按内容挑一个。
默认音色 `sohee`，模型 `mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit`。

## 环境变量

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `TTS_MODEL` | ...CustomVoice-8bit | 换 bf16 更细，量化版更有“电”味 |
| `TTS_VOICE` | sohee | 音色 |
| `DEFAULT_MOOD` | lively | 默认语气；轻松、俏皮，但不挑衅 |
| `HF_ENDPOINT` | https://hf-mirror.com | 模型下载镜像 |
