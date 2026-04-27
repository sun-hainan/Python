# -*- coding: utf-8 -*-

"""

算法实现：数据库内核 / concurrency_control



本文件实现 concurrency_control 相关的算法功能。

"""



from typing import Dict, List, Optional, Tuple, Set, Any

from dataclasses import dataclass, field

from enum import IntEnum

import threading

import time



# 锁类型

class LockType(IntEnum):

    SHARED = 1       # 共享锁（S）

    EXCLUSIVE = 2     # 排他锁（X）

    UPDATE = 3        # 更新锁（U）- 用于防止死锁

    INTENTION_SHARED = 4   # 意向共享锁（IS）

    INTENTION_EXCLUSIVE = 5 # 意向排他锁（IX）



# 事务状态

class TransactionState(IntEnum):

    ACTIVE = 1

    WAITING = 2

    COMMITTED = 3

    ABORTED = 4





@dataclass

class LockRequest:

    """锁请求"""

    tx_id: int

    lock_type: LockType

    resource_id: str

    timestamp: float = field(default_factory=time.time)





@dataclass

class Transaction:

    """事务"""

    tx_id: int

    state: TransactionState = TransactionState.ACTIVE

    start_time: float = field(default_factory=time.time)

    locks_held: Set[str] = field(default_factory=set)  # 持有的锁

    wait_for_graph_edges: List[Tuple[int, int]] = field(default_factory=list)  # 等待图边





class LockManager:

    """

    锁管理器

    实现多种锁模式并支持死锁检测

    """

    

    def __init__(self):

        self.lock_table: Dict[str, List[LockRequest]] = {}  # resource_id -> 锁列表

        self.tx_table: Dict[int, Transaction] = {}          # tx_id -> 事务

        self.lock_manager_lock = threading.Lock()

    

    def acquire_lock(self, tx_id: int, resource_id: str, 

                     lock_type: LockType, timeout: float = 5.0) -> bool:

        """

        尝试获取锁

        返回: 是否成功获取锁

        """

        with self.lock_manager_lock:

            if tx_id not in self.tx_table:

                self.tx_table[tx_id] = Transaction(tx_id)

            

            tx = self.tx_table[tx_id]

            

            # 检查是否已持有该资源的锁

            if resource_id in tx.locks_held:

                return True

            

            # 尝试获取锁

            if self._can_grant_lock(resource_id, lock_type, tx_id):

                self._grant_lock(tx_id, resource_id, lock_type)

                return True

            

            # 无法立即获取，加入等待

            tx.state = TransactionState.WAITING

            

            # 添加到资源等待队列

            if resource_id not in self.lock_table:

                self.lock_table[resource_id] = []

            

            self.lock_table[resource_id].append(

                LockRequest(tx_id, lock_type, resource_id)

            )

        

        # 等待锁（模拟）

        start_wait = time.time()

        while time.time() - start_wait < timeout:

            time.sleep(0.01)

            with self.lock_manager_lock:

                if resource_id in tx.locks_held:

                    return True

        

        # 超时，返回失败

        return False

    

    def _can_grant_lock(self, resource_id: str, lock_type: LockType, 

                        request_tx_id: int) -> bool:

        """检查是否能授予锁"""

        if resource_id not in self.lock_table:

            return True

        

        # 检查与已有锁是否冲突

        for req in self.lock_table[resource_id]:

            if req.tx_id == request_tx_id:

                continue

            

            # 排他锁与其他任何锁冲突

            if lock_type == LockType.EXCLUSIVE:

                return False

            

            # 共享锁与排他锁冲突

            if (req.lock_type == LockType.EXCLUSIVE and 

                lock_type != LockType.SHARED):

                return False

        

        return True

    

    def _grant_lock(self, tx_id: int, resource_id: str, lock_type: LockType):

        """授予锁"""

        if resource_id not in self.lock_table:

            self.lock_table[resource_id] = []

        

        self.lock_table[resource_id].append(

            LockRequest(tx_id, lock_type, resource_id)

        )

        

        if tx_id in self.tx_table:

            self.tx_table[tx_id].locks_held.add(resource_id)

            self.tx_table[tx_id].state = TransactionState.ACTIVE

    

    def release_lock(self, tx_id: int, resource_id: str) -> bool:

        """释放锁"""

        with self.lock_manager_lock:

            if tx_id not in self.tx_table:

                return False

            

            tx = self.tx_table[tx_id]

            

            if resource_id in tx.locks_held:

                tx.locks_held.remove(resource_id)

                

                # 从锁表中移除

                if resource_id in self.lock_table:

                    self.lock_table[resource_id] = [

                        r for r in self.lock_table[resource_id] if r.tx_id != tx_id

                    ]

                    if not self.lock_table[resource_id]:

                        del self.lock_table[resource_id]

                

                return True

            

            return False

    

    def release_all_locks(self, tx_id: int):

        """释放事务持有的所有锁"""

        with self.lock_manager_lock:

            if tx_id not in self.tx_table:

                return

            

            tx = self.tx_table[tx_id]

            for resource_id in list(tx.locks_held):

                self.release_lock(tx_id, resource_id)





