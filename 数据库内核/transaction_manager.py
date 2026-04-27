# -*- coding: utf-8 -*-
"""
算法实现：数据库内核 / transaction_manager

本文件实现 transaction_manager 相关的算法功能。
"""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import IntEnum
import time

# 事务状态
class TransactionState(IntEnum):
    ACTIVE = 1
    PREPARING = 2
    PREPARED = 3
    COMMITTED = 4
    ABORTED = 5
    ROLLING_BACK = 6


@dataclass
class Transaction:
    """事务对象"""
    tx_id: int                    # 事务ID
    state: TransactionState = TransactionState.ACTIVE
    start_time: float = field(default_factory=time.time)
    commit_time: float = 0.0
    last_operation_time: float = field(default_factory=time.time)
    operations: List['Operation'] = field(default_factory=list)
    isolation_level: str = "snapshot"
    
    def __repr__(self):
        return f"Tx({self.tx_id}, {self.state.name})"


@dataclass
class Operation:
    """操作记录"""
    op_type: str          # "READ" / "WRITE" / "UPDATE" / "DELETE"
    table_name: str
    row_id: Any
    before_image: Any = None
    after_image: Any = None
    timestamp: float = field(default_factory=time.time)
    lsn: int = -1        # 日志序列号


@dataclass
class LogRecord:
    """日志记录（ARIES格式）"""
    lsn: int              # 日志序列号
    tx_id: int            # 事务ID
    log_type: str         # "BEGIN" / "UPDATE" / "COMMIT" / "ABORT" / "CHECKPOINT"
    prev_lsn: int         # 前一个LSN（组成Undo链）
    undo_next_lsn: int    # 下一条需要撤销的日志（用于ARIES的撤销）
    page_id: int = -1     # 关联的页ID
    before_image: Any = None
    after_image: Any = None
    timestamp: float = field(default_factory=time.time)
    
    def __repr__(self):
        return f"Log(lsn={self.lsn}, tx={self.tx_id}, type={self.log_type})"


class TransactionLogManager:
    """
    事务日志管理器（基于ARIES格式）
    """
    
    def __init__(self, log_file: str = "transaction.log"):
        self.log_file = log_file
        self.current_lsn = 0
        self.log_buffer: List[LogRecord] = []
        self.transaction_log_chain: Dict[int, List[int]] = {}  # tx_id -> [lsn列表]
    
    def write_log(self, log: LogRecord) -> int:
        """写入日志记录"""
        log.lsn = self.current_lsn
        self.current_lsn += 1
        
        self.log_buffer.append(log)
        
        # 更新事务的日志链
        if log.tx_id not in self.transaction_log_chain:
            self.transaction_log_chain[log.tx_id] = []
        self.transaction_log_chain[log.tx_id].append(log.lsn)
        
        # 模拟刷盘（当缓冲区满时）
        if len(self.log_buffer) >= 100:
            self._flush_to_disk()
        
        return log.lsn
    
    def _flush_to_disk(self):
        """模拟刷盘到磁盘"""
        # 实际实现中应该写入磁盘并调用fsync
        self.log_buffer.clear()
    
    def force_flush(self):
        """强制刷盘"""
        self._flush_to_disk()
    
    def get_transaction_logs(self, tx_id: int) -> List[LogRecord]:
        """获取事务的所有日志"""
        lsns = self.transaction_log_chain.get(tx_id, [])
        return [log for log in self.log_buffer if log.lsn in lsns]
    
    def write_begin(self, tx_id: int) -> LogRecord:
        """写入BEGIN日志"""
        log = LogRecord(
            lsn=-1,
            tx_id=tx_id,
            log_type="BEGIN",
            prev_lsn=-1,
            undo_next_lsn=-1
        )
        lsn = self.write_log(log)
        return log
    
    def write_update(self, tx_id: int, prev_lsn: int, 
                     page_id: int, before: Any, after: Any) -> LogRecord:
        """写入UPDATE日志"""
        log = LogRecord(
            lsn=-1,
            tx_id=tx_id,
            log_type="UPDATE",
            prev_lsn=prev_lsn,
            undo_next_lsn=-1,  # 暂时未知，之后更新
            page_id=page_id,
            before_image=before,
            after_image=after
        )
        lsn = self.write_log(log)
        return log
    
    def write_commit(self, tx_id: int) -> LogRecord:
        """写入COMMIT日志"""
        log = LogRecord(
            lsn=-1,
            tx_id=tx_id,
            log_type="COMMIT",
            prev_lsn=self.transaction_log_chain.get(tx_id, [-1])[-1],
            undo_next_lsn=-1
        )
        lsn = self.write_log(log)
        self.force_flush()  # COMMIT必须持久化
        return log
    
    def write_abort(self, tx_id: int) -> LogRecord:
        """写入ABORT日志"""
        log = LogRecord(
            lsn=-1,
            tx_id=tx_id,
            log_type="ABORT",
            prev_lsn=self.transaction_log_chain.get(tx_id, [-1])[-1],
            undo_next_lsn=-1
        )
        lsn = self.write_log(log)
        return log


