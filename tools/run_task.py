#!/usr/bin/env python3
"""不动 GUI，直接用 MaaFramework 跑一个任务（含 agent）。

为什么需要这个：MFAAvalonia 在我们这台机器上加载资源会失败
（日志里 `IMaaResource failed to load resources. MaaJobStatus cannot be Failed.`），
但同一份资源用 MaaFramework 本体加载是好的 —— 实测 deps/bin/MaaPiCli.exe 能正常
解析 interface.json 并列出任务。所以拿这个脚本当替代品：验证 pipeline、跑日常都行。

它会做四件事：
  1. 从 assets/interface.json 里按任务名找 entry（也支持直接给节点名）
  2. 加载 assets/resource
  3. 连 adb（MuMu 12 默认 127.0.0.1:16384）
  4. 拉起 agent 子进程并连上它（注意必须先 bind(resource) 再 connect，否则报
     "resource is not bound" —— 这是实测踩出来的）

用法：
    python tools/run_task.py                      # 列出所有任务
    python tools/run_task.py 重复刷关              # 跑一个任务
    python tools/run_task.py 重复刷关 --option 刷取次数=3
    python tools/run_task.py --node 主界面_就绪    # 直接跑一个节点
"""

import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_ADB_CANDIDATES = [
    r"E:\MuMu Player 12\shell\adb.exe",
    r"E:\MuMu Player 12\nx_main\adb.exe",
    r"D:\MuMu Player 12\shell\adb.exe",
]
DEFAULT_ADDRESS = "127.0.0.1:16384"


def _merge(dst, src):
    """按 PI 的规则合并 pipeline_override：顶层字段同名就覆盖，对象不深合并。"""
    for node, fields in (src or {}).items():
        dst.setdefault(node, {})
        dst[node].update(fields)


def _pick_case(option, case_name):
    for c in option.get("cases", []):
        if c.get("name") == case_name:
            return c
    return None


