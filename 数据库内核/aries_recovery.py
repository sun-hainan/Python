# -*- coding: utf-8 -*-
"""
算法实现：数据库内核 / aries_recovery

本文件实现 aries_recovery 相关的算法功能。
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import IntEnum
import time

# 日志类型枚举
class LogType(IntEnum):
    UPDATE = 1          # 更新日志
    COMMIT = 2          # 提交日志
    ABORT = 3           # 中止日志
    CHECKPOINT = 4      # 检查点日志
    BEGIN = 5           # 事务开始


@dataclass
class LogRecord:
    """日志记录"""
    lsn: int            # 日志序列号（Log Sequence Number）
    tx_id: int          # 事务ID
    log_type: LogType   # 日志类型
    page_id: int = -1   # 受影响的页ID
    undo_lsn: int = -1  # 撤销时需要的上一条日志（用于撤销链）
    before_image: Any = None  # 更新前的镜像
    after_image: Any = None   # 更新后的镜像
    timestamp: float = field(default_factory=time.time)
    
    def __repr__(self):
        return f"Log(lsn={self.lsn}, tx={self.tx_id}, type={self.log_type.name}, page={self.page_id})"


class WALManager:
    """
    预写日志管理器（Write-Ahead Log Manager）
    确保日志在数据页修改前先写入磁盘
    """
    
    def __init__(self, log_file: str = "wal.log"):
        self.log_file = log_file          # 日志文件
        self.log_buffer: List[LogRecord] = []  # 日志缓冲区
        self.persistent_lsn: int = 0      # 已持久化的LSN
        self.current_lsn: int = 0         # 当前LSN
        
    def append_log(self, log: LogRecord) -> int:
        """
        追加日志记录
        返回: 分配的LSN
        """
        log.lsn = self.current_lsn
        self.current_lsn += 1
        self.log_buffer.append(log)
        return log.lsn
    
    def write_log(self, log: LogRecord) -> bool:
        """
        写入日志（WAL规则：必须先写日志再修改页）
        """
        # 追加到缓冲区
        lsn = self.append_log(log)
        
        # 模拟刷盘（实际中需要调用fsync）
        if len(self.log_buffer) >= 10:  # 缓冲区满或强制刷盘
            self._flush_to_disk()
        
        return True
    
    def _flush_to_disk(self):
        """模拟刷盘到磁盘"""
        # 实际实现中应该写入磁盘
        self.persistent_lsn = self.current_lsn - 1
    
    def force_flush(self):
        """强制刷盘"""
        self._flush_to_disk()


@dataclass
class Page:
    """数据页"""
    page_id: int
    data: Any = None
    page_lsn: int = 0  # 页最后修改对应的LSN
    is_dirty: bool = False


class CheckpointManager:
    """检查点管理器"""
    
    def __init__(self, wal: WALManager):
        self.wal = wal
        self.last_checkpoint_lsn: int = 0
        self.active_transactions: Dict[int, int] = {}  # tx_id -> last_lsn
    
    def create_checkpoint(self, dirty_pages: List[Page]) -> LogRecord:
        """
        创建检查点
        dirty_pages: 内存中脏页列表
        """
        checkpoint_log = LogRecord(
            lsn=-1,  # 待分配
            tx_id=0,  # 系统事务
            log_type=LogType.CHECKPOINT
        )
        
        # 构建检查点信息
        checkpoint_info = {
            "active_txs": list(self.active_transactions.keys()),
            "dirty_pages": [(p.page_id, p.page_lsn) for p in dirty_pages],
            "last_checkpoint": self.last_checkpoint_lsn
        }
        
        checkpoint_log.after_image = checkpoint_info
        
        # 写检查点日志
        lsn = self.wal.append_log(checkpoint_log)
        checkpoint_log.lsn = lsn
        self.last_checkpoint_lsn = lsn
        
        # 强制刷盘（检查点必须持久化）
        self.wal.force_flush()
        
        return checkpoint_log


class ARIESRecovery:
    """
    ARIES恢复算法实现
    分析(Analysis) -> 重做(Redo) -> 撤销(Undo)
    """
    
    def __init__(self, wal: WALManager, checkpoint_mgr: CheckpointManager):
        self.wal = wal
        self.checkpoint_mgr = checkpoint_mgr
        self.transaction_table: Dict[int, Dict] = {}  # 事务表
        self.dirty_page_table: Dict[int, int] = {}    # 脏页表 (page_id -> rec_lsn)
        self.active_transactions: List[int] = []      # 活动事务列表
    
    def analyze(self) -> Tuple[int, Dict, Dict]:
        """
        分析阶段
        从检查点开始扫描日志，确定哪些事务需要重做/撤销
        返回: (分析结束位置, 事务表, 脏页表)
        """
        print("\n=== 分析阶段 (Analysis) ===")
        
        # 从上一个检查点开始分析
        start_lsn = self.checkpoint_mgr.last_checkpoint_lsn
        print(f"从检查点 LSN={start_lsn} 开始分析")
        
        # 清空表
        self.transaction_table = {}
        self.dirty_page_table = {}
        
        # 扫描日志
        for log in self.wal.log_buffer:
            if log.lsn <= start_lsn:
                continue
            
            if log.log_type == LogType.BEGIN:
                # 事务开始
                self.transaction_table[log.tx_id] = {
                    "status": "active",
                    "last_lsn": log.lsn
                }
                self.active_transactions.append(log.tx_id)
                
            elif log.log_type == LogType.UPDATE:
                # 更新操作
                if log.tx_id in self.transaction_table:
                    self.transaction_table[log.tx_id]["last_lsn"] = log.lsn
                
                # 更新脏页表
                if log.page_id >= 0:
                    self.dirty_page_table[log.page_id] = min(
                        self.dirty_page_table.get(log.page_id, log.lsn),
                        log.lsn
                    )
                
            elif log.log_type == LogType.COMMIT:
                # 事务提交
                if log.tx_id in self.transaction_table:
                    self.transaction_table[log.tx_id]["status"] = "committed"
                    self.active_transactions.remove(log.tx_id)
                    
            elif log.log_type == LogType.ABORT:
                # 事务中止
                if log.tx_id in self.transaction_table:
                    self.transaction_table[log.tx_id]["status"] = "aborted"
                    if log.tx_id in self.active_transactions:
                        self.active_transactions.remove(log.tx_id)
            
            elif log.log_type == LogType.CHECKPOINT:
                # 检查点，更新脏页表
                if log.after_image and "dirty_pages" in log.after_image:
                    for page_id, page_lsn in log.after_image["dirty_pages"]:
                        if page_id not in self.dirty_page_table:
                            self.dirty_page_table[page_id] = page_lsn
        
        print(f"发现活动事务: {self.active_transactions}")
        print(f"脏页数: {len(self.dirty_page_table)}")
        
        return start_lsn, self.transaction_table, self.dirty_page_table
    
    def redo(self, pages: Dict[int, Page]) -> int:
        """
        重做阶段
        从脏页表记录的最早LSN开始，重做所有未刷盘的修改
        返回: 重做的日志数
        """
        print("\n=== 重做阶段 (Redo) ===")
        
        redo_count = 0
        
        # 找到最小rec_lsn
        if not self.dirty_page_table:
            print("无需重做")
            return 0
        
        min_rec_lsn = min(self.dirty_page_table.values())
        print(f"从最小rec_lsn={min_rec_lsn}开始重做")
        
        for page_id, page in pages.items():
            if page.page_lsn < min_rec_lsn:
                continue
            
            # 需要重做
            print(f"重做页 {page_id} (page_lsn={page.page_lsn})")
            page.is_dirty = True
            redo_count += 1
        
        print(f"重做了 {redo_count} 个页")
        return redo_count
    
    def undo(self) -> int:
        """
        撤销阶段
        对活动事务执行撤销（回滚）
        返回: 撤销的操作数
        """
        print("\n=== 撤销阶段 (Undo) ===")
        
        undo_count = 0
        # 模拟撤销活动事务的未提交修改
        for tx_id in self.active_transactions:
            tx_info = self.transaction_table.get(tx_id, {})
            last_lsn = tx_info.get("last_lsn", -1)
            print(f"撤销事务 {tx_id}, last_lsn={last_lsn}")
            undo_count += 1
        
        print(f"撤销了 {undo_count} 个事务")
        return undo_count
    
    def recover(self, pages: Dict[int, Page]) -> Dict[str, int]:
        """
        执行完整恢复
        返回: 各阶段统计
        """
        print("=" * 60)
        print("ARIES 故障恢复")
        print("=" * 60)
        
        # 分析
        analyze_lsn, tx_table, dirty_table = self.analyze()
        
        # 重做
        redo_count = self.redo(pages)
        
        # 撤销
        undo_count = self.undo()
        
        return {
            "analyze_lsn": analyze_lsn,
            "redo_count": redo_count,
            "undo_count": undo_count,
            "active_txs": len(self.active_transactions)
        }


if __name__ == "__main__":
    # 构造测试场景
    wal = WALManager()
    checkpoint_mgr = CheckpointManager(wal)
    aries = ARIESRecovery(wal, checkpoint_mgr)
    
    # 模拟事务操作
    print("模拟事务日志:")
    
    # T1: BEGIN
    log1 = LogRecord(lsn=-1, tx_id=1, log_type=LogType.BEGIN)
    wal.write_log(log1)
    print(f"  {log1}")
    
    # T1: UPDATE page 10
    log2 = LogRecord(lsn=-1, tx_id=1, log_type=LogType.UPDATE,
                     page_id=10, before_image="old", after_image="new")
    wal.write_log(log2)
    print(f"  {log2}")
    
    # T2: BEGIN
    log3 = LogRecord(lsn=-1, tx_id=2, log_type=LogType.BEGIN)
    wal.write_log(log3)
    print(f"  {log3}")
    
    # T2: UPDATE page 20
    log4 = LogRecord(lsn=-1, tx_id=2, log_type=LogType.UPDATE,
                     page_id=20, before_image="old2", after_image="new2")
    wal.write_log(log4)
    print(f"  {log4}")
    
    # 检查点
    dirty_pages = [Page(page_id=10, page_lsn=1), Page(page_id=20, page_lsn=3)]
    checkpoint_log = checkpoint_mgr.create_checkpoint(dirty_pages)
    print(f"  {checkpoint_log}")
    
    # T1: COMMIT
    log5 = LogRecord(lsn=-1, tx_id=1, log_type=LogType.COMMIT)
    wal.write_log(log5)
    print(f"  {log5}")
    
    # T2: UPDATE page 30（故障发生点）
    log6 = LogRecord(lsn=-1, tx_id=2, log_type=LogType.UPDATE,
                     page_id=30, before_image="old3", after_image="new3")
    wal.write_log(log6)
    print(f"  {log6}")
    
    # 执行恢复
    pages = {10: Page(page_id=10, page_lsn=1, is_dirty=True),
             20: Page(page_id=20, page_lsn=3, is_dirty=True),
             30: Page(page_id=30, page_lsn=5, is_dirty=False)}
    
    result = aries.recover(pages)
    
    print("\n恢复结果:")
    print(f"  分析结束位置: LSN={result['analyze_lsn']}")
    print(f"  重做页数: {result['redo_count']}")
    print(f"  撤销事务数: {result['undo_count']}")
    print(f"  剩余活动事务: {result['active_txs']}")
