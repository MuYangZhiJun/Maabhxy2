# 崩坏学园2 小助手（bh2-maa）

基于 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 的崩坏学园2（崩崩）自动化助手：
**图像识别 + 模拟点击**，跑在 PC 上控制安卓模拟器或真机，把每天的日常点完。

> 从官方模板 [MaaPracticeBoilerplate](https://github.com/MaaXYZ/MaaPracticeBoilerplate) 起步，
> 目录结构、JSON Schema、校验工具都沿用官方那一套，方便跟上上游更新。

---

## ⚠️ 先读这段

**本项目 100% 由 AI 代工完成。** 从流程设计、模板截图裁剪、坐标标定，到 agent 脚本和这份文档，
全部是 AI 在真人指导下做的 —— 所以：

- 它**没有经过长期实战检验**，逻辑上尽量做稳（每处回退、兜底、阈值都是实测出来的），
  但游戏一更新 UI、活动一换，识别就可能失效；
- 建议**先拿小号或者低风险地试**，别一上来就挂整天的任务；
- 遇到问题欢迎开 issue，把「哪个任务 + 卡在哪一步 + `debug/agent.log` 的最后几行」带上，
  定位会快很多。

**另外**：自动化操作违反游戏的用户协议，用不用、怎么用，风险和后果都由使用者自己承担。

---

## 它能做什么

| 任务 | 干什么 | 现状 |
| --- | --- | --- |
| 启动崩坏学园2 | 打开游戏、过掉登录/公告/资源下载提示，停在主界面 | ✅ |
| 领取邮件 | 一键领取附件、领取体力、删除已读（可选自动读邮件） | ✅ |
| 领取奖励 | 每日存在感 + 每周任务 + **吼姆的礼物**，三个可分开勾 | ✅ |
| 使魔探险 | 领已完成的探险奖励，再把空位一键派满 | ✅ |
| 商店购物 | 进礼包商店把当天能白拿的买掉（不花水晶） | ✅ |
| 关卡战斗 | 选中的关卡一路打到没体力：**虚轴之庭 / 使魔的爱 / 活动 BONUS** | ✅ |
| 重复刷关 | 重复刷 BONUS 关（阵营战、赌马这类），可指定轮数 | ✅ |

### 「重复刷关」和「关卡战斗 · 活动 BONUS」是同一套逻辑

同一条链、同一批节点、同一个 agent 动作，区别只有两个选项：

| | 关卡战斗 · 活动 BONUS | 重复刷关 |
| --- | --- | --- |
| 刷几轮 | 固定「一直打到没体力 / 双倍体力用完」 | 你填几轮就几轮（`刷取次数`） |
| 体力不足 | 只兑换免费的双倍体力 | 多一个开关：`碎水晶` —— 勾了才花水晶补体力 |

---

## 环境要求

| 项 | 要求 |
| --- | --- |
| 系统 | Windows（理论上 macOS / Linux 也行，但没测过） |
| 模拟器 | MuMu Player 12（其它能连 adb 的模拟器应该也可以） |
| 游戏分辨率 | **1280×720 横屏** —— 所有 roi 和坐标都是按这个标定的，别的分辨率会全歪 |
| Python | 3.9+ |
| Python 包 | `python -m pip install maafw==5.13.0` ⚠️ **必须和 GUI 自带的 MaaFramework 同版本**，不一致会卡在「正在启动 Agent」 |
| GUI | [MFAAvalonia](https://github.com/MaaXYZ/MFAAvalonia)（下面的脚本会自动下载） |

---

## 怎么用

### 方式一：从源码跑（完整功能，推荐）

```sh
git clone https://github.com/MuYangZhiJun/Maabhxy2.git
cd Maabhxy2

python -m pip install maafw==5.13.0   # 版本一定要和 GUI 自带的一致
python tools/install.py               # 装 MaaFramework 到 deps/
python tools/get_gui.py               # 下 MFAAvalonia 并组装出 gui/

gui/MFAAvalonia.exe                   # 双击，然后勾任务 → 开始
```

第一次打开 GUI 需要配一次控制器：adb 路径填模拟器自带那份、地址填 `127.0.0.1:16384`。

### 方式二：只要资源包

下载 [Releases](../../releases) 里的 `bh2-maa-<版本>.zip`，解压得到：

```
interface.json      ← 任务与选项定义
resource/           ← pipeline + 模板图
agent/              ← Python agent（自动战斗、刷关）
```

把它作为资源放进 MFAAvalonia 即可。

### 方式三：用 GUI 的「更新资源」

在 MFAAvalonia 里把本仓库作为资源源加进去，之后点「更新资源」就会读 `interface.json` 里的
`github` 字段比对版本、自动更新。（想自己发布的话看 [`PUBLISH.md`](PUBLISH.md)。）

### 命令行跑单个任务（调试用，不需要 GUI）

```sh
python tools/run_task.py                  # 列出所有任务
python tools/run_task.py 领取邮件          # 跑一个任务
python tools/run_task.py 重复刷关 --option 次数=3
python tools/run_task.py 领取邮件 --case 邮件操作=领取附件   # 复现"GUI 里只勾了这一项"
```

每个节点命中情况会打到屏幕，同时落一份 UTF-8 到 `debug/run_nodes.log`。

想单独测**一个节点**（比如"这一步到底点动没有"）：

```sh
python tools/run_node.py 日常_活动BONUS_选好友
python tools/run_node.py 日常_活动BONUS_选好友 '{"target":[682,651,0,0]}'
```

（`run_task.py --node` 不带 override，而很多节点在文件里是 `enabled: false`，
单独跑等于"没启用"；`run_node.py` 会自己把 `enabled` 打开。）

---

## 怎么启动

**双击根目录的「启动小助手.bat」** —— 它会先确认模拟器连得上（连不上会提示你先开 MuMu），
再打开图形界面。然后在界面里勾任务、点「开始」。

任务顺序建议这么勾（前一个跑完自动接下一个）：

```
启动崩坏学园2 → 使魔探险 → 领取邮件 → 商店购物 → 关卡战斗 → 领取奖励
```

只想跑一个任务、不想开界面：

```sh
python tools/run_task.py 领取邮件
python tools/run_task.py 重复刷关 --option 次数=3
```

---

## 怎么自启（每天自动跑）

MFAAvalonia **自带定时任务**，不用去折腾 Windows 计划任务。三步：

**1. 让界面开机就在**
按 `Win + R`，输入 `shell:startup` 回车，把 `gui\MFAAvalonia.exe` 的**快捷方式**丢进那个文件夹。

**2. 在界面里配定时任务**
MFAAvalonia 有最多 **7 个定时槽**（配置键名是 `Timer.Timer1` ~ `Timer.Timer7`，
在设置里找「定时任务 / Timer」那一块）。每个槽填一个时间 + 选好要跑的那套配置。

**3. 让模拟器也在**
游戏得跑在模拟器里，所以模拟器也得在：

- MuMu Player 12 设置里打开「开机自启」；或者
- 在 MFAAvalonia 的实例设置里把「软件路径」填成模拟器的启动程序 ——
  这样它会在跑任务前先把模拟器拉起来（配置项就是日志里那个 `SoftwarePath`）

⚠️ **注意两点**：

- 定时任务靠界面里的定时器触发，所以**界面必须一直开着**（第 1 步就是干这个的）
- **别把时间设在游戏维护时段**（一般是周四），维护时进不去游戏，任务会失败

---

## 常见问题

**Q：为什么必须 1280×720？**
所有 roi（识别区域）和点击坐标都是按 1280×720 标定的。分辨率不同 → 全部错位。
模拟器设置里把游戏分辨率调成 720p 横屏即可。

**Q：卡在「正在启动 Agent」怎么办？**
九成是 **Python 的 `maafw` 版本和 GUI 自带的 MaaFramework 不一致**（agent 走框架内部协议，
大版本对不上就连不上）。查一下 GUI 的 `runtimes/win-x64/native/MaaFramework.dll` 里的版本号，
把 `maafw` 装成同一个版本（当前是 `5.13.0`）。

**Q：活动和关卡认不出来了？**
崩崩的活动每期轮换，卡片名字天天变。所以项目**不认活动名**，认的是稳定特征
（比如活动卡片的「难度指数：B」「剩余时间」标签、关地图上的金色「BONUS」标签）。
如果连这些也变了，就需要重新裁模板（见下面）。

**Q：体力不够会花我的水晶吗？**
默认不会。「碎水晶」这个开关默认关闭；不勾的话体力不足就干净收工，
只会尝试兑换**免费**的双倍体力。

**Q：游戏更新后一堆识别失败？**
UI 一动模板就失效，这是图像识别的宿命。项目里带了工具重新标定：

```sh
python tools/crop.py 截图.png x y w h 输出.png --scale 3 --grid 20   # 裁模板（带坐标网格）
python tools/check_template.py 日常/xxx.png --shots 截图目录          # 给模板打分
python tools/template_health.py                                      # 全部模板体检
python tools/pick_template.py --shots 截图.png --candidate 新图.png    # 候选图 vs 现用图
```

**Q：想直接看"屏幕现在写的是什么"？**
不用眯眼看图，让 OCR 读给你听（排查神器，装一次就行）：

```sh
python -m pip install rapidocr-onnxruntime
python tools/read_screen.py --live                 # 把当前屏幕上所有文字连坐标打出来
python tools/read_screen.py 截图.png --crop 600,500,600,140   # 只看某一块（按钮小字要放大）
python tools/read_screen.py --tap 254 298          # 点一下再看，逐屏排查用
python tools/ascii_view.py 截图.png --color        # 实在没招了：转成字符画看布局
```

---

## 目录结构

```
assets/interface.json          任务与选项定义（JSONC，带注释）
assets/resource/pipeline/*.json 流水线：节点、识别、动作、跳转
assets/resource/image/         模板图（所有识别的依据）
agent/                         Python agent：自动战斗、BONUS 刷关循环
tools/                         开发工具（跑任务、校验、裁图、打分、体检、打包）
                               其中 tools/read_screen.py 能把屏幕上的字读出来（OCR 排查用）
HANDOFF.md                     开发笔记：当前状态、待办、踩过的坑（改之前先看这个）
PUBLISH.md                     发布与本仓库作为更新源的说明
```

改了 pipeline 或补了模板图之后：

```sh
python tools/check_env.py              # 引用检查（不存在的节点、没登记的图）
python tools/validate_schema.py        # 官方 JSON Schema 校验
python tools/get_gui.py --sync-only    # 同步进 gui/
```

---

## 致谢

- [MaaFramework](https://github.com/MaaXYZ/MaaFramework) —— 识别与控制的底座
- [MaaPracticeBoilerplate](https://github.com/MaaXYZ/MaaPracticeBoilerplate) —— 项目模板与校验工具
- [MFAAvalonia](https://github.com/MaaXYZ/MFAAvalonia) —— 图形界面
- [MMDFTJ/MaaBhxy2](https://github.com/MMDFTJ/MaaBhxy2) —— 功能上的参考

## 许可

MIT，见 [LICENSE](LICENSE)。