def build_overrides(interface, task_name, extra_pairs, case_overrides=None):
    """按 GUI 的规则把任务的默认选项展开成 pipeline_override。

    支持 select / switch / checkbox / input 四种类型，用的是各自 default_case / default。
    input 的 {占位符} 会按 pipeline_type 转成 int / bool / string。

    case_overrides: {选项名: [case 名, ...]}，用来复现"用户在 GUI 里勾了什么"。
    这个很有用 —— 踩过：命令行按默认选项跑是好的，用户在 GUI 里只勾了一项，
    走到某条 next 上没有兜底节点，死等 20 秒判失败。光看默认选项永远复现不出来。
    """
    task = None
    for t in interface.get("task", []):
        if t.get("name") == task_name:
            task = t
            break
    if task is None:
        return {}

    case_overrides = case_overrides or {}
    overrides = {}
    for opt_name in task.get("option", []):
        opt = interface.get("option", {}).get(opt_name)
        if not opt:
            continue
        otype = opt.get("type")
        chosen = case_overrides.get(opt_name)

        if otype in ("select", "switch"):
            want = chosen[0] if chosen else opt.get("default_case")
            case = _pick_case(opt, want)
            if case:
                _merge(overrides, case.get("pipeline_override"))

        elif otype == "checkbox":
            names = chosen if chosen is not None else opt.get("default_case", [])
            for case_name in names:
                case = _pick_case(opt, case_name)
                if case:
                    _merge(overrides, case.get("pipeline_override"))

        elif otype == "input":
            values = {}
            for item in opt.get("inputs", []):
                values[item["name"]] = item.get("default", "")
            # 命令行传进来的覆盖默认值
            for pair in extra_pairs:
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    if k in values:
                        values[k] = v

            def convert(key, raw):
                for item in opt.get("inputs", []):
                    if item["name"] == key:
                        pt = item.get("pipeline_type", "string")
                        if pt == "int":
                            try:
                                return int(raw)
                            except (TypeError, ValueError):
                                return raw
                        if pt == "bool":
                            return str(raw).lower() in ("1", "true", "yes", "y")
                return raw

            def replace(obj):
                """把 {占位符} 换成实际值，并按 pipeline_type 转类型。"""
                if isinstance(obj, str):
                    # 整串就是一个占位符 -> 直接换成对应类型的值
                    for k, v in values.items():
                        if obj == "{%s}" % k:
                            return convert(k, v)
                    out = obj
                    for k, v in values.items():
                        out = out.replace("{%s}" % k, str(v))
                    return out
                if isinstance(obj, dict):
                    return {k: replace(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [replace(v) for v in obj]
                return obj

            tmpl = opt.get("pipeline_override")
            if tmpl:
                import copy
                _merge(overrides, replace(copy.deepcopy(tmpl)))

    _merge(overrides, task.get("pipeline_override"))
    return overrides


def load_interface():
    path = os.path.join(ROOT, "assets", "interface.json")
    raw = open(path, encoding="utf-8").read()
    # 去掉 // 行注释
    lines = []
    for line in raw.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("//"):
            continue
        lines.append(line)
    return json.loads("\n".join(lines))


def find_adb():
    for c in DEFAULT_ADB_CANDIDATES:
        if os.path.isfile(c):
            return c
    import shutil
    return shutil.which("adb")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="直接用 MaaFramework 跑一个任务")
    parser.add_argument("task", nargs="?", help="任务名或节点名")
    parser.add_argument("--node", action="store_true", help="把参数当成节点名，不查 interface")
    parser.add_argument("--option", action="append", default=[],
                        help="覆盖选项，形如 --option 刷取次数=3（只支持手填类）")
    parser.add_argument("--case", action="append", default=[], dest="cases",
                        help="复现 GUI 里勾了什么，形如 --case 邮件操作=领取附件"
                             "（多选用逗号分隔：--case 邮件操作=领取附件,领取体力）")
    parser.add_argument("--adb", default=None)
    parser.add_argument("--address", default=DEFAULT_ADDRESS)
    parser.add_argument("--no-agent", action="store_true", help="不启动 agent（纯识别任务用）")
    args = parser.parse_args()

    interface = load_interface()

    # 列出任务
    if not args.task:
        print("可用任务：")
        for t in interface.get("task", []):
            print("  %-18s -> %s" % (t["name"], t["entry"]))
            if t.get("description"):
                print("      %s" % t["description"])
        print()
        print("用法: python tools/run_task.py <任务名>")
        return

    entry = args.task
    overrides = {}
    case_overrides = {}
    for pair in args.cases:
        if "=" not in pair:
            print(f"[!!] --case 要写成 选项名=case名（多选用逗号分隔），收到的是 {pair!r}")
            return 1
        key, value = pair.split("=", 1)
        case_overrides[key.strip()] = [v.strip() for v in value.split(",") if v.strip()]

    if not args.node:
        for t in interface.get("task", []):
            if t["name"] == args.task:
                entry = t["entry"]
                break
        else:
            print(f"[!!] interface.json 里没有任务「{args.task}」，当成节点名试")
        overrides = build_overrides(interface, args.task, args.option, case_overrides)
        print(f"任务「{args.task}」-> 入口节点 {entry}")
        if case_overrides:
            print("按 --case 指定的选项: " + json.dumps(case_overrides, ensure_ascii=False))
        print(f"展开出 {len(overrides)} 个节点的 override")
    else:
        print(f"直接跑节点 {entry}")

    # agent 子进程
    agent_proc = None
    client = None
    if not args.no_agent:
        from maa.agent_client import AgentClient
        import uuid
        agent_script = os.path.join(ROOT, "assets", "agent", "main.py")
        if not os.path.isfile(agent_script):
            agent_script = os.path.join(ROOT, "agent", "main.py")
        exec_ = sys.executable
        # 显式给 identifier：自动创建的那个有时候读不回来（client.identifier 返回 None），
        # 那样 agent 子进程就拿到空 id，永远连不上。
        ident = "bh2maa" + uuid.uuid4().hex[:8]
        client = AgentClient(ident)
        # -u 是必须的：agent 的 print 重定向到文件时是块缓冲，
        # 而这里最后是 kill 掉子进程，缓冲区里没冲出来的日志会全丢（踩过：日志只剩启动那一行）。
        cmd = [exec_, "-u", agent_script, ident, "socket_id=%s" % ident]
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"
        # agent 的 print 是排查问题的唯一线索（尤其 bonus_battle 的战斗日志），
        # 丢 DEVNULL 等于瞎跑，所以落一份到 debug/agent.log。
        log_dir = os.path.join(ROOT, "debug")
        os.makedirs(log_dir, exist_ok=True)
        agent_log_path = os.path.join(log_dir, "agent.log")
        agent_log = open(agent_log_path, "w", encoding="utf-8", errors="replace")
        agent_proc = subprocess.Popen(cmd, cwd=os.path.dirname(agent_script),
                                      env=env,
                                      stdout=agent_log, stderr=subprocess.STDOUT)
        print(f"agent 已启动 pid={agent_proc.pid} identifier={ident} script={agent_script}")
        print(f"agent 日志 -> {agent_log_path}")

    try:
        from maa.controller import AdbController
        from maa.resource import Resource
        from maa.tasker import Tasker
        from maa.toolkit import Toolkit

        Toolkit.init_option(ROOT)

        resource = Resource()
        job = resource.post_bundle(os.path.join(ROOT, "assets", "resource"))
        job.wait()
        if not job.succeeded:
            print("[!!] 资源加载失败")
            return 1
        print("资源加载 OK")

        if overrides:
            resource.override_pipeline(overrides)

        if client is not None:
            client.bind(resource)
            connected = False
            for i in range(10):
                if client.connect():
                    connected = True
                    break
                time.sleep(1)
            print("agent 连接:", "OK" if connected else "失败")
            if not connected:
                return 1

        adb = args.adb or find_adb()
        if not adb:
            print("[!!] 找不到 adb")
            return 1
        controller = AdbController(adb, args.address)
        controller.post_connection().wait()
        if not controller.connected:
            print("[!!] 连不上模拟器")
            return 1
        print("模拟器已连接")

        tasker = Tasker()
        if not tasker.bind(resource, controller):
            print("[!!] bind 失败")
            return 1

        print("开始执行……")
        detail = tasker.post_task(entry).wait().get()
        status = getattr(detail, "status", None)
        print("执行结果:", status, "succeeded =", getattr(status, "succeeded", "?"))
        for node in (getattr(detail, "nodes", None) or []):
            reco = getattr(node, "recognition", None)
            box = getattr(reco, "box", None) if reco is not None else None
            print("   %-34s %s" % (getattr(node, "name", "?"),
                                   ("命中 " + str(box)) if box is not None else "未命中"))
        return 0
    finally:
        if agent_proc is not None:
            try:
                agent_proc.kill()
            except Exception:  # noqa: BLE001
                pass
        try:
            agent_log.close()
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    sys.exit(main())
