# -*- coding: utf-8 -*-

"""

算法实现：数据库内核 / deadlock_detection



本文件实现 deadlock_detection 相关的算法功能。

"""



import time

from collections import defaultdict, deque

from dataclasses import dataclass, field

from typing import Dict, List, Set, Tuple, Optional

from enum import Enum





class LockMode(Enum):

    """锁模式"""

    SHARED = "S"  # 共享锁

    EXCLUSIVE = "X"  # 排他锁





@dataclass

class LockRequest:

    """锁请求"""

    transaction_id: int  # 事务ID

    resource_id: str  # 资源ID

    mode: LockMode  # 锁模式

    timestamp: float = field(default_factory=time.time)  # 请求时间





@dataclass

class Transaction:

    """事务信息"""

    tx_id: int  # 事务ID

    blocked_by: Optional[int] = None  # 被哪个事务阻塞

    blocked_since: Optional[float] = None  # 阻塞开始时间

    wait_for: Set[str] = field(default_factory=set)  # 等待的资源





class WaitGraph:

    """

    事务等待图



    顶点: 事务

    边: T1 -> T2 表示T1等待T2持有的锁

    检测环: 死锁

    """



    def __init__(self):

        self.edges: Dict[int, List[int]] = defaultdict(list)  # 等待图边

        self.transactions: Dict[int, Transaction] = {}  # 事务信息



    def add_transaction(self, tx_id: int):

        """添加事务顶点"""

        if tx_id not in self.transactions:

            self.transactions[tx_id] = Transaction(tx_id=tx_id)



    def add_edge(self, from_tx: int, to_tx: int):

        """添加等待边: from_tx等待to_tx"""

        if from_tx != to_tx and to_tx not in self.edges[from_tx]:

            self.edges[from_tx].append(to_tx)



    def remove_vertex(self, tx_id: int):

        """移除事务(当事务结束时)"""

        if tx_id in self.transactions:

            del self.transactions[tx_id]

        if tx_id in self.edges:

            del self.edges[tx_id]

        # 移除所有指向该事务的边

        for tx in self.edges:

            if tx_id in self.edges[tx]:

                self.edges[tx].remove(tx_id)



    def detect_cycle(self) -> Optional[List[int]]:

        """

        检测等待图中的环(死锁)

        使用DFS检测 cycle



        返回:

            死锁环中事务ID列表, None表示无死锁

        """

        visited: Set[int] = set()

        rec_stack: Set[int] = set()

        path: List[int] = []



        def dfs(tx_id: int) -> Optional[List[int]]:

            """DFS遍历,检测回边"""

            visited.add(tx_id)

            rec_stack.add(tx_id)

            path.append(tx_id)



            for neighbor in self.edges.get(tx_id, []):

                if neighbor not in visited:

                    result = dfs(neighbor)

                    if result:

                        return result

                elif neighbor in rec_stack:

                    # 找到环,提取环

                    cycle_start = path.index(neighbor)

                    return path[cycle_start:] + [neighbor]



            path.pop()

            rec_stack.remove(tx_id)

            return None



        # 遍历所有顶点

        for tx_id in list(self.transactions.keys()):

            if tx_id not in visited:

                cycle = dfs(tx_id)

                if cycle:

                    return cycle



        return None



    def find_wait_cycle(self) -> List[List[int]]:

        """

        查找所有等待环

        使用Kahn算法变形检测所有环

        """

        in_degree: Dict[int, int] = {tx: 0 for tx in self.transactions}



        # 计算入度

        for tx in self.edges:

            for neighbor in self.edges[tx]:

                if neighbor in in_degree:

                    in_degree[neighbor] += 1



        cycles = []

        remaining = set(self.transactions.keys())



        while remaining:

            # 找到入度为0的节点(死锁边缘)

            no_incoming = [tx for tx in remaining if in_degree.get(tx, 0) == 0]

            if not no_incoming:

                break



            # 移除这些节点和它们的边

            for tx in no_incoming:

                remaining.remove(tx)

                for neighbor in self.edges.get(tx, []):

                    if neighbor in in_degree:

                        in_degree[neighbor] -= 1



        # 剩下的就是环中的事务

        if remaining:

            cycles.append(list(remaining))



        return cycles





