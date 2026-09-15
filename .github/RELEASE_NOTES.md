## 怎么用

**方式一（推荐）**：下载 `bh2-maa-<版本>.zip`，解压得到 `interface.json` + `resource/` + `agent/`，
放进 [MFAAvalonia](https://github.com/MaaXYZ/MFAAvalonia) 当资源用。

**方式二（能自动更新）**：在 MFAAvalonia 里把本仓库加为资源源，之后点「更新资源」，
它会读 `interface.json` 里的 `github` 字段比对版本、自动更新。

**方式三（开发）**：下载 `bh2-maa-<版本>-source.zip`，里面有完整源码和 `tools/`，能自己构建 GUI：

```sh
python -m pip install maafw==5.13.0
python tools/install.py
python tools/get_gui.py
gui/MFAAvalonia.exe
```

## 注意

- ⚠️ Python 的 `maafw` 必须和 GUI 自带的 MaaFramework **同版本**（当前 `5.13.0`），
  不一致会一直卡在「正在启动 Agent」。
- 游戏内分辨率要 **1280×720 横屏**，所有识别区域都按这个标定。
- 「重复刷关」和「关卡战斗 · 活动 BONUS」是同一套逻辑，只差「刷取次数」和「碎水晶」两个选项。
- 完整说明（怎么启动、怎么自启、常见问题）看仓库的 [README](../README.md)。

> 本项目 **100% 由 AI 代工完成**，没有经过长期实战检验，建议先小号或低风险地试。
> 自动化操作违反游戏用户协议，使用风险自负。
