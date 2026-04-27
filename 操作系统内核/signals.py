# -*- coding: utf-8 -*-

"""

算法实现：操作系统内核 / signals



本文件实现 signals 相关的算法功能。

"""



from typing import Dict, List, Optional, Set, Callable

from dataclasses import dataclass, field

from enum import Enum

import time





class SignalNumber(Enum):

    """信号编号"""

    SIGHUP = 1

    SIGINT = 2

    SIGQUIT = 3

    SIGILL = 4

    SIGTRAP = 5

    SIGABRT = 6

    SIGBUS = 7

    SIGFPE = 8

    SIGKILL = 9

    SIGUSR1 = 10

    SIGSEGV = 11

    SIGUSR2 = 12

    SIGPIPE = 13

    SIGALRM = 14

    SIGTERM = 15

    SIGSTKFLT = 16

    SIGCHLD = 17

    SIGCONT = 18

    SIGSTOP = 19

    SIGTSTP = 20





class SignalAction:

    """信号处理动作"""

    SIG_DFL = 0  # 默认动作

    SIG_IGN = 1  # 忽略

    # 用户自定义处理函数

    custom_handler: Optional[Callable] = None





@dataclass

class SignalInfo:

    """信号信息"""

    signum: int

    pid: int  # 发送者PID

    uid: int   # 发送者UID

    timestamp: float = field(default_factory=time.time)

    info: str = ""





class SignalHandler:

    """

    信号处理器



    管理信号处理函数和信号队列。

    """



    def __init__(self, pid: int):

        self.pid = pid



        # 信号处理函数表

        self.handlers: Dict[int, SignalAction] = {}



        # 待处理信号队列

        self.pending_signals: List[SignalInfo] = []



        # 已阻塞的信号

        self.blocked_signals: Set[int] = set()



        # 信号栈

        self.signal_stack: Optional[bytes] = None



        # 初始化默认处理

        self._init_default_handlers()



    def _init_default_handlers(self):

        """初始化默认处理"""

        for sig in SignalNumber:

            self.handlers[sig.value] = SignalAction()



    def set_handler(self, signum: int, handler: Callable):

        """设置信号处理函数"""

        if signum in self.handlers:

            self.handlers[signum].custom_handler = handler



    def set_ignore(self, signum: int):

        """忽略信号"""

        if signum in self.handlers:

            self.handlers[signum] = SignalAction(SIG_IGN)



    def set_default(self, signum: int):

        """恢复默认处理"""

        if signum in self.handlers:

            self.handlers[signum] = SignalAction(SIG_DFL)



    def send_signal(self, signum: int, sender_pid: int, uid: int = 0):

        """发送信号"""

        if signum in self.blocked_signals:

            # 被阻塞，加入pending队列

            info = SignalInfo(signum, sender_pid, uid, info=f"SIG{signum}")

            self.pending_signals.append(info)

            return False



        # 检查是否有自定义处理

        action = self.handlers.get(signum, SignalAction())



        if action == SignalAction(SIG_IGN):

            # 忽略

            return True



        if action == SignalAction(SIG_DFL):

            # 默认动作

            return self._execute_default_action(signum)



        if action.custom_handler:

            # 调用自定义处理函数

            return self._execute_custom_handler(action.custom_handler, signum)



        return False



    def _execute_default_action(self, signum: int) -> bool:

        """执行默认动作"""

        if signum == SignalNumber.SIGCHLD.value:

            # 忽略

            return True

        elif signum == SignalNumber.SIGSTOP.value:

            # 停止进程

            print(f"  [PID={self.pid}] 收到SIGSTOP，进程停止")

            return True

        elif signum == SignalNumber.SIGKILL.value:

            # 杀死进程（不可捕获）

            print(f"  [PID={self.pid}] 收到SIGKILL，进程被终止")

            return True

        elif signum == SignalNumber.SIGTERM.value:

            # 优雅终止

            print(f"  [PID={self.pid}] 收到SIGTERM，请求终止")

            return True



        return True



    def _execute_custom_handler(self, handler: Callable, signum: int) -> bool:

        """执行自定义处理函数"""

        print(f"  [PID={self.pid}] 调用自定义信号处理函数 (SIG{signum})")

        try:

            handler(signum)

            return True

        except:

            return False



    def block_signal(self, signum: int):

        """阻塞信号"""

        self.blocked_signals.add(signum)



    def unblock_signal(self, signum: int):

        """解除信号阻塞"""

        self.blocked_signals.discard(signum)

        # 处理pending信号

        self._process_pending_signals()



    def _process_pending_signals(self):

        """处理pending信号"""

        still_pending = []

        for info in self.pending_signals:

            if info.signum not in self.blocked_signals:

                self.send_signal(info.signum, info.pid, info.uid)

            else:

                still_pending.append(info)

        self.pending_signals = still_pending



    def pending(self) -> List[int]:

        """获取pending信号列表"""

        return [info.signum for info in self.pending_signals]





