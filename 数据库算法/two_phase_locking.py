# -*- coding: utf-8 -*-
"""
算法实现：数据库算法 / two_phase_locking

本文件实现 two_phase_locking 相关的算法功能。
"""

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
import time


@dataclass
class LockRequest:
    """锁请求"""
    transaction_id: int       # 事务ID
    resource_id: str          # 资源ID（如表、行）
    lock_mode: str            # 锁模式: SHARED, EXCLUSIVE
    timestamp: float = field(default_factory=time.time)


class LockManager:
    """锁管理器"""

    # 锁模式
    LOCK_SHARED = "SHARED"           # 共享锁（S锁）
    LOCK_EXCLUSIVE = "EXCLUSIVE"     # 排他锁（X锁）

    def __init__(self):
        # 资源锁表: resource_id -> {lock_mode: [transaction_ids]}
        self.lock_table: Dict[str, Dict[str, Set[int]]] = defaultdict(
            lambda: {self.LOCK_SHARED: set(), self.LOCK_EXCLUSIVE: set()}
        )
        
        # 事务等待图（用于死锁检测）
        self.wait_graph: Dict[int, Set[int]] = defaultdict(set)
        
        # 等待队列
        self.wait_queue: List[LockRequest] = []

    def request_lock(self, transaction_id: int, resource_id: str,
                    lock_mode: str) -> Tuple[bool, Optional[str]]:
        """
        请求锁
        
        Args:
            transaction_id: 事务ID
            resource_id: 资源ID
            lock_mode: 锁模式
            
        Returns:
            (是否成功, 失败原因)
        """
        resource_locks = self.lock_table[resource_id]
        
        # 检查是否满足锁兼容性
        compatible, blocker = self._check_compatibility(
            transaction_id, resource_id, lock_mode
        )
        
        if compatible:
            # 授予锁
            resource_locks[lock_mode].add(transaction_id)
            return True, None
        else:
            # 添加到等待图（可能导致死锁）
            self.wait_graph[transaction_id].add(blocker)
            return False, f"blocked_by_T{blocker}"

    def release_lock(self, transaction_id: int, resource_id: str,
                    lock_mode: Optional[str] = None) -> bool:
        """
        释放锁
        
        Args:
            transaction_id: 事务ID
            resource_id: 资源ID
            lock_mode: 锁模式，None表示释放所有该事务持有的该资源锁
            
        Returns:
            是否成功
        """
        resource_locks = self.lock_table[resource_id]
        
        if lock_mode:
            # 释放特定模式的锁
            if transaction_id in resource_locks[lock_mode]:
                resource_locks[lock_mode].discard(transaction_id)
        else:
            # 释放所有该事务持有的该资源锁
            for mode in [self.LOCK_SHARED, self.LOCK_EXCLUSIVE]:
                resource_locks[mode].discard(transaction_id)
        
        # 从等待图中移除
        if transaction_id in self.wait_graph:
            del self.wait_graph[transaction_id]
        
        # 更新被阻塞事务的等待图
        for txn, wait_for in list(self.wait_graph.items()):
            wait_for.discard(transaction_id)
        
        return True

    def release_all_locks(self, transaction_id: int) -> List[Tuple[str, str]]:
        """
        释放事务持有的所有锁
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            释放的锁列表 [(resource_id, lock_mode), ...]
        """
        released = []
        
        for resource_id, resource_locks in list(self.lock_table.items()):
            for lock_mode in [self.LOCK_SHARED, self.LOCK_EXCLUSIVE]:
                if transaction_id in resource_locks[lock_mode]:
                    resource_locks[lock_mode].discard(transaction_id)
                    released.append((resource_id, lock_mode))
        
        # 从等待图中移除
        if transaction_id in self.wait_graph:
            del self.wait_graph[transaction_id]
        
        return released

    def _check_compatibility(self, transaction_id: int, resource_id: str,
                           lock_mode: str) -> Tuple[bool, Optional[int]]:
        """
        检查锁兼容性
        
        Returns:
            (是否兼容, 阻塞者事务ID)
        """
        resource_locks = self.lock_table[resource_id]
        
        if lock_mode == self.LOCK_SHARED:
            # S锁：与S锁兼容，与X锁不兼容
            if resource_locks[self.LOCK_EXCLUSIVE]:
                # 有X锁存在
                return False, next(iter(resource_locks[self.LOCK_EXCLUSIVE]))
            return True, None
        
        elif lock_mode == self.LOCK_EXCLUSIVE:
            # X锁：与任何锁都不兼容
            if resource_locks[self.LOCK_EXCLUSIVE] or resource_locks[self.LOCK_SHARED]:
                # 有锁存在
                if resource_locks[self.LOCK_EXCLUSIVE]:
                    return False, next(iter(resource_locks[self.LOCK_EXCLUSIVE]))
                elif resource_locks[self.LOCK_SHARED]:
                    return False, next(iter(resource_locks[self.LOCK_SHARED]))
            return True, None
        
        return False, None

    def detect_deadlock(self) -> Optional[List[int]]:
        """
        检测死锁（使用DFS检测环）
        
        Returns:
            死锁环中的事务列表，None表示无死锁
        """
        visited = set()
        rec_stack = set()
        
        def dfs(txn: int, path: List[int]) -> Optional[List[int]]:
            visited.add(txn)
            rec_stack.add(txn)
            path.append(txn)
            
            for wait_for in self.wait_graph.get(txn, []):
                if wait_for not in visited:
                    result = dfs(wait_for, path[:])
                    if result:
                        return result
                elif wait_for in rec_stack:
                    # 找到环
                    cycle_start = path.index(wait_for)
                    return path[cycle_start:]
            
            rec_stack.remove(txn)
            return None
        
        for txn in self.wait_graph:
            if txn not in visited:
                result = dfs(txn, [])
                if result:
                    return result
        
        return None

    def get_lock_status(self, resource_id: str) -> dict:
        """获取资源的锁状态"""
        if resource_id not in self.lock_table:
            return {"shared": [], "exclusive": []}
        
        resource_locks = self.lock_table[resource_id]
        return {
            "shared": list(resource_locks[self.LOCK_SHARED]),
            "exclusive": list(resource_locks[self.LOCK_EXCLUSIVE])
        }


