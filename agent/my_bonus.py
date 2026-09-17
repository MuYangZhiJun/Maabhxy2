# -*- coding: utf-8 -*-
"""活动 BONUS：一个动作负责「刷 N 轮」的全部事。

为什么循环写在 agent 里而不是 pipeline 里：
  pipeline 的节点是静态的，`max_hit` 在这个框架版本又不可用（见 README），
  想在 pipeline 里表达「刷 N 次」就只能预生成一堆轮次节点 + 用 enabled 挑前几轮，
  那样用户只能从固定档位里选。搬进 agent 后，轮数就是用户填多少是多少。

一轮 = 打 -> 结算 -> （还有下一轮的话）再次挑战 -> 选好友 -> 开战。
中途体力不够的处理：
  点「再次挑战」（体力不足时它是红的，点了会弹窗）
    -> 弹「兑换双倍体力」-> 点兑换，继续刷（免费的双倍体力，默认就用）
    -> 弹「补充体力」   -> 看 use_crystal，勾了才点购买，没勾就收工
    -> 什么窗都没有     -> 说明真没体力了，点确定收工
"""
import json
import os
import random
import time

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction

_HERE = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = os.path.join(_HERE, "battle_config.json")
_DEBUG_DIR = os.path.join(os.path.dirname(_HERE), "debug")

_SCRATCH = "_内部_模板识别"

