# 发布与更新（GitHub）

这份文档写给「要把这个项目放到 GitHub 上、让别人下载、并且能用 GitHub 源更新」的人。

---

## 一次性准备

### 1. 建一个自己的仓库

**别用模板仓库**（现在 `git remote` 指向的是 `MaaXYZ/MaaPracticeBoilerplate`，那是 MaaFramework 的模板，
不是你的项目）。在 GitHub 网页上新建一个空仓库，比如 `bh2-maa`，然后：

```sh
git remote set-url origin https://github.com/<你的用户名>/bh2-maa.git
git remote -v          # 确认已经不是 MaaXYZ 了
```

### 2. 改 `assets/interface.json` 里的三处

| 字段 | 现在是什么 | 要改成 |
| --- | --- | --- |
| `github` | `https://github.com/MaaXYZ/MaaPracticeBoilerplate` | **你自己的仓库地址** —— MFAAvalonia 的「更新资源」就是读这个字段 |
| `contact` | `改成你自己的仓库地址或交流群` | 你的仓库/群，或直接删掉这一行 |
| `welcome` | 还写着"模板图还没采集齐，只有启动和自动战斗能跑" | 更新成现在的实际情况 |

`github` 这一项最关键：**不改的话，别人点「更新资源」会去检查 MaaXYZ 的模板仓库**，
永远不会拿到你的更新。

### 3. 推上去

```sh
git add -A
git commit -m "feat: 崩坏学园2 小助手（日常清理 / 重复刷关 / 自动战斗）"
git push -u origin main
```

---

## 每次发版

> **现在发版是全自动的**：打个 `v*` 的 tag 推上来，GitHub Actions 会自己打包、自检、
> 建好 Release 并挂上两个 zip（见 `.github/workflows/release.yml`）。
> 手动打包只是为了本地先看一眼。

1. **把 `assets/interface.json` 的 `version` 往上加**（比如 `0.1.0` → `0.1.1`）。
   ⚠️ 这一步不能省：MFAAvalonia 的「更新资源」是**读这个字段**判断有没有新版本的，
   不改的话别人点更新会以为"已经是最新"。流水线会核对 tag 和 version 是否一致，不一致会报警告。
2. （可选）本地先看一眼包干不干净：
   ```sh
   python tools/package.py --with-tools   # 出 dist/ 两个 zip
   python tools/check_package.py          # 检查没混进隐私/调试文件、必需内容齐全
   python tools/check_version.py v0.1.1   # 核对 tag 和 version
   ```
3. **提交 + 推送**（网络抽风的话它自己重试）：
   ```sh
   python tools/push.py -m "chore: release v0.1.1"
   ```
   或者双击「推送更新.bat」。
4. **打 tag 并推上去**（这一步会触发发布流水线）：
   ```sh
   git tag v0.1.1
   git push origin v0.1.1
   ```
5. 等一两分钟，Release 就自动出现在
   `https://github.com/<你的用户名>/<仓库>/releases` —— 两个 zip 已经挂好了。

**Release 说明**（正文）用的是 `.github/RELEASE_NOTES.md`，想改说明就改那个文件。

> ⚠️ Python 的 `maafw` 版本、以及 `.github/workflows/` 里那两个流水线：
> `check.yml` 在每次改动 assets/agent/tools 时跑项目自己的自检（schema、引用、缺图、
> 打包内容），`release.yml` 管发布。模板原来带的 `install.yml` / `mirrorchyan_*.yml` /
> `sync_schema_files.yml` 已经删掉了 —— 那几个是 MaaXYZ 模板和官方镜像服务用的，
> 在这个项目里每次推送都失败，纯噪音。

---

## 别人怎么用

**方式一：直接下载（简单）**
下载 Release 里的 `bh2-maa-<版本>.zip`，解压得到 `interface.json` / `resource/` / `agent/`，
放进 MFAAvalonia 的资源目录（或本地任何位置，用 GUI 里指定资源路径）。

**方式二：用 GitHub 源更新（推荐）**
1. MFAAvalonia 里把这个仓库的 zip 或目录作为资源加进去；
2. 之后点「更新资源」，它会读 `interface.json` 的 `github` 字段去比对 `version`，
   有新版本就自动拉。

**方式三：从源码自己构建（开发用）**
```sh
git clone https://github.com/<你的用户名>/bh2-maa.git
cd bh2-maa
python tools/install.py            # 装 MaaFramework 到 deps/
python tools/get_gui.py            # 下 MFAAvalonia 并组装出 gui/
gui/MFAAvalonia.exe                # 双击就能用
```
⚠️ Python 那边的 `maafw` 版本**必须和 GUI 自带的 MaaFramework 一致**（现在是 `5.13.0`），
不一致会卡在「正在启动 Agent」：
```sh
python -m pip install maafw==5.13.0
```

---

## 发版检查清单

- [ ] `interface.json` 的 `github` 指向自己的仓库（**不是 MaaXYZ 模板**）
- [ ] `version` 已经加过了
- [ ] **模板图里没有个人隐私**：头像 / 昵称 / 玩家 ID / 等级 / 体力数值。
      踩过：原来 `通用/主界面.png` 裁的就是玩家信息板（含头像），既不通用又泄露信息，
      现在换成了左侧侧边栏图标。
- [ ] `debug/`、`config/`、`assets/resource/image/_raw/` 没进 git（`.gitignore` 里已排除；
      `tools/package.py` 打资源包时也会跳过 `_raw`）
- [ ] `python tools/package.py` 打出来的包里没有 `_raw` / `debug` / `config`
