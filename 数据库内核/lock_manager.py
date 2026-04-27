# -*- coding: utf-8 -*-
"""
算法实现：数据库内核 / lock_manager

本文件实现 lock_manager 相关的算法功能。
"""

from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from enum import IntEnum
import threading
import time

# 锁类型
class LockType(IntEnum):
    IS = 1    # 意向共享锁
    IX = 2    # 意向排他锁
    S = 3     # 共享锁
    X = 4     # 排他锁
    SIX = 5   # 共享意向排他锁（表中已有S锁且有意向获取IX）


@dataclass
class Lock:
    """锁对象"""
    lock_id: str            # 锁的唯一标识
    lock_type: LockType     # 锁类型
    owner_tx_id: int        # 持有事务ID
    resource_id: str        # 资源ID
    granted: bool = True    # 是否已授予
    wait_time: float = 0.0 # 等待时间
    
    def __repr__(self):
        return f"Lock({self.lock_type.name}, tx={self.owner_tx_id}, res={self.resource_id})"


@dataclass
class LockRequest:
    """锁请求"""
    tx_id: int
    lock_type: LockType
    resource_id: str
    timestamp: float = field(default_factory=time.time)
    mode: str = "blocking"  # "blocking" 或 "nowait"
    timeout: float = 30.0   # 等待超时时间