class TwoPhaseLocking:

    """

    两阶段锁协议（2PL）

    增长阶段：只能获取锁

    收缩阶段：只能释放锁

    """

    

    def __init__(self, lock_manager: LockManager):

        self.lock_manager = lock_manager

        self.tx_phase: Dict[int, str] = {}  # tx_id -> "growing" or "shrinking"

    

    def begin_transaction(self, tx_id: int):

        """事务开始"""

        self.tx_phase[tx_id] = "growing"

    

    def read(self, tx_id: int, resource: str) -> bool:

        """读取资源（获取共享锁）"""

        if self.tx_phase.get(tx_id) == "shrinking":

            raise Exception(f"事务 {tx_id} 已进入收缩阶段，不能获取新锁")

        

        return self.lock_manager.acquire_lock(tx_id, resource, LockType.SHARED)

    

    def write(self, tx_id: int, resource: str) -> bool:

        """写入资源（获取排他锁）"""

        if self.tx_phase.get(tx_id) == "shrinking":

            raise Exception(f"事务 {tx_id} 已进入收缩阶段，不能获取新锁")

        

        return self.lock_manager.acquire_lock(tx_id, resource, LockType.EXCLUSIVE)

    

    def commit(self, tx_id: int):

        """提交（进入收缩阶段，释放所有锁）"""

        self.tx_phase[tx_id] = "shrinking"

        self.lock_manager.release_all_locks(tx_id)

        self.tx_phase.pop(tx_id, None)

    

    def abort(self, tx_id: int):

        """中止（立即释放所有锁）"""

        self.lock_manager.release_all_locks(tx_id)

        self.tx_phase.pop(tx_id, None)





class OptimisticConcurrencyControl:

    """

    乐观并发控制（OCC）

    三个阶段：读取/验证/写入

    适用于冲突较少的场景

    """

    

    def __init__(self):

        self.transactions: Dict[int, Dict] = {}  # tx_id -> 事务信息

    

    def begin_transaction(self, tx_id: int):

        """开始事务"""

        self.transactions[tx_id] = {

            "read_set": [],    # 读集 [(resource_id, value), ...]

            "write_set": [],   # 写集 [(resource_id, value), ...]

            "start_time": time.time()

        }

    

    def read(self, tx_id: int, resource: str, value: Any):

        """读取阶段"""

        tx_info = self.transactions.get(tx_id)

        if not tx_info:

            raise Exception(f"事务 {tx_id} 不存在")

        

        tx_info["read_set"].append((resource, value))

    

    def write(self, tx_id: int, resource: str, new_value: Any):

        """写入阶段"""

        tx_info = self.transactions.get(tx_id)

        if not tx_info:

            raise Exception(f"事务 {tx_id} 不存在")

        

        tx_info["write_set"].append((resource, new_value))

    

    def validate(self, tx_id: int) -> bool:

        """

        验证阶段

        检查是否与其他已提交事务冲突

        """

        tx_info = self.transactions.get(tx_id)

        if not tx_info:

            return False

        

        read_set = tx_info["read_set"]

        write_set = tx_info["write_set"]

        

        # 检查读集中的值是否被其他事务修改

        for res_id, old_value in read_set:

            # 模拟：检查是否有其他事务写入同一资源且更晚提交

            for other_tx_id, other_info in self.transactions.items():

                if other_tx_id == tx_id:

                    continue

                

                if other_info["start_time"] > tx_info["start_time"]:

                    # 其他事务在之后开始

                    for w_res, w_val in other_info["write_set"]:

                        if w_res == res_id:

                            # 资源被修改，冲突检测

                            # 如果其他事务已提交，则验证失败

                            # 此处简化处理

                            pass

        

        return True

    

    def commit(self, tx_id: int) -> bool:

        """提交事务"""

        tx_info = self.transactions.get(tx_id)

        if not tx_info:

            return False

        

        # 验证

        if not self.validate(tx_id):

            # 验证失败，回滚

            self.transactions.pop(tx_id, None)

            return False

        

        # 写入（应用写集）

        # 实际实现中需要原子性地应用所有写操作

        self.transactions.pop(tx_id, None)

        return True





