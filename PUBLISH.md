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

> **推送用脚本，别手敲 `git push`** —— 这台机器到 GitHub 的连接时通时断，
> 实测推一次要重试 6 次才成功，而 `git push` 自己不会重试。
> ```sh
> python tools/push.py -m "chore: release v0.1.1"     # 提交 + 重试推送 + 校验
> ```
> Windows 上直接双击根目录的 **「推送更新.bat」** 也一样。
> 脚本会确保 `http.version=HTTP/1.1`（HTTP/2 在国内容易被重置）、最多重试 10 次、
> 最后比对远端和本地提交哈希是否一致。

1. **把 `assets/interface.json` 的 `version` 往上加**（比如 `0.1.0` → `0.1.1`）。
   MFAAvalonia 靠这个字段判断"有没有新版本"，不加别人就收不到更新。
2. 跑一遍检查：
   ```sh
   python tools/validate_schema.py     # schema 校验
   python tools/check_env.py           # pipeline 引用 / 缺图
   python tools/get_gui.py --sync-only # 同步进 gui/（本地自测用）
   ```
3. 打包（可选，给不想用更新功能、想直接下 zip 的人）：
   ```sh
   python tools/package.py --with-tools
   ```
   会在 `dist/` 出两个包：
   - `bh2-maa-<版本>.zip` —— **资源包**，MAA 生态通用布局：
     `interface.json` + `resource/`（pipeline + 模板图）+ `agent/`
   - `bh2-maa-<版本>-source.zip` —— 完整源码，含 `tools/`，能自己构建 GUI
4. 提交 + 打 tag + 发 Release：
   ```sh
   git add -A && git commit -m "chore: release v0.1.1"
   git tag v0.1.1 && git push && git push --tags
   ```
   然后在 GitHub 上建 Release，把 `dist/` 里那两个 zip 传上去（可选）。
   **注意：只要仓库本身更新了，用「更新资源」的人就能拿到，Release 只是给想手动下载的人。**

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
