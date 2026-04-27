# -*- coding: utf-8 -*-
"""
算法实现：数据库算法 / lsn_log

本文件实现 lsn_log 相关的算法功能。
"""

import time
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
from collections import deque


@dataclass
class LogRecord:
    """日志记录"""
    lsn: int                    # 日志序列号
    transaction_id: int         # 事务ID
    type: str                   # 日志类型: UPDATE, COMMIT, ABORT, BEGIN
    table_id: str               # 表ID
    page_id: int                # 页面ID
    before_value: Optional[Dict[str, Any]] = None  # 修改前的值（用于Undo）
    after_value: Optional[Dict[str, Any]] = None   # 修改后的值（用于Redo）
    timestamp: float = field(default_factory=time.time)

    def __repr__(self):
        return f"LSN({self.lsn:06d}) T{self.transaction_id} {self.type} Table:{self.table_id}"


class WALog:
    """Write-Ahead Logging 系统"""

    # 日志类型常量
    TYPE_BEGIN = "BEGIN"
    TYPE_UPDATE = "UPDATE"
    TYPE_COMMIT = "COMMIT"
    TYPE_ABORT = "ABORT"
    TYPE_CHECKPOINT = "CHECKPOINT"

    def __init__(self, flush_interval: int = 10):
        """
        初始化WAL系统
        
        Args:
            flush_interval: 多少条日志后触发一次持久化（模拟）
        """
        self.log_buffer: List[LogRecord] = []      # 日志缓冲区
        self.disk_log: List[LogRecord] = []        # 已持久化的日志
        self.current_lsn = 0                        # 当前最大LSN
        self.flush_interval = flush_interval        # 刷新间隔
        
        # 事务状态表
        self.transaction_status: Dict[int, str] = {}  # tid -> status
        self.transaction_first_lsn: Dict[int, int] = {}  # tid -> 起始LSN
        
        # 脏页表（用于检查点）
        self.dirty_pages: Dict[int, int] = {}  # page_id -> 首次修改的LSN
        
        # 统计
        self.stats = {
            "total_log_records": 0,
            "total_flushes": 0,
            "total_bytes_written": 0
        }

    def _generate_lsn(self) -> int:
        """生成下一个LSN"""
        self.current_lsn += 1
        return self.current_lsn

    def begin_transaction(self, transaction_id: int):
        """
        事务开始
        
        Args:
            transaction_id: 事务ID
        """
        lsn = self._generate_lsn()
        record = LogRecord(
            lsn=lsn,
            transaction_id=transaction_id,
            type=self.TYPE_BEGIN,
            table_id="",
            page_id=0
        )
        
        self.log_buffer.append(record)
        self.transaction_status[transaction_id] = "ACTIVE"
        self.transaction_first_lsn[transaction_id] = lsn
        self.stats["total_log_records"] += 1

    def log_update(self, transaction_id: int, table_id: str, page_id: int,
                   before_value: Dict[str, Any], after_value: Dict[str, Any]):
        """
        记录更新操作
        
        Args:
            transaction_id: 事务ID
            table_id: 表ID
            page_id: 页面ID
            before_value: 修改前的值
            after_value: 修改后的值
        """
        lsn = self._generate_lsn()
        record = LogRecord(
            lsn=lsn,
            transaction_id=transaction_id,
            type=self.TYPE_UPDATE,
            table_id=table_id,
            page_id=page_id,
            before_value=before_value,
            after_value=after_value
        )
        
        self.log_buffer.append(record)
        self.stats["total_log_records"] += 1
        
        # 记录脏页
        if page_id not in self.dirty_pages:
            self.dirty_pages[page_id] = lsn
        
        # 检查是否需要刷新
        if len(self.log_buffer) >= self.flush_interval:
            self.flush()

    def commit(self, transaction_id: int) -> bool:
        """
        事务提交
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            是否成功提交
        """
        if transaction_id not in self.transaction_status:
            return False
        
        if self.transaction_status[transaction_id] != "ACTIVE":
            return False
        
        lsn = self._generate_lsn()
        record = LogRecord(
            lsn=lsn,
            transaction_id=transaction_id,
            type=self.TYPE_COMMIT,
            table_id="",
            page_id=0
        )
        
        self.log_buffer.append(record)
        self.transaction_status[transaction_id] = "COMMITTED"
        self.stats["total_log_records"] += 1
        
        # 提交时强制刷新日志
        self.flush()
        
        return True

    def abort(self, transaction_id: int) -> List[LogRecord]:
        """
        事务中止（回滚）
        
        Args:
            transaction_id: 事务ID
            
        Returns:
            需要回滚的日志记录列表
        """
        if transaction_id not in self.transaction_status:
            return []
        
        # 获取该事务的所有日志记录
        undo_list = []
        for record in self.log_buffer:
            if record.transaction_id == transaction_id and record.type == self.TYPE_UPDATE:
                undo_list.append(record)
        
        # 按LSN降序回滚（从新到旧）
        undo_list.reverse()
        
        # 添加ABORT记录
        lsn = self._generate_lsn()
        abort_record = LogRecord(
            lsn=lsn,
            transaction_id=transaction_id,
            type=self.TYPE_ABORT,
            table_id="",
            page_id=0
        )
        self.log_buffer.append(abort_record)
        self.transaction_status[transaction_id] = "ABORTED"
        self.stats["total_log_records"] += 1
        
        # 回滚时也需要刷新
        self.flush()
        
        return undo_list

    def flush(self):
        """
        将日志缓冲区刷新到磁盘（模拟）
        """
        if not self.log_buffer:
            return
        
        # 模拟将日志写入磁盘
        self.disk_log.extend(self.log_buffer)
        bytes_written = sum(self._estimate_record_size(r) for r in self.log_buffer)
        
        self.stats["total_flushes"] += 1
        self.stats["total_bytes_written"] += bytes_written
        
        # 清空缓冲区
        self.log_buffer.clear()

    def _estimate_record_size(self, record: LogRecord) -> int:
        """估算日志记录大小（字节）"""
        base_size = 50  # 基本字段大小
        before_size = len(str(record.before_value)) if record.before_value else 0
        after_size = len(str(record.after_value)) if record.after_value else 0
        return base_size + before_size + after_size

    def checkpoint(self) -> Tuple[int, List[int]]:
        """
        创建检查点
        
        Returns:
            (检查点LSN, 活跃事务列表)
        """
        lsn = self._generate_lsn()
        record = LogRecord(
            lsn=lsn,
            transaction_id=0,
            type=self.TYPE_CHECKPOINT,
            table_id="",
            page_id=0
        )
        
        self.log_buffer.append(record)
        self.stats["total_log_records"] += 1
        
        # 获取活跃事务列表
        active_transactions = [
            tid for tid, status in self.transaction_status.items()
            if status == "ACTIVE"
        ]
        
        # 刷新检查点
        self.flush()
        
        # 清空脏页表（简化）
        self.dirty_pages.clear()
        
        return lsn, active_transactions

    def recovery_analysis(self) -> Tuple[List[int], List[int]]:
        """
        崩溃恢复的分析阶段
        确定需要重做和回滚的事务
        
        Returns:
            (需要重做的事务列表, 需要回滚的事务列表)
        """
        redo_transactions = []
        undo_transactions = []
        
        # 扫描日志
        for record in self.disk_log:
            if record.type == self.TYPE_BEGIN:
                if record.transaction_id not in self.transaction_status:
                    undo_transactions.append(record.transaction_id)
                self.transaction_status[record.transaction_id] = "ACTIVE"
            
            elif record.type == self.TYPE_COMMIT:
                if record.transaction_id in undo_transactions:
                    undo_transactions.remove(record.transaction_id)
                redo_transactions.append(record.transaction_id)
                self.transaction_status[record.transaction_id] = "COMMITTED"
            
            elif record.type == self.TYPE_ABORT:
                if record.transaction_id in undo_transactions:
                    undo_transactions.remove(record.transaction_id)
                redo_transactions.append(record.transaction_id)
                self.transaction_status[record.transaction_id] = "ABORTED"
        
        return redo_transactions, undo_transactions

    def get_log_status(self) -> dict:
        """获取日志系统状态"""
        return {
            "current_lsn": self.current_lsn,
            "buffered_records": len(self.log_buffer),
            "disk_records": len(self.disk_log),
            "dirty_pages": len(self.dirty_pages),
            "active_transactions": sum(1 for s in self.transaction_status.values() if s == "ACTIVE"),
            "stats": self.stats
        }

    def print_recent_logs(self, count: int = 10):
        """打印最近的日志记录"""
        all_logs = self.disk_log[-count:]
        print(f"\n最近的 {len(all_logs)} 条日志记录:")
        print(f"{'LSN':<12}{'事务ID':<10}{'类型':<12}{'表':<10}{'页面ID'}")
        print("-" * 60)
        
        for record in all_logs:
            print(f"  {record.lsn:<10}{record.transaction_id:<10}{record.type:<12}{record.table_id:<10}{record.page_id}")


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("=" * 70)
    print("日志序列号（LSN）与Write-Ahead Logging测试")
    print("=" * 70)

    # 创建WAL系统
    wal = WALog(flush_interval=3)

    # 模拟事务场景
    print("\n--- 场景1：正常提交的事务 ---")
    
    wal.begin_transaction(1)
    print(f"  T1 开始，first_lsn={wal.transaction_first_lsn[1]}")
    
    wal.log_update(1, "users", 100, {"name": "Alice"}, {"name": "Alice Smith"})
    print(f"  T1 更新页面100")
    
    wal.log_update(1, "users", 101, {"balance": 1000}, {"balance": 900})
    print(f"  T1 更新页面101")
    
    wal.commit(1)
    print(f"  T1 提交")

    print("\n--- 场景2：需要回滚的事务 ---")
    
    wal.begin_transaction(2)
    wal.log_update(2, "orders", 200, {"status": "pending"}, {"status": "shipped"})
    wal.log_update(2, "orders", 201, {"status": "pending"}, {"status": "shipped"})
    print(f"  T2 更新了两个订单状态")
    
    undo_list = wal.abort(2)
    print(f"  T2 中止，需要回滚 {len(undo_list)} 条记录")

    print("\n--- 场景3：并发事务 ---")
    
    wal.begin_transaction(3)
    wal.begin_transaction(4)
    wal.begin_transaction(5)
    
    wal.log_update(3, "products", 300, {"stock": 50}, {"stock": 45})
    wal.log_update(4, "products", 301, {"stock": 30}, {"stock": 25})
    wal.log_update(5, "products", 302, {"stock": 20}, {"stock": 15})
    
    wal.commit(4)  # T4先提交
    print(f"  T3, T4, T5 并发执行，T4先提交")
    
    wal.commit(3)
    wal.abort(5)   # T5回滚
    print(f"  T3提交，T5回滚")

    # 检查点
    print("\n--- 场景4：检查点 ---")
    checkpoint_lsn, active = wal.checkpoint()
    print(f"  检查点创建于 LSN={checkpoint_lsn}")
    print(f"  检查点时活跃事务: {active}")

    # 状态和统计
    print("\n--- 系统状态 ---")
    status = wal.get_log_status()
    print(f"  当前LSN: {status['current_lsn']}")
    print(f"  缓冲区记录: {status['buffered_records']}")
    print(f"  磁盘记录: {status['disk_records']}")
    print(f"  脏页数: {status['dirty_pages']}")
    print(f"  活跃事务: {status['active_transactions']}")
    print(f"  统计: {status['stats']}")

    # 打印日志
    wal.print_recent_logs(10)

    print("\n" + "=" * 70)
    print("复杂度: O(1) 追加写，O(N) 恢复分析")
    print("=" * 70)
