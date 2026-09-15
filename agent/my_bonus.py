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

_SCRATCH = "_内部_模板识别"

_DEFAULTS = {
    "duration": 150,
    "auto_fight": True,
    "rounds": 1,
    "use_crystal": False,
    "weapon_button": [997, 635],
    "joystick_center": [200, 590],
    "move_right_offset": 300,
    "click_interval": 0.16,
    "weapon_jitter": 10,
    "check_every": 3.0,
    "rechallenge_button": [638, 613],
    "support_slot": [462, 264],
    "support_template": "日常/选择助战好友.png",
    "support_roi": [400, 600, 700, 120],
    "backup_template": "日常/助战_备用装备.png",
    "backup_roi": [200, 150, 900, 400],
    "backup_offset": [46, 28],
    "start_button": [879, 659],
    "settle_confirm": [797, 611],
    "settle_template": "日常/战斗结算.png",
    "settle_roi": [400, 80, 600, 90],
    "rechallenge_template": "日常/再次挑战.png",
    "rechallenge_roi": [400, 540, 500, 140],
    "support_template": "日常/选择助战好友.png",
    "support_roi": [400, 600, 700, 120],
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

    def find(self, template, roi):
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
                "threshold": self.cfg["threshold"],
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


def _fight(ctl, cfg, duration):
    """打一轮：按住摇杆往右 + 连点一号位武器（auto_fight 关掉就纯挂机），认到结算就停。"""
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
                if ctl.has(cfg["settle_template"], cfg["settle_roi"]):
                    print(f"[bonus]   认到战斗结算（点了 {clicks} 次）")
                    return True
    finally:
        if holding:
            try:
                c.post_touch_up().wait()
            except Exception:  # noqa: BLE001
                pass

    print(f"[bonus]   到时间上限还没结算（点了 {clicks} 次）")
    return False


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
        elif not ctl.has(cfg["support_template"], cfg["support_roi"]):
            print("[bonus]   没进好友列表，也不认识弹窗，收工")
            return False

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
    box = ctl.find(cfg["crystal_template"], cfg["crystal_roi"])
    if box:
        print("[bonus]   收工前发现「补充体力」窗还开着，先点取消")
        ctl.click_offset(box, cfg["crystal_cancel_offset"], 1.5, "取消")
    ctl.click(cfg["settle_confirm"], 2.5, "确定")


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