class LockManager:
    """
    锁管理器
    实现行锁、表锁、意向锁以及死锁检测
    """
    
    # 锁兼容性矩阵
    COMPAT_MATRIX = {
        (LockType.IS, LockType.IS): True,
        (LockType.IS, LockType.IX): True,
        (LockType.IS, LockType.S): True,
        (LockType.IS, LockType.X): False,
        (LockType.IX, LockType.IS): True,
        (LockType.IX, LockType.IX): True,
        (LockType.IX, LockType.S): False,
        (LockType.IX, LockType.X): False,
        (LockType.S, LockType.IS): True,
        (LockType.S, LockType.IX): False,
        (LockType.S, LockType.S): True,
        (LockType.S, LockType.X): False,
        (LockType.X, LockType.IS): False,
        (LockType.X, LockType.IX): False,
        (LockType.X, LockType.S): False,
        (LockType.X, LockType.X): False,
        (LockType.SIX, LockType.S): False,
        (LockType.SIX, LockType.X): False,
    }
    
    def __init__(self):
        self.lock_table: Dict[str, List[Lock]] = {}  # resource_id -> 锁列表
        self.tx_lock_map: Dict[int, Set[str]] = {}  # tx_id -> 锁集合
        self.wait_queue: Dict[str, List[LockRequest]] = {}  # 等待队列
        self.deadlock_threshold = 10.0  # 死锁检测阈值（秒）
        self.lock_id_counter = 0
        self.manager_lock = threading.Lock()
    
    def _generate_lock_id(self) -> str:
        """生成唯一锁ID"""
        self.lock_id_counter += 1
        return f"lock_{self.lock_id_counter}"
    
    def _can_grant(self, resource_id: str, lock_type: LockType, 
                   request_tx_id: int) -> bool:
        """检查锁是否可以被授予"""
        if resource_id not in self.lock_table:
            return True
        
        for lock in self.lock_table[resource_id]:
            if lock.owner_tx_id == request_tx_id:
                return True  # 已持有该资源的锁
            
            # 检查兼容性
            key = (lock.lock_type, lock_type)
            if key in self.COMPAT_MATRIX:
                if not self.COMPAT_MATRIX[key]:
                    return False
            else:
                if lock.lock_type == lock_type:
                    if lock_type not in (LockType.S, LockType.IS):
                        return False
        
        return True
    
    def _grant_lock(self, request: LockRequest) -> Lock:
        """授予锁"""
        lock = Lock(
            lock_id=self._generate_lock_id(),
            lock_type=request.lock_type,
            owner_tx_id=request.tx_id,
            resource_id=request.resource_id,
            granted=True
        )
        
        if request.resource_id not in self.lock_table:
            self.lock_table[request.resource_id] = []
        self.lock_table[request.resource_id].append(lock)
        
        if request.tx_id not in self.tx_lock_map:
            self.tx_lock_map[request.tx_id] = set()
        self.tx_lock_map[request.tx_id].add(request.resource_id)
        
        return lock
    
    def request_lock(self, request: LockRequest) -> Optional[Lock]:
        """
        请求锁
        返回: Lock对象（成功）或 None（失败/超时）
        """
        with self.manager_lock:
            # 检查是否可以授予
            if self._can_grant(request.resource_id, request.lock_type, request.tx_id):
                return self._grant_lock(request)
            
            # 无法授予，加入等待队列
            if request.resource_id not in self.wait_queue:
                self.wait_queue[request.resource_id] = []
            self.wait_queue[request.resource_id].append(request)
            
            # 创建未授予的锁对象
            lock = Lock(
                lock_id=self._generate_lock_id(),
                lock_type=request.lock_type,
                owner_tx_id=request.tx_id,
                resource_id=request.resource_id,
                granted=False
            )
            return None
    
    def acquire_table_lock(self, tx_id: int, table_name: str, 
                           lock_type: LockType) -> bool:
        """
        获取表级意向锁
        """
        resource = f"table:{table_name}"
        request = LockRequest(tx_id, lock_type, resource, timeout=30.0)
        
        lock = self.request_lock(request)
        return lock is not None and lock.granted
    
    def acquire_row_lock(self, tx_id: int, table_name: str, 
                         row_id: Any, lock_type: LockType) -> bool:
        """
        获取行级锁
        需要先获取表级意向锁
        """
        # 获取表级意向锁
        table_lock_type = LockType.IX if lock_type == LockType.X else LockType.IS
        if not self.acquire_table_lock(tx_id, table_name, table_lock_type):
            return False
        
        # 获取行锁
        resource = f"row:{table_name}:{row_id}"
        request = LockRequest(tx_id, lock_type, resource, timeout=30.0)
        
        lock = self.request_lock(request)
        return lock is not None and lock.granted
    
    def release_lock(self, tx_id: int, resource_id: str) -> bool:
        """释放锁"""
        with self.manager_lock:
            if resource_id not in self.lock_table:
                return False
            
            # 找到该事务持有的锁
            for lock in self.lock_table[resource_id]:
                if lock.owner_tx_id == tx_id:
                    self.lock_table[resource_id].remove(lock)
                    
                    # 更新事务锁映射
                    if tx_id in self.tx_lock_map:
                        self.tx_lock_map[tx_id].discard(resource_id)
                    
                    # 唤醒等待队列中的请求
                    self._grant_waiting_requests(resource_id)
                    return True
            
            return False
    
    def release_all_locks(self, tx_id: int):
        """释放事务持有的所有锁"""
        with self.manager_lock:
            if tx_id not in self.tx_lock_map:
                return
            
            resources = list(self.tx_lock_map[tx_id])
            for resource_id in resources:
                self.release_lock(tx_id, resource_id)
    
    def _grant_waiting_requests(self, resource_id: str):
        """授予等待队列中的请求"""
        if resource_id not in self.wait_queue:
            return
        
        # 按等待时间排序（FIFO）
        self.wait_queue[resource_id].sort(key=lambda r: r.timestamp)
        
        while self.wait_queue[resource_id]:
            request = self.wait_queue[resource_id][0]
            
            if self._can_grant(resource_id, request.lock_type, request.tx_id):
                self.wait_queue[resource_id].pop(0)
                self._grant_lock(request)
            else:
                break
    
    def upgrade_lock(self, tx_id: int, resource_id: str, 
                     new_lock_type: LockType) -> bool:
        """
        升级锁（如IS升级为IX，或S升级为X）
        """
        with self.manager_lock:
            if resource_id not in self.lock_table:
                return False
            
            # 找到该事务持有的锁
            for lock in self.lock_table[resource_id]:
                if lock.owner_tx_id == tx_id:
                    # 检查是否可以升级
                    if self._can_grant(resource_id, new_lock_type, tx_id):
                        # 释放旧锁，授予新锁
                        self.lock_table[resource_id].remove(lock)
                        new_lock = Lock(
                            lock_id=self._generate_lock_id(),
                            lock_type=new_lock_type,
                            owner_tx_id=tx_id,
                            resource_id=resource_id
                        )
                        self.lock_table[resource_id].append(new_lock)
                        return True
                    return False
            
            return False