_DEFAULTS = {
    "duration": 150,
    "auto_fight": True,
    "rounds": 1,
    "use_crystal": False,
    "weapon_button": [997, 635],
    "joystick_center": [200, 590],
    "move_right_offset": 300,
    "click_interval": 0.22,
    "weapon_jitter": 10,
    # ⚠️ 检查间隔别太密：一次 screencap 实测 ~350ms，加上模板匹配就 ~0.5 秒。
    # 3 秒一轮的话，打完那一刻最多要等 3 秒才发现；1.5 秒更跟手（代价是每秒多截一次图）。
    "check_every": 1.5,
    "rechallenge_button": [638, 613],
    "support_slot": [462, 264],
    "support_template": "日常/选择助战好友.png",
    "support_roi": [400, 600, 700, 120],
    "backup_template": "日常/助战_备用装备.png",
    "backup_roi": [200, 150, 900, 400],
    "backup_offset": [46, 28],
    "start_button": [879, 659],
    "settle_confirm": [797, 611],
    # 「战斗到底进没进去」靠开战按钮本身判断 —— 它还在，就说明人还杵在助战页上。
    # roi 跟 pipeline 里 `日常_活动BONUS_开战` 用的一致（实测命中 (778,632,202,54)）。
    "prep_template": "日常/开战.png",
    "prep_roi": [600, 580, 600, 140],
    # 游戏自己的「网络连接中...」提示（截的是文字部分，不带转圈图标）。
    # 实测 1.0000 @(428,302)，稳。出现就停下等，别继续瞎点。
    "net_template": "通用/网络连接中.png",
    "net_roi": [380, 260, 520, 220],
    "net_wait": 5.0,
    # 卡在助战页时兜底点的通用「确定」（网络异常/体力不足之类的弹窗）。
    # ⚠️ 只在**确认还在助战页**时才点，不然战斗中乱点确定可能把战斗点到暂停。
    "dialog_template": "通用/确定.png",
    "dialog_roi": [320, 240, 640, 340],
    "reentry_limit": 3,
    "fail_shot_limit": 3,
    # ---- 选助战（`bonus_pick_support`）----
    # 「选择助战好友」点下去之后好友列表**可能要 5~10 秒才出来**，原来只等 3.5 秒
    # → 认不到就掉兜底 → 什么都没打成（用户报「卡在关卡 BONUS 界面」就是这个）。
    "ready_template": "日常/备用装备加成.png",
    "ready_roi": [400, 350, 500, 100],
    "support_tries": 4,
    "support_polls": 5,
    "support_wait": 2.5,
    # ⚠️ 「选择助战好友」阈值必须 0.95：体力不够时按钮变成「补充体力」，
    # 而那张模板在错页面上还有 0.9376 分（0.85 就误判，实测踩过）
    "support_threshold": 0.95,
    # ---- BONUS 关入口 ----
    # 金色「BONUS」标签是全屏唯一的锚点（每张截图都 1.0000，第 1/2 页上没有它）。
    "badge_template": "日常/活动_BONUS.png",
    "badge_roi": [130, 100, 1150, 620],
    # 详情页判定：详情页顶部那个「BONUS」标题 + 底部的「选择助战好友」。
    # ⚠️ 两个都认，是因为别的关卡详情页也有「选择助战好友」——只认它就分不出
    #    自己是不是点进了 BONUS 关（点歪进错关的代价是白刷一场）。
    "entry_title_template": "日常/BONUS详情标题.png",
    "entry_title_roi": [400, 80, 700, 120],
    "entry_support_template": "日常/选择助战好友.png",
    "entry_support_roi": [400, 600, 700, 120],
    # 候选偏移（相对 BONUS 标签框中心）。第一个是实测正确的；
    # 后面几个是「标签还在但关卡节点挪了」时的兜底，每个都会**验证**过才算数。
    "entry_offsets": [
        [20, 38],
        [30, 48],
        [10, 28],
        [30, 28],
        [10, 48],
        [0, 38],
        [40, 38],
        [20, 58],
        [20, 18]
    ],
    "entry_wait": 1.8,
    # 「首页」「战斗」两个导航的点击点（幂等：点错也只是切个分区）
    "nav_home": [656, 60],
    "nav_battle": [785, 60],
    # 「往上一层」= 点右上角的活动标题（用户 2026-09-17 指正：不用先回首页再切回来，
    # 游戏会记住上次离开的界面，**直接点标题**就行）
    "up_button": [1150, 165],
    "up_tries": 3,
    # 「我在不在主界面」的判据：顶部导航栏里**亮起的首页图标**（选中态实心高亮）。
    # 实测主界面 0.91~1.00、子页 0.68~0.69 → 阈值 0.80。⚠️ roi 跟着模板走（模板在 (605,35)）。
    "home_template": "通用/主界面.png",
    "home_roi": [560, 10, 180, 110],
    "home_threshold": 0.80,
    # 活动页的翻页箭头（1/2 ↔ 2/2，BONUS 标签只在其中一页上）
    "pager_template": "日常/活动_翻页.png",
    "pager_roi": [660, 610, 300, 110],
    "pager_button": [742, 664],
    # ---- 开场弹窗 / 卡死兜底 ----
    # 「回归赠礼」那类全屏活动页**没有出口**：导航栏是死的、返回键没反应、
    # 点页面里任何位置画面都不动（实测 16 个候选点全无反应）——
    # 唯一的出路是**重启游戏**。所以这里配了包名和一键重启。
    "package": "com.miHoYo.HSoDv2Original",
    "relaunch_wait": 25.0,
    # 「回归赠礼」死胡同页的标题（和 pipeline 的 `日常_卡死_回归赠礼` 用同一张图）。
    # ⚠️ 为什么要写进 agent：`bonus_enter` 自己也会点「首页/战斗/右上角活动名」，
    # 这些点击**有可能把这页点出来**（主界面右上角那块就是回归赠礼横幅）——
    # 实测 18:39 那次 `bonus_entry_fail` 的现场图正是这一页。所以它也要会自救。
    "trap_template": "日常/回归赠礼.png",
    "trap_roi": [400, 100, 700, 160],
    # 活动列表页的判据：这两张在列表页上都是 1.0000，在活动地图页上没有
    "act_card_templates": ["日常/活动_难度B.png", "日常/活动_剩余时间.png"],
    "act_card_roi": [130, 100, 1150, 620],
    "settle_template": "日常/战斗结算.png",
    "settle_roi": [400, 80, 600, 90],
    # ⚠️ 结算页要多认几个标志（2026-09-16 踩：那次战斗结算页**画面卡住/只渲染了一半**，
    #    `日常/战斗结算.png` 只打到 **0.8094**（正常 0.9928）→ 认不到 → 白白点满 150 秒，
    #    外面看就是「战斗结束后卡住不动」）。但同一张卡住的画面上
    #    `日常/再次挑战.png` 是 0.9030、`日常/结算确定.png` 是 0.9830 —— 都还在！
    #    所以"这一把打完了"用**任一命中**来判断，别只押在一个模板上。
    "settle_markers": [
        ["日常/战斗结算.png", [400, 80, 600, 90], 0.78],
        ["日常/再次挑战.png", [400, 540, 500, 140], 0.85],
        ["日常/结算确定.png", [500, 480, 600, 240], 0.85]
    ],
    "rechallenge_template": "日常/再次挑战.png",
    "rechallenge_roi": [400, 540, 500, 140],
    "double_template": "日常/兑换双倍体力.png",
    "double_roi": [300, 150, 700, 400],
    "double_offset": [-168, 199],
    "crystal_template": "日常/补充体力.png",
    "crystal_roi": [300, 150, 700, 400],
    "crystal_offset": [-111, 200],
    "crystal_cancel_offset": [109, 199],
    "threshold": 0.85,
}


def _cfg(overrides=None):
    cfg = dict(_DEFAULTS)
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            user = json.load(f)
        section = user.get("bonus_battle") if isinstance(user, dict) else None
        if isinstance(section, dict):
            cfg.update({k: v for k, v in section.items() if not k.startswith("//")})
    except FileNotFoundError:
        pass
    except Exception as exc:  # noqa: BLE001
        print(f"[bonus] battle_config.json 读取失败（用默认值）: {exc}")
    if overrides:
        cfg.update(overrides)
    return cfg


def _jitter(point, radius):
    return (int(point[0]) + random.randint(-radius, radius),
            int(point[1]) + random.randint(-radius, radius))