class TransactionManager:
    """
    事务管理器
    提供ACID保证
    """
    
    def __init__(self):
        self.active_transactions: Dict[int, Transaction] = {}
        self.next_tx_id = 1
        self.log_manager = TransactionLogManager()
        self.lock_manager = None  # 可以注入锁管理器
    
    def begin_transaction(self, isolation_level: str = "snapshot") -> Transaction:
        """开始新事务"""
        tx = Transaction(
            tx_id=self.next_tx_id,
            isolation_level=isolation_level
        )
        self.next_tx_id += 1
        
        self.active_transactions[tx.tx_id] = tx
        self.log_manager.write_begin(tx.tx_id)
        
        return tx
    
    def read_row(self, tx: Transaction, table: str, row_id: Any) -> Optional[Any]:
        """
        读取行
        实现MVCC快照读
        """
        # 简化实现，返回None表示读取成功但无数据
        # 实际需要从存储引擎读取
        return None
    
    def write_row(self, tx: Transaction, table: str, row_id: Any, 
                  new_value: Any) -> bool:
        """
        写入行（创建新版本）
        """
        if tx.state != TransactionState.ACTIVE:
            return False
        
        # 记录操作
        op = Operation(
            op_type="WRITE",
            table_name=table,
            row_id=row_id,
            after_image=new_value
        )
        tx.operations.append(op)
        
        # 获取前一个LSN
        prev_lsn = -1
        if tx.operations:
            prev_lsn = tx.operations[-1].lsn
        
        # 写入日志
        log = self.log_manager.write_update(
            tx_id=tx.tx_id,
            prev_lsn=prev_lsn,
            page_id=hash(f"{table}:{row_id}") % 10000,
            before=None,
            after=new_value
        )
        
        op.lsn = log.lsn
        
        # 更新undo_next指针（形成撤销链）
        if len(tx.operations) >= 2:
            tx.operations[-2].undo_next_lsn = log.lsn
        
        return True
    
    def commit_transaction(self, tx: Transaction) -> bool:
        """
        提交事务
        1. 写入COMMIT日志
        2. 释放锁
        3. 更新事务状态
        """
        if tx.tx_id not in self.active_transactions:
            return False
        
        if tx.state != TransactionState.ACTIVE:
            return False
        
        # 准备提交
        tx.state = TransactionState.PREPARING
        
        # 写入COMMIT日志
        self.log_manager.write_commit(tx.tx_id)
        
        # 更新事务状态
        tx.state = TransactionState.COMMITTED
        tx.commit_time = time.time()
        
        # 释放锁（如果使用锁并发控制）
        if self.lock_manager:
            # 释放事务持有的所有锁
            pass
        
        # 从活跃事务中移除
        self.active_transactions.pop(tx.tx_id, None)
        
        print(f"事务 {tx.tx_id} 已提交")
        return True
    
    def abort_transaction(self, tx: Transaction) -> bool:
        """
        中止事务（回滚）
        使用Undo链执行回滚
        """
        if tx.tx_id not in self.active_transactions:
            return False
        
        tx.state = TransactionState.ROLLING_BACK
        
        # 写入ABORT日志
        self.log_manager.write_abort(tx.tx_id)
        
        # 从后向前回滚
        for op in reversed(tx.operations):
            if op.op_type == "WRITE" and op.before_image is not None:
                # 应用before_image
                pass  # 实际实现需要更新存储
        
        tx.state = TransactionState.ABORTED
        self.active_transactions.pop(tx.tx_id, None)
        
        print(f"事务 {tx.tx_id} 已回滚")
        return True
    
    def get_transaction_state(self, tx_id: int) -> Optional[TransactionState]:
        """获取事务状态"""
        tx = self.active_transactions.get(tx_id)
        if tx:
            return tx.state
        return None


