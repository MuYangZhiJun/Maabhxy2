import sys

from maa.agent.agent_server import AgentServer
from maa.toolkit import Toolkit

import my_action
import my_bonus
import my_reco


def _pick_socket_id(argv):
    """从命令行里挑出 socket_id。

    客户端（MFAAvalonia）实际传的是这样一串：
        main.py kvZafnuL socket_id=kvZafnuL instance_id=default instance_name=配置 1

    注意最后那个 instance_name 里带空格，会被拆成两个参数 —— 所以原来写的
    `sys.argv[-1]` 拿到的是「1」，不是 socket_id，agent 于是拿着错的 id 去连，
    永远连不上，表现就是界面一直卡在「正在启动 Agent」。

    这里按优先级找：显式的 socket_id=xxx > 第一个位置参数 > 最后一个参数。
    """
    for arg in argv[1:]:
        if arg.startswith("socket_id="):
            value = arg.split("=", 1)[1].strip()
            if value:
                return value
    if len(argv) > 1 and "=" not in argv[1]:
        return argv[1].strip()
    if len(argv) > 1:
        return argv[-1].strip()
    return None


def main():
    Toolkit.init_option("./")

    socket_id = _pick_socket_id(sys.argv)
    if not socket_id:
        print("Usage: python main.py <socket_id>")
        print("socket_id is provided by AgentIdentifier.")
        print("实际收到的参数: %r" % (sys.argv[1:],))
        sys.exit(1)

    try:
        import importlib.metadata as _md
        _ver = _md.version("maafw")
    except Exception:  # noqa: BLE001
        _ver = "(读不到)"
    print("agent 启动，socket_id=%s，maafw=%s，argv=%r"
          % (socket_id, _ver, sys.argv[1:]), flush=True)

    # ⚠️ start_up 的返回值必须检查！它连不上的时候不抛异常，只返回 False，
    # 后面 join() 就永久阻塞 —— 进程活着、CPU 几乎为 0，界面上表现为一直卡在
    # 「正在启动 Agent」，要等五分钟重试耗尽才报「任务运行失败」，很难查。
    # 实测踩到的原因：**Python 的 maafw 版本和 GUI 自带 MaaFramework 的版本不一致**
    # （agent 走的是内部协议，大版本对不上就是连不上：4.3.2 对 5.13.0 连不上）。
    if not AgentServer.start_up(socket_id):
        print("[!!] agent 连不上 GUI 的 socket（socket_id=%s），直接退出，不再空等。" % socket_id,
              flush=True)
        print("[!!] 多半是版本不一致：python -m pip show maafw 的版本，"
              "要和 gui/runtimes/win-x64/native/MaaFramework.dll 里的版本号（字符串 vX.Y.Z）一致。",
              flush=True)
        sys.exit(2)

    AgentServer.join()
    AgentServer.shut_down()


if __name__ == "__main__":
    main()
