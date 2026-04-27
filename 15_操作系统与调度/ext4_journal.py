# -*- coding: utf-8 -*-

"""

算法实现：15_操作系统与调度 / ext4_journal



本文件实现 ext4_journal 相关的算法功能。

"""



from enum import Enum

from dataclasses import dataclass, field

from typing import Optional

import time





class JournalBlockType(Enum):

    """日志块类型"""

    SUPERBLOCK = 1

    DESCRIPTOR = 2

    COMMIT = 3

    REVOKE = 4

    DATA = 5





class TransactionState(Enum):

    """事务状态"""

    RUNNING = 1

    COMMITTED = 2

    FINISHED = 3

    ABORTED = 4





@dataclass

class JournalBlock:

    """日志块"""

    block_id: int

    block_type: JournalBlockType

    data: bytes = b""

    transaction_id: int = 0





@dataclass

class Transaction:

    """日志事务"""

    txn_id: int

    state: TransactionState = TransactionState.RUNNING

    start_time: float = 0.0

    commit_time: float = 0.0

    blocks: list[JournalBlock] = field(default_factory=list)

    revoke_list: list[int] = field(default_factory=list)  # 已撤销的块ID列表





class Ext4Journal:

    """

    ext4日志文件系统（简化实现）

    工作模式：ordered（默认）= 元数据写日志，数据直接写磁盘

    流程：transaction begin → modify → journal write → checkpoint → commit

    """



    def __init__(self, journal_blocks: int = 1024):

        self.journal_blocks = journal_blocks

        self.journal_area: list[Optional[JournalBlock]] = [None] * journal_blocks

        self.current_txn: Optional[Transaction] = None

        self.next_txn_id = 1

        self.commit_sequence = 0  # 已提交的序列号



    def begin_transaction(self) -> Transaction:

        """开始新事务"""

        if self.current_txn and self.current_txn.state == TransactionState.RUNNING:

            raise RuntimeError("上一事务未提交")



        txn = Transaction(

            txn_id=self.next_txn_id,

            state=TransactionState.RUNNING,

            start_time=time.time()

        )

        self.next_txn_id += 1

        self.current_txn = txn

        return txn



    def add_to_transaction(self, block_id: int, data: bytes, block_type: JournalBlockType = JournalBlockType.DATA):

        """将块添加到当前事务"""

        if self.current_txn is None:

            raise RuntimeError("无活跃事务")



        jblock = JournalBlock(

            block_id=block_id,

            block_type=block_type,

            data=data,

            transaction_id=self.current_txn.txn_id

        )

        self.current_txn.blocks.append(jblock)



    def revoke_block(self, block_id: int):

        """撤销块（在恢复时不重复应用）"""

        if self.current_txn:

            self.current_txn.revoke_list.append(block_id)



    def commit_transaction(self) -> bool:

        """提交事务"""

        if self.current_txn is None:

            return False



        txn = self.current_txn



        # 1. 写入日志（descriptor + data blocks）

        self._write_journal(txn)



        # 2. 等待磁盘同步（模拟）

        self._wait_journal_sync()



        # 3. 写入commit block

        self._write_commit(txn)



        # 4. 更新状态

        txn.state = TransactionState.COMMITTED

        txn.commit_time = time.time()



        # 5. 更新commit sequence

        self.commit_sequence += 1



        # 6. 检查点（将日志数据写出到磁盘，释放日志空间）

        self._checkpoint(txn)



        self.current_txn = None

        return True



    def _write_journal(self, txn: Transaction):

        """写入日志区域（descriptor block + data blocks）"""

        # 分配日志块（简化：顺序分配）

        for i, blk in enumerate(self.journal_blocks):

            if blk is None:

                # 写入descriptor

                desc = JournalBlock(

                    block_id=i,

                    block_type=JournalBlockType.DESCRIPTOR,

                    data=f"txn:{txn.txn_id}, blocks:{len(txn.blocks)}".encode(),

                    transaction_id=txn.txn_id

                )

                self.journal_area[i] = desc

                # 写入数据块

                for j, datablock in enumerate(txn.blocks):

                    self.journal_area[i + j + 1] = datablock

                break



    def _wait_journal_sync(self):

        """等待日志同步到磁盘（模拟）"""

        pass



    def _write_commit(self, txn: Transaction):

        """写入commit block"""

        for i, blk in enumerate(self.journal_blocks):

            if blk is None:

                commit = JournalBlock(

                    block_id=i,

                    block_type=JournalBlockType.COMMIT,

                    data=f"COMMIT:{txn.txn_id}".encode(),

                    transaction_id=txn.txn_id

                )

                self.journal_area[i] = commit

                break



    def _checkpoint(self, txn: Transaction):

        """检查点：释放已提交事务占用的日志空间"""

        # 简化：将所有与txn相关的日志块清除

        for i in range(len(self.journal_area)):

            if self.journal_area[i] and self.journal_area[i].transaction_id == txn.txn_id:

                self.journal_area[i] = None



    def recover(self) -> list[Transaction]:

        """从崩溃恢复：重放已提交但未checkpoint的事务"""

        recovered = []

        for blk in self.journal_area:

            if blk is None:

                continue

            if blk.block_type == JournalBlockType.COMMIT:

                # 找到已提交事务

                txn_id = blk.transaction_id

                # 重放该事务的数据块

                for b in self.journal_area:

                    if b and b.transaction_id == txn_id and b.block_type == JournalBlockType.DATA:

                        pass  # 重放数据块到磁盘



                txn = Transaction(

                    txn_id=txn_id,

                    state=TransactionState.FINISHED

                )

                recovered.append(txn)



        return recovered



    def get_stats(self) -> dict:

        """获取日志统计"""

        used = sum(1 for b in self.journal_area if b is not None)

        return {

            "total_blocks": self.journal_blocks,

            "used_blocks": used,

            "free_blocks": self.journal_blocks - used,

            "current_txn": self.current_txn.txn_id if self.current_txn else None,

            "commit_sequence": self.commit_sequence,

        }





