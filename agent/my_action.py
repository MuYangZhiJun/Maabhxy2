"""崩坏学园2 自定义动作。

这里的东西全部跑在 agent 进程里（interface.json 的 "agent" 字段拉起），
不需要任何模板图，所以即使一张截图都还没采集，auto_battle 也能直接用。

坐标全部按 1280x720 横屏，实际点位在 agent/battle_config.json 里改。
崩崩是横版动作：左手摇杆走位 + 右手武器键输出，所以「边走边打」= 不停点攻击键，
中间穿插几次摇杆拖动。加随机抖动是为了别点得太机械。
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

_DEFAULT_CONFIG = {
    "duration": 60,
    "attack_button": [1150, 600],
    "attack_jitter": 14,
    "click_interval": 0.28,
    "joystick_center": [200, 590],
    "walk_left_offset": -260,
    "walk_right_offset": 260,
    "walk_duration_ms": 380,
    "walk_hold_ms": 700,
    "swipe_every": 4,
    "pause_every": 12,
    "pause_seconds": [0.4, 1.1],
    "fail_limit": 5,
}


def _load_battle_config():
    """读 battle_config.json；坏了就退回内置默认值，不让整条流水线崩掉。"""
    cfg = dict(_DEFAULT_CONFIG)
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            user = json.load(f)
        if isinstance(user, dict):
            cfg.update(user)
    except FileNotFoundError:
        print("[battle] 没找到 battle_config.json，使用内置默认坐标")
    except Exception as exc:  # noqa: BLE001
        print(f"[battle] battle_config.json 读取失败（用默认值继续）: {exc}")
    return cfg


def _params(argv):
    raw = getattr(argv, "custom_action_param", None) or "{}"
    try:
        data = json.loads(raw)
    except Exception:  # noqa: BLE001
        print(f"[battle] custom_action_param 不是合法 JSON，忽略: {raw!r}")
        return {}
    return data if isinstance(data, dict) else {}


def _jitter(point, radius):
    return (
        int(point[0]) + random.randint(-radius, radius),
        int(point[1]) + random.randint(-radius, radius),
    )


@AgentServer.custom_action("auto_battle")
class AutoBattleAction(CustomAction):
    """在战斗中持续输出，持续 duration 秒后交还控制权。

    custom_action_param 可以只写 {"duration": 90} —— 缺的字段由
    battle_config.json 和内置默认值补齐，所以界面上的「战斗时长」选项
    只覆盖时长，不会把坐标一起冲掉。
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        param = _params(argv)
        cfg = _load_battle_config()

        duration = float(param.get("duration", cfg.get("duration", 60)))
        attack = param.get("attack_button", cfg["attack_button"])
        joystick = param.get("joystick_center", cfg["joystick_center"])
        jitter = int(cfg.get("attack_jitter", 14))
        interval = float(cfg.get("click_interval", 0.28))
        swipe_every = max(1, int(cfg.get("swipe_every", 4)))
        pause_every = max(1, int(cfg.get("pause_every", 12)))
        pause_range = cfg.get("pause_seconds", [0.4, 1.1])
        fail_limit = int(cfg.get("fail_limit", 5))

        tasker = getattr(context, "tasker", None)
        controller = getattr(tasker, "controller", None)
        if controller is None:
            print("[battle] 拿不到 controller，自动战斗取消")
            return False

        can_swipe = hasattr(controller, "post_swipe")
        if not can_swipe:
            print("[battle] 当前 maa 版本没有 post_swipe，退化为「只点攻击键、不走位」")

        print(f"[battle] 开始自动战斗：{duration:.0f} 秒，攻击键 {attack}，走位 {'开' if can_swipe else '关'}")
        deadline = time.monotonic() + duration
        clicks = 0
        failures = 0

        while time.monotonic() < deadline:
            try:
                controller.post_click(*_jitter(attack, jitter)).wait()
                clicks += 1
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"[battle] 点击失败({failures}/{fail_limit}): {exc}")
                if failures >= fail_limit:
                    print("[battle] 连续失败太多，提前收工")
                    return False
                time.sleep(0.5)
                continue

            if can_swipe and clicks % swipe_every == 0:
                self._walk(controller, joystick, cfg)

            if clicks % pause_every == 0:
                lo, hi = (pause_range + [0.4, 1.1])[:2]
                time.sleep(random.uniform(float(lo), float(hi)))

            time.sleep(interval)

        print(f"[battle] 自动战斗结束，共点击 {clicks} 次")
        return True

    def _walk(self, controller, joystick, cfg):
        """拖一下摇杆走位：随机选左右，从摇杆中心往外拖。"""
        direction = random.choice(["left", "right"])
        offset = int(cfg.get("walk_left_offset", -260) if direction == "left" else cfg.get("walk_right_offset", 260))
        duration_ms = int(cfg.get("walk_duration_ms", 380))
        hold_ms = int(cfg.get("walk_hold_ms", 700))
        y = int(joystick[1]) + random.randint(-30, 30)
        try:
            controller.post_swipe(int(joystick[0]), y, int(joystick[0]) + offset, y, duration_ms).wait()
            time.sleep(hold_ms / 1000.0)
        except Exception as exc:  # noqa: BLE001
            print(f"[battle] 走位滑动失败（忽略，继续打）: {exc}")


@AgentServer.custom_action("click_target")
class ClickTargetAction(CustomAction):
    """点一个固定坐标，param: {"target": [x, y]}。"""

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        param = _params(argv)
        target = param.get("target")
        if not isinstance(target, list) or len(target) != 2:
            print("[click_target] target 必须是 [x, y]")
            return False
        controller = getattr(getattr(context, "tasker", None), "controller", None)
        if controller is None:
            return False
        try:
            controller.post_click(int(target[0]), int(target[1])).wait()
        except Exception as exc:  # noqa: BLE001
            print(f"[click_target] 点击失败: {exc}")
            return False
        return True


@AgentServer.custom_action("human_swipe")
class HumanSwipeAction(CustomAction):
    """随机化滑动，param: {"begin": [x,y], "end": [x,y], "duration_ms": 400, "jitter": 12}。"""

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        param = _params(argv)
        begin = param.get("begin")
        end = param.get("end")
        if not (isinstance(begin, list) and isinstance(end, list)):
            print("[human_swipe] 需要 begin 和 end，都是 [x, y]")
            return False
        jitter = int(param.get("jitter", 12))
        duration_ms = int(param.get("duration_ms", 400))
        controller = getattr(getattr(context, "tasker", None), "controller", None)
        if controller is None or not hasattr(controller, "post_swipe"):
            return False
        try:
            controller.post_swipe(
                *_jitter(begin, jitter), *_jitter(end, jitter), duration_ms
            ).wait()
        except Exception as exc:  # noqa: BLE001
            print(f"[human_swipe] 滑动失败: {exc}")
            return False
        return True