class _Ctl:
    """包一层 controller，把「截图 + 认模板」和「点一下」都收拢。"""

    def __init__(self, context, cfg):
        self.context = context
        self.cfg = cfg
        self.controller = getattr(getattr(context, "tasker", None), "controller", None)

    @property
    def ok(self):
        return self.controller is not None

    def click(self, point, wait=0.0, label=""):
        try:
            self.controller.post_click(int(point[0]), int(point[1])).wait()
            if label:
                print(f"[bonus]   点「{label}」{point}")
        except Exception as exc:  # noqa: BLE001
            print(f"[bonus]   点「{label}」失败: {exc}")
            return False
        if wait:
            time.sleep(wait)
        return True

    def find(self, template, roi, threshold=None):
        """截一张图认模板，命中返回 box [x,y,w,h]，否则 None。"""
        try:
            image = self.controller.post_screencap().wait().get()
        except Exception as exc:  # noqa: BLE001
            print(f"[bonus]   截图失败: {exc}")
            return None
        if image is None:
            return None
        detail = self.context.run_recognition(
            _SCRATCH, image,
            pipeline_override={_SCRATCH: {
                "recognition": "TemplateMatch",
                "template": template,
                "roi": roi,
                "threshold": self.cfg["threshold"] if threshold is None else float(threshold),
            }},
        )
        box = getattr(detail, "box", None) if detail is not None else None
        if box is None:
            return None
        try:
            return [int(v) for v in box]
        except (TypeError, ValueError):
            return None

    def has(self, template, roi):
        return self.find(template, roi) is not None

    def click_offset(self, box, offset, wait=0.0, label=""):
        point = (box[0] + offset[0] + box[2] // 2, box[1] + offset[1] + box[3] // 2)
        return self.click(point, wait, label)

    def save_shot(self, tag="shot"):
        """把当前画面存到 debug/ 下，卡住的时候留个证据。

        为什么非要存：agent 是**盲**的 —— 卡住时它只知道"没认到结算"，
        说不出屏幕上到底是什么。存一张下来，事后 `tools/what_is_this.py`
        一扫就知道当时停在哪一屏（模板反查，不需要 OCR）。
        """
        try:
            image = self.controller.post_screencap().wait().get()
        except Exception as exc:  # noqa: BLE001
            print(f"[bonus]   存截图失败（截不到）: {exc}")
            return None
        if image is None:
            return None
        try:
            import cv2
            os.makedirs(_DEBUG_DIR, exist_ok=True)
            path = os.path.join(_DEBUG_DIR, f"{tag}_{time.strftime('%m%d_%H%M%S')}.png")
            cv2.imwrite(path, image)
            print(f"[bonus]   卡住时的画面已存: {path}")
            return path
        except Exception as exc:  # noqa: BLE001
            print(f"[bonus]   存截图失败（写盘）: {exc}")
            return None


def _settled(ctl, cfg):
    """这一把打完了吗？**任一结算标志命中**就算（别只认一个模板）。

    为什么：实测碰到过结算页**画面卡住/只渲染一半**的情况，`战斗结算.png` 掉到 0.8094
    （阈值 0.85 过不去），但同一屏上的「再次挑战」「结算确定」都还是好分数。
    只认一个模板的话，就会在已经打完的结算页上白点 150 秒 —— 外面看是「战斗结束后卡住」。
    """
    for item in cfg["settle_markers"]:
        name, roi, thr = item[0], item[1], float(item[2])
        if ctl.find(name, roi, threshold=thr):
            return True
    return False


def _fight(ctl, cfg, duration):
    """打一轮：按住摇杆往右 + 连点一号位武器（auto_fight 关掉就纯挂机），认到结算就停。

    每 check_every 秒会看一眼屏幕，按优先级判断：
      1. **战斗结算**  → 打完了，收工
      2. **网络遮罩**（「网络连接中」那种）→ 说明卡在网络上，**停下来等**，别继续瞎点；
         等待不计入时间上限（deadline 往后推）
      3. **人还在助战页**（开战按钮还认得到）→ 战斗根本没进去（网络异常、弹窗吃掉点击…）：
         先关掉挡路的弹窗，再重新点「开战」，最多 reentry_limit 次；用完就直接收工，
         不陪它耗满 duration
    实在打不完就把那一刻的截图存到 debug/，方便事后看卡在哪。

    ⚠️ 「人还在助战页」这个判断**必须连续两次都命中才算数**：开战→战斗loading 那一瞬间
    开战按钮可能还在画面上，单次命中就重新点会把已经进战斗的局点乱。
    """
    c = ctl.controller
    auto = bool(cfg["auto_fight"])
    weapon = cfg["weapon_button"]
    joy = cfg["joystick_center"]
    offset = int(cfg["move_right_offset"])
    interval = float(cfg["click_interval"])
    jitter = int(cfg["weapon_jitter"])
    check_every = float(cfg["check_every"])

    deadline = time.monotonic() + float(duration)
    next_check = time.monotonic() + check_every
    clicks = 0
    fails = 0
    holding = False
    waits = 0
    reentry = 0
    prep_seen = 0
    started = False
    shots = 0

    try:
        while time.monotonic() < deadline:
            if auto and not holding and hasattr(c, "post_touch_down"):
                try:
                    c.post_touch_down(int(joy[0]), int(joy[1])).wait()
                    c.post_touch_move(int(joy[0]) + offset, int(joy[1])).wait()
                    holding = True
                except Exception as exc:  # noqa: BLE001
                    print(f"[bonus]   按住摇杆失败（改为只砍不走了）: {exc}")
                    offset = 0

            if auto:
                try:
                    c.post_click(*_jitter(weapon, jitter)).wait()
                    clicks += 1
                    fails = 0
                except Exception as exc:  # noqa: BLE001
                    fails += 1
                    print(f"[bonus]   点击失败({fails}): {exc}")
                    if fails >= 5:
                        print("[bonus]   连续点不动，收工")
                        return False
                    time.sleep(0.4)

            time.sleep(interval)

            if time.monotonic() >= next_check:
                next_check = time.monotonic() + check_every

                if _settled(ctl, cfg):
                    print(f"[bonus]   认到战斗结算（点了 {clicks} 次）")
                    return True

                # 网络遮罩：停下等，别继续点（点了也没用，还可能点到别的东西）
                if ctl.has(cfg["net_template"], cfg["net_roi"]):
                    waits += 1
                    print(f"[bonus]   屏幕上「网络连接中」—— 第 {waits} 次等它自己好"
                          f"（这 {cfg['net_wait']} 秒不点屏幕，时间上限往后推）")
                    time.sleep(float(cfg["net_wait"]))
                    deadline += float(cfg["net_wait"])
                    # 等完再认一次结算：网络恢复后可能直接就到结算页了
                    if _settled(ctl, cfg):
                        print(f"[bonus]   网络恢复后认到战斗结算（点了 {clicks} 次）")
                        return True
                    continue

                # 战斗到底进没进去？看开战按钮还在不在。连续两次命中才算「还在助战页」。
                if not started and ctl.has(cfg["prep_template"], cfg["prep_roi"]):
                    prep_seen += 1
                    if prep_seen < 2:
                        continue
                    # 到这儿说明点了开战、等了 3 秒以上，人还杵在助战页上
                    if reentry >= cfg["reentry_limit"]:
                        print(f"[bonus]   点了 {reentry} 次开战都进不去，别耗了，收工")
                        break
                    # 先看有没有弹窗挡路（网络异常/体力不足之类），有就点掉再重试
                    box = ctl.find(cfg["dialog_template"], cfg["dialog_roi"])
                    if box:
                        shots += _dump(ctl, cfg, shots, "bonus_blocked")
                        ctl.click_offset(box, [0, 0], 3.0, "弹窗确定")
                        deadline += 3.0
                        continue
                    reentry += 1
                    print(f"[bonus]   开战没生效（人还在助战页）—— 第 {reentry} 次重新点开战")
                    ctl.click(cfg["start_button"], 4.0, "开战(重试)")
                    deadline += 4.0
                    prep_seen = 0
                    continue
                if not started:
                    started = True
    finally:
        if holding:
            try:
                c.post_touch_up().wait()
            except Exception:  # noqa: BLE001
                pass

    print(f"[bonus]   到时间上限还没结算（点了 {clicks} 次，"
          f"网络等待 {waits} 次，重进战斗 {reentry} 次，"
          f"{'人一直在助战页没进去' if not started else '进过战斗'}）")
    _dump(ctl, cfg, shots, "bonus_fail")
    return False


def _dump(ctl, cfg, shots, tag):
    """存一张现场截图（有个数上限，别把 debug/ 塞爆）。返回新的张数。"""
    if shots >= int(cfg.get("fail_shot_limit", 3)):
        return shots
    if ctl.save_shot(tag):
        return shots + 1
    return shots


def _wait_net(ctl, cfg, tries=6):
    """屏幕上还挂着「网络连接中」就等它自己走。返回等了几次。

    为什么到处都要调它：这游戏的网络提示是**随时**冒出来的，不只是战斗中 ——
    点完「再次挑战」、点完「开战」都可能卡在这儿。卡着的时候点什么都白点，
    而且弹窗是模态的，后面所有点击都会被它吃掉。
    """
    n = 0
    while n < tries and ctl.has(cfg["net_template"], cfg["net_roi"]):
        n += 1
        print(f"[bonus]   「网络连接中」—— 等它自己好（第 {n} 次，"
              f"每次 {cfg['net_wait']} 秒）")
        time.sleep(float(cfg["net_wait"]))
    return n


def _next_round(ctl, cfg, use_crystal):
    """结算页 -> 开好下一轮。返回 False 表示刷不下去了。"""
    # ⚠️ 「再次挑战」体力不足时会变红，而模板是正常态的，所以**红色的认不出来**。
    # 认不到不代表该收工 —— 红色按钮位置一样，点了照样弹体力窗。
    # 所以这里不拿"认不认得到"当门槛，直接点一下，再看弹出来的是哪个窗。
    # （以前这里是 `if not has(...): return False`，等于把下面那套体力窗处理全废掉了，
    #   免费的双倍体力永远用不上。）
    if ctl.has(cfg["rechallenge_template"], cfg["rechallenge_roi"]):
        print("[bonus]   认到「再次挑战」（体力够）")
    else:
        print("[bonus]   没认到「再次挑战」—— 多半是红的（体力不够），照样点一下看弹什么")

    ctl.click(cfg["rechallenge_button"], 3.0, "再次挑战")
    _wait_net(ctl, cfg, tries=3)

    # 点完之后可能弹体力窗，也可能直接进好友列表
    box = ctl.find(cfg["double_template"], cfg["double_roi"])
    if box:
        print("[bonus]   弹的是「兑换双倍体力」，换掉存的双倍体力继续")
        ctl.click_offset(box, cfg["double_offset"], 3.0, "兑换")
    else:
        box = ctl.find(cfg["crystal_template"], cfg["crystal_roi"])
        if box:
            if not use_crystal:
                # ⚠️ 一定要点「取消」把窗关掉再收工。这是个模态窗，
                # 留着不清，后面 收尾 点导航栏会被它挡住，任务会"成功"结束
                # 但游戏卡在弹窗里出不来（实测踩过）。
                print("[bonus]   弹的是「补充体力」（要花水晶），没勾「用水晶补体力」"
                      "—— 点取消关掉窗再收工")
                ctl.click_offset(box, cfg["crystal_cancel_offset"], 2.0, "取消")
                return False
            print("[bonus]   弹的是「补充体力」，买体力继续")
            ctl.click_offset(box, cfg["crystal_offset"], 3.0, "购买")
        else:
            # ⚠️ 这里原来判的是「还认得到『选择助战好友』按钮吗」—— **判错了**：
            # 那个按钮是**详情页**上的，好友列表上根本没有它。于是明明已经进了
            # 好友列表，也会被判成"没进好友列表"直接收工（实测踩过：结算完点
            # 「再次挑战」明明进了列表，日志却写"没进好友列表，收工"，
            # 存下来的现场图上 `助战_备用装备.png` 是 1.0000）。
            # 正确的判据是"**既不在详情页、也不在结算页**"→ 那只可能是好友列表。
            _wait_net(ctl, cfg, tries=3)
            on_detail = _on_bonus_detail(ctl, cfg)
            on_settle = _settled(ctl, cfg)
            backup = ctl.find(cfg["backup_template"], cfg["backup_roi"])
            if on_detail and not backup:
                print("[bonus]   点了「再次挑战」但还停在详情页上，收工")
                _dump(ctl, cfg, 0, "bonus_next_round")
                return False
            if on_settle and not backup:
                print("[bonus]   点了「再次挑战」但还停在结算页上，收工")
                _dump(ctl, cfg, 0, "bonus_next_round")
                return False
            if backup:
                print("[bonus]   到好友列表了（认到「备用装备」那一格）")
            else:
                print("[bonus]   离开结算页了、也没认到弹窗 —— 按好友列表继续")

    # 选助战：**优先按内容认出「备用装备」那一格再点**（关卡战斗默认选的就是它，
    # 是玩家自己的备用装备，不依赖好友在线），认不到才回退到固定坐标 ——
    # 固定坐标等于假设"好友列表第一格永远是备用装备"，排序一变就选到别人。
    backup = ctl.find(cfg["backup_template"], cfg["backup_roi"])
    if backup:
        ctl.click_offset(backup, cfg["backup_offset"], 3.0, "选备用装备")
    else:
        print("[bonus]   没认到「备用装备」那一格，按固定坐标点第一格")
        ctl.click(cfg["support_slot"], 3.0, "选好友")
    ctl.click(cfg["start_button"], 4.5, "开战")
    return True


def _finish(ctl, cfg):
    """收工：先关掉可能还开着的体力窗（模态窗会挡住后面的导航点击），再点结算页「确定」。"""
    _wait_net(ctl, cfg, tries=4)
    box = ctl.find(cfg["crystal_template"], cfg["crystal_roi"])
    if box:
        print("[bonus]   收工前发现「补充体力」窗还开着，先点取消")
        ctl.click_offset(box, cfg["crystal_cancel_offset"], 1.5, "取消")
    ctl.click(cfg["settle_confirm"], 2.5, "确定")


def _on_bonus_detail(ctl, cfg):
    """现在这一屏是不是「BONUS 关详情页」？

    两个条件都要：顶部有「BONUS」标题 + 底部有「选择助战好友」。
    只认后者的话，点歪进了别的关卡也会被当成成功。
    """
    return (ctl.has(cfg["entry_title_template"], cfg["entry_title_roi"])
            and ctl.has(cfg["entry_support_template"], cfg["entry_support_roi"]))


@AgentServer.custom_action("bonus_enter")
class BonusEnterAction(CustomAction):
    """把「走到 BONUS 关详情页」这件事从头做完 —— **认内容，不认固定位置**。

    为什么必须是"认内容 + 每步验证"：
      pipeline 里原来是「认 BONUS 标签 → 按死偏移点一下」，两个毛病都踩过：
      1) 偏移写错（`[-4,78]` 落到 (230,338)，实测是**点空**的）→ 点不进去，
         而点空是**静默**的，链子安静地掉到「收尾」，表现就是「关卡战斗被跳过」；
      2) 就算偏移对，入口也受页面状态影响，所以每一步都得**验证**再往下走。

    从哪一页进来都能用：
      · 已在 BONUS 详情页（认到顶部 BONUS 标题 + 选择助战好友）→ 直接返回
      · 在活动地图页（认得到金色 BONUS 标签）→ 按候选偏移点入口，点完验证
      · 在活动列表页（认得到「难度指数」「剩余时间」）→ 点活动卡片进去，再找标签
      · 都不认识 → 点「首页」+「战斗」导航（幂等，点错也只是切个分区），再看一遍

    返回 True 永远为 True：没成功也别把任务判失败，交给后面的
    `翻页`/`收尾` 收场，同时会把现场存成 debug/bonus_entry_fail_*.png 留证据。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        raw = getattr(argv, "custom_action_param", None)
        overrides = {}
        if raw:
            try:
                overrides = json.loads(raw) or {}
            except Exception:  # noqa: BLE001
                print(f"[bonus] param 不是合法 JSON，忽略: {raw!r}")

        cfg = _cfg(overrides)
        ctl = _Ctl(context, cfg)
        if not ctl.ok:
            print("[bonus] 拿不到 controller，跳过找入口")
            return True

        if self._find_entry(ctl, cfg, "开局就在"):
            return True
        if self._trap(ctl, cfg, "开局就在"):
            return True

        # 在活动列表页 → 点活动卡片进去
        if self._click_activity_card(ctl, cfg):
            if self._find_entry(ctl, cfg, "点完活动卡片"):
                return True

        # ⚠️ 2026-09-17 用户指正：「首页 → 战斗」那一步**是多余的** ——
        # 游戏会记住上次离开的界面，**直接点右上角那个活动标题往上层翻**就行。
        # 但主界面上点右上角那个坐标会点到**「回归赠礼」横幅**（全屏死胡同、进得去出不来，实测踩过两次），
        # 所以分成两种情况：
        #   · 在主界面上（认「亮起的首页图标」）→ 点一次「战斗」进分区（游戏会自己回到上次那个活动页）
        #   · 已经不在主界面 → 直接点右上角标题往上翻
        if self._on_home(ctl, cfg):
            print("[bonus] 在主界面上 —— 点一次「战斗」进分区（游戏会回到上次那个活动页）")
            ctl.click(cfg["nav_battle"], 4.0, "战斗导航")
            if self._find_entry(ctl, cfg, "进战斗分区后"):
                return True
            if self._trap(ctl, cfg, "进战斗分区后"):
                return True
            if self._click_activity_card(ctl, cfg):
                if self._find_entry(ctl, cfg, "进战斗分区并点卡片后"):
                    return True

        # 游戏会记住「战斗」分区上次停在哪个活动子页，所以点「战斗」不一定到得了 BONUS 那个活动页。
        # 这时候靠**点右上角活动标题往上翻**（和 pipeline 里 `开列表` 同一个做法）。
        for i in range(int(cfg["up_tries"])):
            print(f"[bonus] 点右上角标题往上一层（第 {i + 1} 次）")
            ctl.click(cfg["up_button"], 3.0, "右上角标题（往上一层）")
            if self._find_entry(ctl, cfg, f"上翻 {i + 1} 层后"):
                return True
            # 上翻那一下也可能正好点在「回归赠礼」横幅上 —— 那就得重启游戏自救
            if self._trap(ctl, cfg, f"上翻 {i + 1} 层后"):
                return True
            if self._click_activity_card(ctl, cfg):
                if self._find_entry(ctl, cfg, f"上翻 {i + 1} 层并点卡片后"):
                    return True

        print("[bonus] 没能走到 BONUS 关入口，存张图留证据")
        ctl.save_shot("bonus_entry_fail")
        return True

    # ---- 内部小步骤 ----

    @staticmethod
    def _on_home(ctl, cfg):
        """在不在主界面上？认的是**顶部导航栏里亮起的「首页」图标**（选中态是实心高亮）。

        实测：主界面 0.91~1.00、子页（活动列表 / 关卡详情页 / 地图页）0.68~0.69 → 阈值 0.80。
        """
        return ctl.find(cfg["home_template"], cfg["home_roi"],
                        threshold=cfg["home_threshold"]) is not None

    @staticmethod
    def _trap(ctl, cfg, where=""):
        """是不是卡在「回归赠礼」那个死胡同页上了？是就重启游戏。返回 True 表示确实卡住了。

        ⚠️ 为什么这条得写在 agent 里：找入口的过程本身会点「首页/战斗/右上角活动名」，
        而主界面右上角那块正好是**回归赠礼横幅** —— 点中了就进死胡同。
        实测 18:39 那次的 `bonus_entry_fail` 现场图就是这一页，链子只能存图收场。
        """
        if not ctl.has(cfg["trap_template"], cfg["trap_roi"]):
            return False
        print(f"[bonus] {where}发现卡在「回归赠礼」死胡同页上 —— 这页没有出口，重启游戏")
        try:
            ctl.controller.post_stop_app(cfg["package"]).wait()
            time.sleep(3.0)
            ctl.controller.post_start_app(cfg["package"]).wait()
        except Exception as exc:  # noqa: BLE001
            print(f"[bonus] 重启游戏失败: {exc}")
            ctl.save_shot("bonus_trap_relaunch_fail")
            return True
        time.sleep(float(cfg["relaunch_wait"]))
        ctl.save_shot("bonus_trap_relaunched")
        return True

    @staticmethod
    def _on_detail(ctl, cfg):
        """现在这一屏是不是「BONUS 关详情页」？

        两个条件都要：顶部有「BONUS」标题 + 底部有「选择助战好友」。
        只认后者的话，点歪进了别的关卡也会被当成成功。
        """
        return (ctl.has(cfg["entry_title_template"], cfg["entry_title_roi"])
                and ctl.has(cfg["entry_support_template"], cfg["entry_support_roi"]))

    def _find_entry(self, ctl, cfg, where=""):
        """在活动地图页上找 BONUS 标签并点进去。返回 True 表示确实进了详情页。"""
        if self._on_detail(ctl, cfg):
            print(f"[bonus] {where}已经在 BONUS 关详情页上了")
            return True

        box = ctl.find(cfg["badge_template"], cfg["badge_roi"])
        if not box and ctl.has(cfg["pager_template"], cfg["pager_roi"]):
            # 活动页分 1/2 和 2/2，BONUS 标签只在其中一页上 —— 翻一下再找
            print(f"[bonus] {where}这页没有 BONUS 标签，先翻一页看看")
            ctl.click(cfg["pager_button"], 3.0, "翻页")
            box = ctl.find(cfg["badge_template"], cfg["badge_roi"])
        if not box:
            return False
        cx = box[0] + box[2] // 2
        cy = box[1] + box[3] // 2
        print(f"[bonus] {where}认到 BONUS 标签 @({box[0]},{box[1]},{box[2]},{box[3]})，"
              f"中心 ({cx},{cy})")
        for i, off in enumerate(cfg["entry_offsets"]):
            px, py = cx + int(off[0]), cy + int(off[1])
            ctl.click((px, py), float(cfg["entry_wait"]),
                      f"BONUS 入口候选{i + 1}（偏移 {off}）")
            if self._on_detail(ctl, cfg):
                if i == 0:
                    print(f"[bonus] 进 BONUS 详情页了（偏移 {off} 生效）")
                else:
                    print(f"[bonus] ⚠️ 首选偏移 {cfg['entry_offsets'][0]} 这次没生效，"
                          f"是 {off} 点进去的 —— 该把 entry_offsets 的顺序改了")
                return True
        print("[bonus] 所有候选偏移都没点进详情页")
        return False

    @staticmethod
    def _click_activity_card(ctl, cfg):
        """在活动列表页上点活动卡片。返回 True 表示点了。"""
        for name in cfg["act_card_templates"]:
            box = ctl.find(name, cfg["act_card_roi"])
            if box:
                pt = (box[0] + box[2] // 2, box[1] + box[3] // 2)
                print(f"[bonus] 认到活动列表（{name}）→ 点卡片 {pt}")
                ctl.click(pt, 4.0, "活动卡片")
                return True
        return False


@AgentServer.custom_action("bonus_find_entry")
class BonusFindEntryAction(BonusEnterAction):
    """老名字，保留兼容（老 pipeline / 用户手上的旧配置还会调它）。"""


@AgentServer.custom_action("bonus_pick_support")
class BonusPickSupportAction(CustomAction):
    """「选助战好友 → 挑一个助战」这一段，改成**每步验证 + 重试**。

    为什么不能只点一下就算完（2026-09-17 用户报「卡在关卡 BONUS 界面，没去点选择助战好友」）：
    `选择助战好友` 点下去之后，好友列表**有时候要 5~10 秒才出来**（网络慢、页面还在滑），
    而链子原来只等 3.5 秒：认不到 `助战_备用装备` 就掉到兜底坐标乱点一下、再点一次「开战」重试，
    最后什么都没打成 —— 而且**全程不报错**，外面看就是"卡在那儿不动"。

    现在：
      1. 已经在助战确认页（认得到「备用装备加成」）→ 直接过
      2. 还在关卡详情页（认得到「选择助战好友」）→ 点它，然后**轮询等好友列表**（每次 2.5 秒，最多 5 次）
      3. 等到列表 → 优先认「备用装备」那一格再点（认不到才按固定坐标点第一格）
      4. 每一轮都验证「到助战确认页了没」，没到就再来一轮（最多 4 轮）
      5. 全都不行 → 存 `debug/bonus_support_fail_*.png` 留证据
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        raw = getattr(argv, "custom_action_param", None)
        overrides = {}
        if raw:
            try:
                overrides = json.loads(raw) or {}
            except Exception:  # noqa: BLE001
                print(f"[bonus] param 不是合法 JSON，忽略: {raw!r}")
        cfg = _cfg(overrides)
        ctl = _Ctl(context, cfg)
        if not ctl.ok:
            print("[bonus] 拿不到 controller，跳过选助战")
            return True

        def on_ready():
            return ctl.has(cfg["ready_template"], cfg["ready_roi"])

        def on_detail():
            """是不是在关卡详情页上？

            ⚠️ 别拿「选择助战好友」当判据 —— 那行字在**体力不足时会变成「补充体力」**，
            而 `选择助战好友.png` 在那种页面上还有 **0.9376** 分（阈值 0.85 就误判了，
            实测踩过：以为在详情页、点下去其实点的是「补充体力」，弹了花水晶的窗）。
            改用详情页上稳定的两个东西：BONUS 标题 / 使用双倍券。
            """
            return (ctl.has(cfg["entry_title_template"], cfg["entry_title_roi"])
                    or ctl.has(cfg["double_template"], cfg["double_roi"]))

        def crystal_dialog():
            """「补充体力」窗（花水晶补体力）。体力不够时点按钮就会弹它。"""
            return ctl.find(cfg["crystal_template"], cfg["crystal_roi"], threshold=0.95)

        if on_ready():
            print("[bonus] 已经在助战确认页上了，直接过")
            return True

        for attempt in range(1, int(cfg["support_tries"]) + 1):
            print(f"[bonus] 选助战：第 {attempt}/{cfg['support_tries']} 轮")

            # 体力不够时页面底部那个按钮会变成「补充体力」，点它会弹花水晶的窗 ——
            # 我们不该买，看到窗就直接点「取消」收工。
            box = crystal_dialog()
            if box:
                print("[bonus] 页面/弹窗是「补充体力」（体力不够，要花水晶）—— 点取消，收工")
                ctl.click_offset(box, cfg["crystal_cancel_offset"], 2.0, "取消")
                return True

            if not on_ready() and on_detail():
                btn = ctl.find(cfg["entry_support_template"], cfg["entry_support_roi"],
                               threshold=cfg["support_threshold"])
                if btn:
                    pt = (btn[0] + btn[2] // 2, btn[1] + btn[3] // 2)
                    ctl.click(pt, 1.5, "选择助战好友")
                else:
                    print("[bonus] 详情页上认不到「选择助战好友」"
                          "（多半是体力不够、按钮文字改成「补充体力」了）—— 收工")
                    ctl.save_shot("bonus_support_nostamina")
                    return True
            # 轮询等好友列表（这一步是这次修的重点：别只等一次）
            backup = None
            for poll in range(int(cfg["support_polls"])):
                if on_ready():
                    print("[bonus] 到助战确认页了")
                    return True
                backup = ctl.find(cfg["backup_template"], cfg["backup_roi"])
                if backup:
                    break
                time.sleep(float(cfg["support_wait"]))
            if on_ready():
                return True
            if backup:
                ctl.click_offset(backup, cfg["backup_offset"], 3.0, "选备用装备")
            else:
                print("[bonus] 还没等到好友列表 —— 按固定坐标点第一格试试")
                ctl.click(cfg["support_slot"], 3.0, "选好友（兜底坐标）")
            if on_ready():
                print("[bonus] 到助战确认页了")
                return True
        print("[bonus] 选助战试了几轮都没到确认页，存图留证据")
        ctl.save_shot("bonus_support_fail")
        return True


@AgentServer.custom_action("escape_event_trap")
class EscapeEventTrapAction(CustomAction):
    """卡在「回归赠礼」那类全屏活动页时的兜底：**重启游戏**。

    为什么只能重启：那页实测**没有出口** —— 导航栏是死的（点首页/战斗/装备都没反应）、
    系统返回键没反应、页面里点哪都不动（我试了 16 个候选点，画面差异全在噪声级别），
    最后是靠 `am force-stop` + 重新启动才出来的。

    节点上是**用模板门槛**挂的（`日常/回归赠礼.png` @0.85），所以没卡住时它根本不会被调用。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        raw = getattr(argv, "custom_action_param", None)
        overrides = {}
        if raw:
            try:
                overrides = json.loads(raw) or {}
            except Exception:  # noqa: BLE001
                print(f"[escape] param 不是合法 JSON，忽略: {raw!r}")
        cfg = _cfg(overrides)
        ctl = _Ctl(context, cfg)
        if not ctl.ok:
            print("[escape] 拿不到 controller，跳过")
            return True

        pkg = cfg["package"]
        print(f"[escape] 卡在「回归赠礼」全屏页上 —— 这页没有出口，重启游戏（{pkg}）")
        try:
            ctl.controller.post_stop_app(pkg).wait()
        except Exception as exc:  # noqa: BLE001
            print(f"[escape] 关闭游戏失败: {exc}")
        time.sleep(3.0)
        try:
            ctl.controller.post_start_app(pkg).wait()
            print("[escape] 已重新启动，等它起来（后面的节点会等主界面）")
        except Exception as exc:  # noqa: BLE001
            print(f"[escape] 启动游戏失败: {exc}")
            return True
        time.sleep(float(cfg["relaunch_wait"]))
        ctl.save_shot("escape_relaunched")
        return True


@AgentServer.custom_action("bonus_battle")
class BonusBattleAction(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        raw = getattr(argv, "custom_action_param", None)
        overrides = {}
        if raw:
            try:
                overrides = json.loads(raw) or {}
            except Exception:  # noqa: BLE001
                print(f"[bonus] param 不是合法 JSON，忽略: {raw!r}")

        cfg = _cfg(overrides)
        ctl = _Ctl(context, cfg)
        if not ctl.ok:
            print("[bonus] 拿不到 controller，取消")
            return False

        rounds = max(1, int(cfg.get("rounds", 1)))
        use_crystal = bool(cfg.get("use_crystal", False))
        print(f"[bonus] 开刷：{rounds} 轮，{'拖动输出' if cfg['auto_fight'] else '挂机等结算'}，"
              f"水晶补体力 {'开' if use_crystal else '关'}")

        for i in range(rounds):
            print(f"[bonus] === 第 {i + 1}/{rounds} 轮 ===")
            if not _fight(ctl, cfg, cfg["duration"]):
                print("[bonus] 这轮没打出结算，先收工")
                break
            if i == rounds - 1:
                print("[bonus] 最后一轮，点确定收尾")
                _finish(ctl, cfg)
                return True
            if not _next_round(ctl, cfg, use_crystal):
                print("[bonus] 刷不下去了，点确定收尾")
                _finish(ctl, cfg)
                return True

        return True