class LockManager:
    """
    简化的锁管理器
    用于事务的并发控制
    """
    
    def __init__(self):
        self.locks: Dict[str, Dict[int, str]] = {}  # resource -> {tx_id -> lock_type}
        self.wait_queue: Dict[str, List[Tuple[int, str]]] = {}  # resource -> [(tx_id, lock_type)]
    
    def acquire_lock(self, tx_id: int, resource: str, lock_type: str = "X") -> bool:
        """获取锁"""
        if resource not in self.locks:
            self.locks[resource] = {}
        
        if not self.locks[resource]:
            self.locks[resource][tx_id] = lock_type
            return True
        
        # 检查是否可以获取
        for held_tx, held_type in self.locks[resource].items():
            if held_tx == tx_id:
                return True  # 已持有
            
            # 检查锁冲突
            if lock_type == "X" or held_type == "X":
                # 需要等待，加入等待队列
                if resource not in self.wait_queue:
                    self.wait_queue[resource] = []
                self.wait_queue[resource].append((tx_id, lock_type))
                return False
        
        self.locks[resource][tx_id] = lock_type
        return True
    
    def release_lock(self, tx_id: int, resource: str):
        """释放锁"""
        if resource in self.locks and tx_id in self.locks[resource]:
            del self.locks[resource][tx_id]
            
            # 唤醒等待队列中的事务
            if resource in self.wait_queue and self.wait_queue[resource]:
                next_tx, next_type = self.wait_queue[resource].pop(0)
                self.locks[resource][next_tx] = next_type


if __name__ == "__main__":
    print("=" * 60)
    print("事务管理器演示")
    print("=" * 60)
    
    # 创建事务管理器
    tm = TransactionManager()
    
    # 开始事务T1
    print("\n--- 事务T1 ---")
    tx1 = tm.begin_transaction()
    print(f"T1 开始: {tx1}")
    
    # T1 执行操作
    tm.write_row(tx1, "orders", 1, {"amount": 100, "status": "new"})
    print(f"T1 写入 orders:1")
    
    # 开始事务T2
    print("\n--- 事务T2 ---")
    tx2 = tm.begin_transaction()
    print(f"T2 开始: {tx2}")
    
    # T2 尝试读取相同行
    print(f"T2 尝试读取 orders:1")
    
    # T1 提交
    print("\n--- T1 提交 ---")
    tm.commit_transaction(tx1)
    
    # T2 提交
    print("\n--- T2 提交 ---")
    tm.commit_transaction(tx2)
    
    # 演示中止场景
    print("\n--- 事务中止演示 ---")
    tx3 = tm.begin_transaction()
    print(f"T3 开始: {tx3}")
    
    tm.write_row(tx3, "accounts", 100, {"balance": 500})
    print(f"T3 写入 accounts:100")
    
    # 中止T3
    tm.abort_transaction(tx3)
    
    # 展示事务状态
    print(f"\nT3 状态: {tm.get_transaction_state(tx3.tx_id)}")
    
    print("\nACID保证:")
    print("  Atomicity: 所有操作要么全部提交，要么全部回滚")
    print("  Consistency: 事务执行前后数据库保持一致状态")
    print("  Isolation: 并发事务相互隔离（快照隔离）")
    print("  Durability: 提交的事务，其修改永久保存")