class SignalQueue:

    """

    信号队列（System V信号）

    """

    def __init__(self, pid: int):

        self.pid = pid

        self.queue: List[SignalInfo] = []



    def enqueue(self, info: SignalInfo):

        """入队"""

        self.queue.append(info)



    def dequeue(self) -> Optional[SignalInfo]:

        """出队"""

        if self.queue:

            return self.queue.pop(0)

        return None



    def peek(self) -> Optional[SignalInfo]:

        """查看队首"""

        if self.queue:

            return self.queue[0]

        return None





class SignalSimulator:

    """信号模拟器"""



    def __init__(self):

        self.processes: Dict[int, SignalHandler] = {}

        self.signal_queues: Dict[int, SignalQueue] = {}



    def register_process(self, pid: int):

        """注册进程"""

        self.processes[pid] = SignalHandler(pid)

        self.signal_queues[pid] = SignalQueue(pid)



    def send_to_process(self, target_pid: int, signum: int, sender_pid: int):

        """向进程发送信号"""

        if target_pid not in self.processes:

            return False



        handler = self.processes[target_pid]

        return handler.send_signal(signum, sender_pid)



    def send_to_process_group(self, pgid: int, signum: int, sender_pid: int):

        """向进程组发送信号"""

        for pid, handler in self.processes.items():

            # 简化：假设所有进程都属于同一组

            handler.send_signal(signum, sender_pid)





def simulate_signals():

    """

    模拟信号机制

    """

    print("=" * 60)

    print("信号 (Signals)")

    print("=" * 60)



    # 创建信号模拟器

    sim = SignalSimulator()



    # 注册进程

    pid1 = 100

    pid2 = 101

    sim.register_process(pid1)

    sim.register_process(pid2)



    print(f"\n进程注册:")

    print(f"  PID={pid1}: 已注册")

    print(f"  PID={pid2}: 已注册")



    # 信号发送演示

    print("\n" + "-" * 50)

    print("信号发送演示")

    print("-" * 50)



    print(f"\n1. 发送 SIGTERM 到 PID={pid1}:")

    sim.send_to_process(pid1, SignalNumber.SIGTERM.value, 0)



    print(f"\n2. 发送 SIGINT 到 PID={pid2}:")

    sim.send_to_process(pid2, SignalNumber.SIGINT.value, 0)



    print(f"\n3. 发送 SIGKILL 到 PID={pid1}:")

    sim.send_to_process(pid1, SignalNumber.SIGKILL.value, 0)



    # 自定义信号处理

    print("\n" + "-" * 50)

    print("自定义信号处理")

    print("-" * 50)



    def custom_handler(signum):

        print(f"    自定义处理: 处理信号 {signum}")



    print(f"\n4. 设置SIGUSR1的自定义处理:")

    handler = sim.processes[pid1]

    handler.set_handler(SignalNumber.SIGUSR1.value, custom_handler)



    print(f"\n5. 发送 SIGUSR1 到 PID={pid1}:")

    sim.send_to_process(pid1, SignalNumber.SIGUSR1.value, 0)



    # 信号阻塞

    print("\n" + "-" * 50)

    print("信号阻塞")

    print("-" * 50)



    print(f"\n6. 阻塞 SIGUSR1:")

    handler.block_signal(SignalNumber.SIGUSR1.value)



    print(f"\n7. 发送 SIGUSR1 到 PID={pid1} (应该pending):")

    sim.send_to_process(pid1, SignalNumber.SIGUSR1.value, 0)

    pending = handler.pending()

    print(f"   Pending信号: {pending}")



    print(f"\n8. 解除阻塞 SIGUSR1:")

    handler.unblock_signal(SignalNumber.SIGUSR1.value)



    # 信号忽略

    print("\n" + "-" * 50)

    print("信号忽略")

    print("-" * 50)



    print(f"\n9. 忽略 SIGCHLD:")

    handler.set_ignore(SignalNumber.SIGCHLD.value)



    print(f"\n10. 发送 SIGCHLD 到 PID={pid1}:")

    sim.send_to_process(pid1, SignalNumber.SIGCHLD.value, 0)

    print(f"    (信号被忽略)")



    # 信号列表

    print("\n" + "=" * 60)

    print("常见信号列表")

    print("=" * 60)

    common_signals = [

        (1, "SIGHUP", "挂断"),

        (2, "SIGINT", "中断 (Ctrl+C)"),

        (9, "SIGKILL", "强制终止 (不可捕获)"),

        (15, "SIGTERM", "终止 (可捕获)"),

        (11, "SIGSEGV", "段错误"),

        (17, "SIGCHLD", "子进程状态改变"),

    ]



    print(f"\n{'编号':<6} {'名称':<12} {'描述':<20}")

    print("-" * 40)

    for num, name, desc in common_signals:

        print(f"{num:<6} {name:<12} {desc:<20}")





if __name__ == "__main__":

    simulate_signals()