if __name__ == "__main__":

    journal = Ext4Journal(journal_blocks=64)



    print("=== ext4日志文件系统演示 ===")

    print(f"初始状态: {journal.get_stats()}")



    # 模拟文件系统操作：创建文件

    print("\n=== 模拟事务：创建文件 /home/user/data.txt ===")



    # 1. 开始事务

    txn = journal.begin_transaction()

    print(f"开始事务 T{txn.txn_id}")



    # 2. 添加修改的块（inode、dentry、data block）

    journal.add_to_transaction(

        block_id=1024,

        data=b"inode: mode=0644, size=1024",

        block_type=JournalBlockType.DATA

    )

    journal.add_to_transaction(

        block_id=2048,

        data=b"dentry: /home/user/data.txt -> inode 1024",

        block_type=JournalBlockType.DATA

    )

    journal.add_to_transaction(

        block_id=4096,

        data=b"Hello, ext4 journal!",

        block_type=JournalBlockType.DATA

    )



    print(f"添加3个块到事务")



    # 3. 提交事务

    success = journal.commit_transaction()

    print(f"提交结果: {'成功' if success else '失败'}")



    # 4. 检查日志状态

    print(f"提交后状态: {journal.get_stats()}")



    # 模拟崩溃恢复

    print("\n=== 模拟崩溃恢复 ===")

    recovered = journal.recover()

    print(f"恢复的事务数: {len(recovered)}")

    for txn in recovered:

        print(f"  重放事务 T{txn.txn_id}")



    # 演示数据一致性

    print("\n=== 数据一致性保证 ===")

    print("日志模式（ordered）保证：")

    print("1. 元数据变更先写入日志")

    print("2. 事务commit后，数据checkpoint到磁盘")

    print("3. 崩溃后根据日志恢复，无数据丢失")

    print("4. fsck检查journal重放即可修复")