class TwoPhaseLocking:
    """两阶段锁协议"""

    # 事务状态
    STATUS_ACTIVE = "ACTIVE"
    STATUS_GROWING = "GROWING"
    STATUS_SHRINKING = "SHRINKING"
    STATUS_COMMITTED = "COMMITTED"
    STATUS_ABORTED = "ABORTED"

    def __init__(self, strict: bool = True, deadlock_detection: bool = True):
        """
        初始化2PL
        
        Args:
            strict: 严格2PL（排他锁持有到事务结束）
            deadlock_detection: 是否启用死锁检测
        """
        self.lock_manager = LockManager()
        self.strict = strict
        self.deadlock_detection = deadlock_detection
        
        # 事务状态
        self.transactions: Dict[int, str] = {}
        
        # 事务持有的锁
        self.transaction_locks: Dict[int, List[Tuple[str, str]]] = defaultdict(list)
        
        # 统计
        self.stats = {
            "locks_acquired": 0,
            "locks_released": 0,
            "deadlocks_detected": 0,
            "aborts_due_to_deadlock": 0
        }

    def begin_transaction(self, transaction_id: int):
        """开始事务"""
        self.transactions[transaction_id] = self.STATUS_GROWING

    def acquire_lock(self, transaction_id: int, resource_id: str,
                    lock_mode: str) -> Tuple[bool, Optional[str]]:
        """
        获取锁（仅在扩展阶段有效）
        
        Args:
            transaction_id: 事务ID
            resource_id: 资源ID
            lock_mode: 锁模式
            
        Returns:
            (是否成功, 错误信息)
        """
        if self.transactions.get(transaction_id) == self.STATUS_SHRINKING:
            return False, "Cannot acquire lock in shrinking phase"
        
        self.transactions[transaction_id] = self.STATUS_GROWING
        
        success, blocker = self.lock_manager.request_lock(
            transaction_id, resource_id, lock_mode
        )
        
        if success:
            self.transaction_locks[transaction_id].append((resource_id, lock_mode))
            self.stats["locks_acquired"] += 1
            
            # 死锁检测
            if self.deadlock_detection:
                deadlock = self.lock_manager.detect_deadlock()
                if deadlock:
                    self.stats["deadlocks_detected"] += 1
                    return False, f"Deadlock detected: {deadlock}"
        
        return success, blocker

    def release_lock(self, transaction_id: int, resource_id: str) -> bool:
        """
        释放锁（进入收缩阶段）
        
        Args:
            transaction_id: 事务ID
            resource_id: 资源ID
            
        Returns:
            是否成功
        """
        if self.transactions.get(transaction_id) == self.STATUS_SHRINKING:
            return False
        
        # 进入收缩阶段
        self.transactions[transaction_id] = self.STATUS_SHRINKING
        
        released = self.lock_manager.release_lock(transaction_id, resource_id)
        
        if released:
            # 从事务锁列表中移除
            locks = self.transaction_locks[transaction_id]
            self.transaction_locks[transaction_id] = [
                (rid, mode) for rid, mode in locks if rid != resource_id
            ]
            self.stats["locks_released"] += 1
        
        return released

    def commit(self, transaction_id: int) -> bool:
        """
        提交事务
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            是否成功
        """
        if transaction_id not in self.transactions:
            return False
        
        # 严格2PL：所有锁在事务结束时释放
        if self.strict:
            released = self.lock_manager.release_all_locks(transaction_id)
            self.transaction_locks[transaction_id].clear()
            self.stats["locks_released"] += len(released)
        
        self.transactions[transaction_id] = self.STATUS_COMMITTED
        return True

    def abort(self, transaction_id: int) -> bool:
        """
        中止事务
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            是否成功
        """
        if transaction_id not in self.transactions:
            return False
        
        # 释放所有锁
        released = self.lock_manager.release_all_locks(transaction_id)
        self.transaction_locks[transaction_id].clear()
        self.stats["locks_released"] += len(released)
        
        self.transactions[transaction_id] = self.STATUS_ABORTED
        
        if released:
            self.stats["aborts_due_to_deadlock"] += 1
        
        return True

    def read(self, transaction_id: int, resource_id: str) -> bool:
        """
        读取资源（获取S锁）
        
        Args:
            transaction_id: 事务ID
            resource_id: 资源ID
            
        Returns:
            是否成功获取锁
        """
        success, error = self.acquire_lock(
            transaction_id, resource_id, self.lock_manager.LOCK_SHARED
        )
        return success

    def write(self, transaction_id: int, resource_id: str) -> bool:
        """
        写入资源（获取X锁）
        
        Args:
            transaction_id: 事务ID
            resource_id: 资源ID
            
        Returns:
            是否成功获取锁
        """
        success, error = self.acquire_lock(
            transaction_id, resource_id, self.lock_manager.LOCK_EXCLUSIVE
        )
        return success

    def get_transaction_status(self, transaction_id: int) -> Optional[str]:
        """获取事务状态"""
        return self.transactions.get(transaction_id)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("=" * 70)
    print("两阶段锁协议（2PL）测试")
    print("=" * 70)

    # 创建2PL系统
    two_pl = TwoPhaseLocking(strict=True, deadlock_detection=True)

    # 场景1：正常事务流程
    print("\n--- 场景1：正常事务流程 ---")
    
    two_pl.begin_transaction(1)
    print(f"  T1 开始")
    
    two_pl.write(1, "row_A")  # 获取X锁
    print(f"  T1 获取 row_A 的X锁")
    
    two_pl.write(1, "row_B")
    print(f"  T1 获取 row_B 的X锁")
    
    two_pl.commit(1)
    print(f"  T1 提交，释放所有锁")

    # 场景2：锁争用
    print("\n--- 场景2：锁争用 ---")
    
    two_pl.begin_transaction(2)
    two_pl.begin_transaction(3)
    
    two_pl.write(2, "row_X")
    print(f"  T2 获取 row_X 的X锁")
    
    success = two_pl.read(3, "row_X")  # 尝试S锁
    print(f"  T3 尝试读取 row_X: {'成功' if success else '阻塞'}")
    
    two_pl.commit(2)
    print(f"  T2 提交，释放X锁")
    
    # T3现在可以获取S锁了
    status = two_pl.get_transaction_status(3)
    print(f"  T3 状态: {status}")

    # 场景3：死锁
    print("\n--- 场景3：死锁检测 ---")
    
    two_pl.begin_transaction(4)
    two_pl.begin_transaction(5)
    
    two_pl.write(4, "resource_1")
    print(f"  T4 获取 resource_1 的X锁")
    
    two_pl.write(5, "resource_2")
    print(f"  T5 获取 resource_2 的X锁")
    
    # 尝试获取对方持有的锁
    print(f"  T4 尝试获取 resource_2...")
    success_4 = two_pl.write(4, "resource_2")
    
    print(f"  T5 尝试获取 resource_1...")
    success_5 = two_pl.write(5, "resource_1")
    
    if not success_4 and not success_5:
        print("  ⚠ 检测到死锁！")
        
        # 死锁检测
        deadlock = two_pl.lock_manager.detect_deadlock()
        if deadlock:
            print(f"  死锁环: T{' -> T'.join(map(str, deadlock))}")
            
            # 选择一个事务中止（通常是最年轻的）
            victim = max(deadlock)
            print(f"  选择 T{victim} 作为牺牲者")
            two_pl.abort(victim)

    # 场景4：严格2PL
    print("\n--- 场景4：严格2PL ---")
    
    two_pl.begin_transaction(6)
    two_pl.write(6, "account")
    print(f"  T6 获取 account 的X锁")
    
    # 在提交前尝试释放锁
    released = two_pl.release_lock(6, "account")
    print(f"  尝试在提交前释放锁: {'成功' if released else '失败（严格2PL不允许）'}")
    
    two_pl.commit(6)
    print(f"  T6 提交，锁自动释放")

    # 场景5：收缩阶段不能再获取锁
    print("\n--- 场景5：收缩阶段规则 ---")
    
    two_pl.begin_transaction(7)
    two_pl.write(7, "table_A")
    print(f"  T7 获取 table_A 的X锁")
    
    two_pl.release_lock(7, "table_A")  # 进入收缩阶段
    print(f"  T7 释放 table_A，进入收缩阶段")
    
    success = two_pl.write(7, "table_B")
    print(f"  T7 尝试获取 table_B: {'成功' if success else '失败（收缩阶段不能获取锁）'}")

    print("\n" + "=" * 70)
    print("统计:", two_pl.stats)
    print("=" * 70)