class DeadlockDetector:

    """

    死锁检测器（基于等待图/WFG）

    """

    

    def __init__(self, lock_manager: LockManager):

        self.lock_manager = lock_manager

    

    def build_wait_for_graph(self) -> Dict[int, List[int]]:

        """

        构建等待图

        边 (i, j) 表示事务i等待事务j持有的资源

        """

        graph: Dict[int, List[int]] = {}

        

        with self.lock_manager.lock_manager_lock:

            # 遍历所有锁请求

            for resource_id, requests in self.lock_manager.lock_table.items():

                for req in requests:

                    tx = self.lock_manager.tx_table.get(req.tx_id)

                    if tx and tx.state == TransactionState.WAITING:

                        # 该事务在等待

                        if req.tx_id not in graph:

                            graph[req.tx_id] = []

                        

                        # 找到持有该资源锁的事务

                        for held_req in requests:

                            if held_req.tx_id != req.tx_id:

                                # 持有者可能是冲突的（简化处理）

                                graph[req.tx_id].append(held_req.tx_id)

        

        return graph

    

    def detect_deadlock(self) -> Optional[List[int]]:

        """

        检测死锁（使用DFS找环）

        返回: 死锁环中的事务ID列表

        """

        graph = self.build_wait_for_graph()

        visited = set()

        rec_stack = set()

        path = []

        

        def dfs(tx_id: int) -> Optional[List[int]]:

            if tx_id in rec_stack:

                # 找到环，返回环中的事务

                return [tx_id]

            

            if tx_id in visited:

                return None

            

            visited.add(tx_id)

            rec_stack.add(tx_id)

            

            for neighbor in graph.get(tx_id, []):

                result = dfs(neighbor)

                if result:

                    if result[0] == tx_id:

                        return result

                    return result + [tx_id]

            

            rec_stack.remove(tx_id)

            return None

        

        # 检查所有节点

        for tx_id in graph:

            if tx_id not in visited:

                cycle = dfs(tx_id)

                if cycle:

                    return cycle

        

        return None

    

    def resolve_deadlock(self, victim_tx_ids: List[int]):

        """解决死锁，选择受害者回滚"""

        for tx_id in victim_tx_ids:

            print(f"死锁解决: 回滚事务 {tx_id}")

            self.lock_manager.release_all_locks(tx_id)





if __name__ == "__main__":

    # 演示并发控制

    print("=" * 60)

    print("并发控制算法演示")

    print("=" * 60)

    

    # 1. 2PL演示

    lock_mgr = LockManager()

    protocol = TwoPhaseLocking(lock_mgr)

    

    print("\n--- 2PL (两阶段锁) ---")

    protocol.begin_transaction(1)

    protocol.begin_transaction(2)

    

    print(f"Tx1 读取资源 A: {protocol.read(1, 'resource_A')}")

    print(f"Tx1 写入资源 B: {protocol.write(1, 'resource_B')}")

    print(f"Tx2 读取资源 B: {protocol.read(2, 'resource_B')}")  # 可能阻塞

    

    protocol.commit(1)

    protocol.commit(2)

    

    # 2. OCC演示

    print("\n--- OCC (乐观并发控制) ---")

    occ = OptimisticConcurrencyControl()

    

    occ.begin_transaction(100)

    occ.read(100, "x", 10)

    occ.read(100, "y", 20)

    occ.write(100, "z", 30)

    print(f"Tx100 验证: {occ.validate(100)}")

    print(f"Tx100 提交: {occ.commit(100)}")

    

    # 3. 死锁检测演示

    print("\n--- 死锁检测 ---")

    lock_mgr2 = LockManager()

    

    # 模拟死锁场景

    lock_mgr2.acquire_lock(10, "R1", LockType.SHARED)

    lock_mgr2.acquire_lock(20, "R2", LockType.SHARED)

    lock_mgr2.acquire_lock(10, "R2", LockType.EXCLUSIVE)  # Tx10等待R2

    lock_mgr2.acquire_lock(20, "R1", LockType.EXCLUSIVE)  # Tx20等待R1 - 死锁!

    

    detector = DeadlockDetector(lock_mgr2)

    cycle = detector.detect_deadlock()

    

    if cycle:

        print(f"检测到死锁环: {cycle}")

        detector.resolve_deadlock(cycle[1:])  # 回滚除第一个外的事务

    else:

        print("未检测到死锁")