class DeadlockDetector:

    """

    死锁检测器



    使用等待图算法检测死锁

    支持增量更新和定时检测

    """



    def __init__(self, timeout_seconds: float = 30.0):

        self.wait_graph = WaitGraph()  # 等待图

        self.lock_table: Dict[str, List[LockRequest]] = defaultdict(list)  # 锁表

        self.hold_locks: Dict[int, Set[str]] = defaultdict(set)  # 事务持有的锁

        self.timeout_seconds = timeout_seconds  # 死锁超时

        self.deadlock_history: List[List[int]] = []  # 历史死锁



    def request_lock(self, tx_id: int, resource: str, mode: LockMode) -> bool:

        """

        请求锁

        返回True表示获得锁, False表示需要等待

        """

        self.wait_graph.add_transaction(tx_id)



        # 检查是否能获得锁

        if self.can_grant_lock(resource, mode, tx_id):

            self.lock_table[resource].append(LockRequest(tx_id, resource, mode))

            self.hold_locks[tx_id].add(resource)

            return True

        else:

            # 不能获得,等待 - 构建等待边

            for held in self.lock_table[resource]:

                self.wait_graph.add_edge(tx_id, held.transaction_id)

            return False



    def can_grant_lock(self, resource: str, mode: LockMode, request_tx: int) -> bool:

        """检查是否可以授予锁"""

        holders = self.lock_table[resource]



        # 排他锁: 只能有一个持有者,且不能有其他锁

        if mode == LockMode.EXCLUSIVE:

            if any(h.mode == LockMode.EXCLUSIVE for h in holders):

                return False

            if any(h.transaction_id != request_tx for h in holders):

                return False

            return True



        # 共享锁: 不能有排他锁持有者

        if mode == LockMode.SHARED:

            if any(h.mode == LockMode.EXCLUSIVE for h in holders):

                return False

            return True



        return False



    def release_lock(self, tx_id: int, resource: str = None):

        """释放锁"""

        if resource:

            # 释放指定资源

            self.lock_table[resource] = [

                req for req in self.lock_table[resource]

                if req.transaction_id != tx_id

            ]

            self.hold_locks[tx_id].discard(resource)

        else:

            # 释放所有锁

            for res in list(self.hold_locks[tx_id]):

                self.release_lock(tx_id, res)



        self.wait_graph.remove_vertex(tx_id)



    def detect_deadlock(self) -> Optional[List[int]]:

        """

        检测当前是否存在死锁



        返回:

            死锁环中事务ID列表, None表示无死锁

        """

        return self.wait_graph.detect_cycle()



    def select_victim(self, deadlock_cycle: List[int]) -> int:

        """

        选择死锁牺牲者

        策略: 选择等待时间最长的事务

        """

        oldest = None

        oldest_time = float('inf')



        for tx_id in deadlock_cycle:

            tx = self.wait_graph.transactions.get(tx_id)

            if tx and tx.blocked_since:

                if tx.blocked_since < oldest_time:

                    oldest_time = tx.blocked_since

                    oldest = tx_id



        return oldest if oldest else deadlock_cycle[0]



    def resolve_deadlock(self) -> Tuple[bool, List[int]]:

        """

        检测并解决死锁



        返回:

            (是否发现死锁, 被回滚的事务ID列表)

        """

        deadlock_cycle = self.detect_deadlock()

        if not deadlock_cycle:

            return False, []



        print(f"检测到死锁: 事务 {deadlock_cycle}")



        # 选择牺牲者并回滚

        victim = self.select_victim(deadlock_cycle)

        print(f"选择事务 {victim} 作为牺牲者")



        # 释放该事务的所有锁

        self.release_lock(victim)

        self.deadlock_history.append(deadlock_cycle)



        return True, [victim]



    def check_timeout(self) -> List[int]:

        """检查超时等待的事务,返回应被回滚的事务"""

        now = time.time()

        timed_out = []



        for tx_id, tx in self.wait_graph.transactions.items():

            if tx.blocked_since and (now - tx.blocked_since) > self.timeout_seconds:

                timed_out.append(tx_id)



        return timed_out



    def print_wait_graph(self):

        """打印等待图"""

        print("=== 等待图 ===")

        for tx, neighbors in self.wait_graph.edges.items():

            for neighbor in neighbors:

                print(f"  T{tx} -> T{neighbor}")





if __name__ == "__main__":

    detector = DeadlockDetector(timeout_seconds=5.0)



    # 模拟死锁场景

    print("=== 模拟死锁场景 ===")

    # T1 持有 R1, 请求 R2

    detector.request_lock(1, "R1", LockMode.EXCLUSIVE)

    print("T1: 获得 R1 排他锁")



    # T2 持有 R2, 请求 R1

    detector.request_lock(2, "R2", LockMode.EXCLUSIVE)

    print("T2: 获得 R2 排他锁")



    # T1 请求 R2 (将被阻塞)

    granted = detector.request_lock(1, "R2", LockMode.EXCLUSIVE)

    print(f"T1: 请求 R2 {'获得' if granted else '等待'}")



    # T2 请求 R1 (将被阻塞,形成死锁)

    granted = detector.request_lock(2, "R1", LockMode.EXCLUSIVE)

    print(f"T2: 请求 R1 {'获得' if granted else '等待'}")



    detector.print_wait_graph()



    # 检测死锁

    print("\n=== 死锁检测 ===")

    has_deadlock, victims = detector.resolve_deadlock()

    print(f"发现死锁: {has_deadlock}, 牺牲者: {victims}")



    # 再次检测

    if has_deadlock:

        detector.print_wait_graph()

        has_deadlock2, _ = detector.resolve_deadlock()

        print(f"再次检测: {'仍有死锁' if has_deadlock2 else '死锁已解决'}")



    # 另一个场景: 链式等待

    print("\n=== 链式等待场景 ===")

    detector2 = DeadlockDetector()



    detector2.request_lock(10, "A", LockMode.SHARED)

    detector2.request_lock(11, "B", LockMode.SHARED)

    detector2.request_lock(12, "C", LockMode.SHARED)



    granted = detector2.request_lock(10, "B", LockMode.EXCLUSIVE)

    granted = detector2.request_lock(11, "C", LockMode.EXCLUSIVE)

    granted = detector2.request_lock(12, "A", LockMode.EXCLUSIVE)



    detector2.print_wait_graph()



    has_dl, victims = detector2.resolve_deadlock()

    print(f"链式等待检测: {'有死锁' if has_dl else '无死锁'}")

