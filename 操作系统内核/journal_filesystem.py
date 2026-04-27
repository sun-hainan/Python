# -*- coding: utf-8 -*-
"""
算法实现：操作系统内核 / journal_filesystem

本文件实现 journal_filesystem 相关的算法功能。
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time


class JournalMode(Enum):
    """日志模式"""
    JOURNAL = "journal"      # 完全日志
    ORDERED = "ordered"      # 有序模式
    WRITEBACK = "writeback" # 回写模式


@dataclass
class JournalBlock:
    """日志块"""
    block_nr: int            # 块号
    data: bytes = b''        # 数据
    transaction_id: int = 0  # 所属事务
    timestamp: int = 0


@dataclass
class Transaction:
    """事务"""
    tid: int                 # 事务ID
    status: str = "running"  # running, committed, checkpointed
    blocks: List[Tuple[int, bytes]] = field(default_factory=list)  # (block_nr, data)
    start_time: int = 0
    commit_time: int = 0


class JBD2:
    """
    Journaling Block Device (JBD2)

    ext4使用的日志子系统。
    负责管理日志区域和事务处理。
    """

    def __init__(self, device_size: int, journal_blocks: int = 1024):
        self.device_size = device_size
        self.journal_size = journal_blocks

        # 日志区域（模拟）
        self.journal_area: List[Optional[JournalBlock]] = [None] * journal_blocks
        self.journal_start = 0  # 日志起始位置
        self.journal_end = 0    # 日志结束位置

        # 事务
        self.transactions: Dict[int, Transaction] = {}
        self.next_tid = 1

        # 当前活跃事务
        self.current_transaction: Optional[Transaction] = None

        # 检查点
        self.checkpointed_transactions: Set[int] = set()

        # 统计
        self.total_commits = 0
        self.total_checkpoints = 0

    def start_transaction(self) -> int:
        """开始新事务"""
        if self.current_transaction and self.current_transaction.status == "running":
            # 已有活跃事务
            self.commit_transaction()

        tid = self.next_tid
        self.next_tid += 1

        self.current_transaction = Transaction(
            tid=tid,
            status="running",
            start_time=int(time.time())
        )
        self.transactions[tid] = self.current_transaction

        return tid

    def modify_block(self, block_nr: int, data: bytes):
        """记录块修改"""
        if not self.current_transaction:
            self.start_transaction()

        # 将旧数据保存到事务中
        self.current_transaction.blocks.append((block_nr, data))

    def commit_transaction(self) -> bool:
        """提交事务"""
        if not self.current_transaction:
            return False

        txn = self.current_transaction

        # 1. 将修改的块复制到日志区域
        for block_nr, data in txn.blocks:
            journal_block = JournalBlock(
                block_nr=block_nr,
                data=data,
                transaction_id=txn.tid,
                timestamp=int(time.time())
            )

            # 写入日志
            if self.journal_end < self.journal_size:
                self.journal_area[self.journal_end] = journal_block
                self.journal_end += 1

        # 2. 标记事务为已提交
        txn.status = "committed"
        txn.commit_time = int(time.time())

        self.total_commits += 1
        self.current_transaction = None

        print(f"  事务 {txn.tid} 已提交，包含 {len(txn.blocks)} 个块")

        return True

    def checkpoint_transaction(self, tid: int) -> bool:
        """检查点事务：将日志中的修改应用到主文件系统"""
        if tid not in self.transactions:
            return False

        txn = self.transactions[tid]
        if txn.status != "committed":
            return False

        # 将日志中的数据写入主文件系统（模拟）
        for block_nr, data in txn.blocks:
            # 实际会调用submit_bh将块写入磁盘
            pass

        txn.status = "checkpointed"
        self.checkpointed_transactions.add(tid)
        self.total_checkpoints += 1

        print(f"  事务 {tid} 检查点完成")

        return True

    def recovery(self):
        """恢复：在系统崩溃后重放日志"""
        print("\n开始恢复...")

        # 找到所有已提交但未检查点的事务
        to_replay = []
        for tid, txn in self.transactions.items():
            if txn.status == "committed" and tid not in self.checkpointed_transactions:
                to_replay.append(txn)

        # 重放这些事务
        for txn in sorted(to_replay, key=lambda t: t.commit_time):
            print(f"  重放事务 {txn.tid}...")
            for block_nr, data in txn.blocks:
                # 重放块修改
                print(f"    重放块 {block_nr}")

        print(f"恢复完成，共重放 {len(to_replay)} 个事务")


class Ext4Filesystem:
    """
    ext4文件系统

    支持日志功能。
    """

    def __init__(self, device_size: int = 1024 * 1024):
        self.device_size = device_size

        # 块大小
        self.block_size = 4096
        self.num_blocks = device_size // self.block_size

        # 文件系统状态
        self.blocks: Dict[int, bytes] = {}
        self.free_blocks: Set[int] = set(range(1, self.num_blocks))

        # 日志
        self.journal_mode = JournalMode.ORDERED
        self.jbd2 = JBD2(device_size, journal_blocks=1024)

        # 统计
        self.mount_count = 0
        self.last_mount_time = 0

    def write_block(self, block_nr: int, data: bytes):
        """写入块"""
        # 在ordered模式下，元数据写入日志，数据直接写入
        if self.journal_mode == JournalMode.ORDERED:
            self.jbd2.modify_block(block_nr, self.blocks.get(block_nr, b'\x00' * self.block_size))
            self.blocks[block_nr] = data
        else:
            self.jbd2.modify_block(block_nr, self.blocks.get(block_nr, b'\x00' * self.block_size))
            self.blocks[block_nr] = data

    def allocate_block(self) -> Optional[int]:
        """分配块"""
        if not self.free_blocks:
            return None
        return self.free_blocks.pop()

    def free_block(self, block_nr: int):
        """释放块"""
        self.free_blocks.add(block_nr)

    def mount(self):
        """挂载文件系统"""
        self.mount_count += 1
        self.last_mount_time = int(time.time())
        print(f"\next4文件系统已挂载")
        print(f"  块大小: {self.block_size}")
        print(f"  总块数: {self.num_blocks}")
        print(f"  空闲块: {len(self.free_blocks)}")
        print(f"  日志模式: {self.journal_mode.value}")

    def unmount(self):
        """卸载文件系统"""
        # 提交所有活跃事务
        if self.jbd2.current_transaction:
            self.jbd2.commit_transaction()

        # 检查点所有已提交事务
        for tid in list(self.jbd2.transactions.keys()):
            if tid not in self.jbd2.checkpointed_transactions:
                self.jbd2.checkpoint_transaction(tid)

        print(f"\next4文件系统已卸载")
        print(f"  挂载次数: {self.mount_count}")


class WALTransaction:
    """
    Write-Ahead Logging 事务

    WAL的核心思想：
    1. 日志先写入（Write-Ahead）
    2. 数据修改在日志之后
    3. 确保日志已提交后数据修改才生效
    """

    def __init__(self, name: str):
        self.name = name
        self.operations: List[Dict] = []
        self.status = "pending"  # pending, committed, applied

    def add_operation(self, op_type: str, data: any):
        """添加操作到日志"""
        self.operations.append({
            'type': op_type,
            'data': data,
            'timestamp': time.time()
        })

    def commit(self):
        """提交事务"""
        self.status = "committed"
        print(f"  WAL事务 '{self.name}' 已提交，包含 {len(self.operations)} 个操作")

    def apply(self):
        """应用到数据库（模拟）"""
        self.status = "applied"
        print(f"  WAL事务 '{self.name}' 已应用")


def simulate_ext4_journal():
    """
    模拟ext4日志文件系统
    """
    print("=" * 60)
    print("日志文件系统：ext4 Journal")
    print("=" * 60)

    # 创建ext4文件系统
    fs = Ext4Filesystem(device_size=1024 * 1024)  # 1MB

    # 挂载
    fs.mount()

    # 模拟文件操作
    print("\n模拟文件操作:")
    print("-" * 50)

    # 创建文件
    print("\n1. 创建新文件 /test.txt")
    fs.jbd2.start_transaction()

    # 分配块并写入
    block1 = fs.allocate_block()
    print(f"  分配块: {block1}")
    fs.write_block(block1, b"Hello, ext4!")

    # 提交事务
    fs.jbd2.commit_transaction()

    # 模拟崩溃后恢复
    print("\n2. 模拟系统崩溃...")

    print("\n3. 系统重启，恢复中:")
    fs.jbd2.recovery()

    # 显示日志状态
    print("\n日志统计:")
    print("-" * 50)
    print(f"  总提交事务: {fs.jbd2.total_commits}")
    print(f"  总检查点: {fs.jbd2.total_checkpoints}")
    print(f"  日志使用: {fs.jbd2.journal_end}/{fs.jbd2.journal_size} 块")

    # WAL演示
    print("\n" + "=" * 60)
    print("Write-Ahead Logging (WAL)")
    print("=" * 60)

    print("\nWAL操作演示:")
    print("-" * 50)

    # 创建WAL事务
    wal_txn = WALTransaction("txn_user_update")

    # 添加操作
    wal_txn.add_operation("UPDATE", {"table": "users", "id": 1, "name": "Alice"})
    wal_txn.add_operation("UPDATE", {"table": "users", "id": 2, "name": "Bob"})

    # 提交
    wal_txn.commit()

    # 应用
    wal_txn.apply()

    # WAL恢复演示
    print("\nWAL恢复演示:")
    print("-" * 50)

    # 模拟一些已提交但未应用的事务
    wal = WALTransaction("txn_orphan")
    wal.add_operation("INSERT", {"table": "orders", "id": 100})
    wal.commit()
    # 未应用

    print("\n系统崩溃前的日志状态:")
    print(f"  事务 '{wal_txn.name}': {wal_txn.status}")
    print(f"  事务 '{wal.name}': {wal.status}")

    # 恢复
    print("\n恢复过程:")
    if wal.status == "committed":
        wal.apply()


if __name__ == "__main__":
    simulate_ext4_journal()