class DeadlockDetector:
    """
    死锁检测器
    基于等待图（Wait-For Graph）检测死锁
    """
    
    def __init__(self, lock_manager: LockManager):
        self.lock_manager = lock_manager
        self.detection_interval = 1.0  # 检测间隔（秒）
        self.max_wait_time = 30.0      # 最大等待时间
    
    def build_wait_for_graph(self) -> Dict[int, Set[int]]:
        """
        构建等待图
        边 (i, j) 表示事务i等待事务j持有的资源
        """
        graph: Dict[int, Set[int]] = {}
        
        with self.lock_manager.manager_lock:
            # 遍历所有资源的锁
            for resource_id, locks in self.lock_manager.lock_table.items():
                for lock in locks:
                    if not lock.granted:
                        continue
                    
                    # lock.owner_tx_id 持有了 resource_id
                    # 找出等待该资源的事务
                    if resource_id in self.lock_manager.wait_queue:
                        for request in self.lock_manager.wait_queue[resource_id]:
                            # request.tx_id 等待 resource_id，而 lock.owner_tx_id 持有该资源
                            waiting_tx = request.tx_id
                            holding_tx = lock.owner_tx_id
                            
                            if waiting_tx != holding_tx:
                                if waiting_tx not in graph:
                                    graph[waiting_tx] = set()
                                graph[waiting_tx].add(holding_tx)
        
        return graph
    
    def detect_deadlock(self) -> Optional[List[int]]:
        """
        检测死锁（使用DFS找环）
        返回: 死锁环中的事务ID列表
        """
        graph = self.build_wait_for_graph()
        
        visited = set()
        rec_stack = []
        
        def dfs(tx_id: int, path: List[int]) -> Optional[List[int]]:
            if tx_id in rec_stack:
                # 找到环
                cycle_start = rec_stack.index(tx_id)
                return rec_stack[cycle_start:] + [tx_id]
            
            if tx_id in visited:
                return None
            
            visited.add(tx_id)
            rec_stack.append(tx_id)
            
            for neighbor in graph.get(tx_id, []):
                result = dfs(neighbor, path)
                if result:
                    return result
            
            rec_stack.pop()
            return None
        
        # 检查所有节点
        for tx_id in graph:
            if tx_id not in visited:
                cycle = dfs(tx_id, [])
                if cycle:
                    return cycle
        
        return None
    
    def check_timeout(self) -> List[int]:
        """
        检测等待超时的事务（另一种死锁检测方式）
        返回: 超时的事务ID列表
        """
        timeout_txs = []
        
        with self.lock_manager.manager_lock:
            for resource_id, queue in self.lock_manager.wait_queue.items():
                for request in queue:
                    wait_time = time.time() - request.timestamp
                    if wait_time > self.max_wait_time:
                        if request.tx_id not in timeout_txs:
                            timeout_txs.append(request.tx_id)
        
        return timeout_txs
    
    def resolve_deadlock(self, victim_txs: List[int], 
                         strategy: str = "youngest") -> int:
        """
        解决死锁
        strategy: "youngest" - 回滚最年轻的事务
                  "fewest_locks" - 回滚持有锁最少的事务
        返回: 被回滚的事务ID
        """
        if not victim_txs:
            return -1
        
        victim = -1
        
        if strategy == "youngest":
            # 选择等待时间最短的事务（最年轻）
            victim = min(victim_txs, key=lambda tx: 
                        self.lock_manager.tx_lock_map.get(tx, set()))
        
        if victim != -1:
            print(f"死锁解决: 回滚事务 {victim}")
            self.lock_manager.release_all_locks(victim)
            return victim
        
        return -1


if __name__ == "__main__":
    print("=" * 60)
    print("锁管理器演示")
    print("=" * 60)
    
    lock_mgr = LockManager()
    detector = DeadlockDetector(lock_mgr)
    
    # 场景1：正常锁获取
    print("\n--- 场景1: 正常锁获取 ---")
    print(f"Tx1 获取行锁: {lock_mgr.acquire_row_lock(1, 'orders', 100, LockType.X)}")
    print(f"Tx1 获取行锁: {lock_mgr.acquire_row_lock(1, 'orders', 200, LockType.X)}")
    print(f"Tx2 尝试获取相同行锁（应等待或失败）:")
    
    # 场景2：死锁演示
    print("\n--- 场景2: 死锁演示 ---")
    
    # 清理
    lock_mgr.release_all_locks(1)
    lock_mgr.release_all_locks(2)
    
    # T1获取row:100的X锁
    print(f"T1 获取 orders:100 X锁: {lock_mgr.acquire_row_lock(1, 'orders', 100, LockType.X)}")
    
    # T2获取orders:200的X锁
    print(f"T2 获取 orders:200 X锁: {lock_mgr.acquire_row_lock(2, 'orders', 200, LockType.X)}")
    
    # T1尝试获取orders:200（被T2持有）
    print(f"T1 尝试获取 orders:200 X锁（等待）...")
    lock_mgr.acquire_row_lock(1, 'orders', 200, LockType.X)
    
    # T2尝试获取orders:100（被T1持有）- 形成死锁
    print(f"T2 尝试获取 orders:100 X锁（等待）...")
    lock_mgr.acquire_row_lock(2, 'orders', 100, LockType.X)
    
    # 检测死锁
    print("\n检测死锁...")
    cycle = detector.detect_deadlock()
    if cycle:
        print(f"检测到死锁环: {cycle}")
        detector.resolve_deadlock(cycle[1:])
    else:
        print("未检测到死锁")
    
    print("\n锁类型层次:")
    print("  IS < IX < S < X")
    print("  获取行S锁前必须先获取表IS锁")
    print("  获取行X锁前必须先获取表IX锁")
