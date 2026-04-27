# -*- coding: utf-8 -*-

"""

算法实现：数据库算法 / transaction_log



本文件实现 transaction_log 相关的算法功能。

"""



import os

import struct

import time

from typing import Dict, List, Optional, Set, Tuple

from dataclasses import dataclass, field

from enum import Enum

import threading





class LogRecordType(Enum):

    """日志记录类型"""

    BEGIN = 0x01          # 事务开始

    UPDATE = 0x02         # 更新操作

    COMMIT = 0x03         # 事务提交

    ABORT = 0x04          # 事务中止

    CHECKPOINT = 0x05     # 检查点

    COMPENSATE = 0x06     # 补偿操作 (CLR)





@dataclass

class LogRecord:

    """日志记录"""

    lsn: int = 0           # 日志序列号

    txn_id: int = 0       # 事务ID

    record_type: LogRecordType = LogRecordType.BEGIN

    page_id: int = 0      # 涉及的页ID

    offset: int = 0       # 页内偏移

    old_value: bytes = b''  # 旧值

    new_value: bytes = b''  # 新值

    prev_lsn: int = 0     # 事务前一个LSN

    timestamp: float = 0.0

    

    def serialize(self) -> bytes:

        """序列化为字节"""

        old_len = len(self.old_value)

        new_len = len(self.new_value)

        

        fmt = f'IIIBIIHHI{old_len}s{new_len}s'

        return struct.pack(fmt,

            self.lsn,

            self.txn_id,

            self.record_type.value,

            self.page_id,

            self.offset,

            old_len,

            new_len,

            self.prev_lsn,

            old_len,

            self.old_value,

            new_len,

            self.new_value

        )

    

    @staticmethod

    def deserialize(data: bytes) -> 'LogRecord':

        """从字节反序列化"""

        # 先读取头部确定old_value和new_value长度

        header = struct.unpack('IIIBIIHH', data[:28])

        

        lsn, txn_id, rec_type, page_id, offset, old_len, new_len, prev_lsn = header

        

        old_value = data[28:28+old_len] if old_len > 0 else b''

        new_value = data[28+old_len:28+old_len+new_len] if new_len > 0 else b''

        

        return LogRecord(

            lsn=lsn,

            txn_id=txn_id,

            record_type=LogRecordType(rec_type),

            page_id=page_id,

            offset=offset,

            old_value=old_value,

            new_value=new_value,

            prev_lsn=prev_lsn

        )





class TransactionManager:

    """

    事务管理器

    

    负责：

    - 事务的开始、提交、中止

    - 维护活跃事务表

    - 生成事务ID

    """

    

    def __init__(self, log_manager: 'LogManager'):

        self.log_manager = log_manager

        self.active_txns: Dict[int, int] = {}  # txn_id -> last_lsn

        self.txn_counter = 0

        self.lock = threading.Lock()

    

    def begin_transaction(self) -> int:

        """开始新事务"""

        with self.lock:

            self.txn_counter += 1

            txn_id = self.txn_counter

            

            # 写BEGIN日志

            record = LogRecord(

                lsn=self.log_manager.get_next_lsn(),

                txn_id=txn_id,

                record_type=LogRecordType.BEGIN

            )

            self.log_manager.append_log(record)

            

            # 记录活跃事务

            self.active_txns[txn_id] = record.lsn

            

            return txn_id

    

    def commit_transaction(self, txn_id: int) -> bool:

        """提交事务"""

        with self.lock:

            if txn_id not in self.active_txns:

                return False

            

            # 写COMMIT日志

            record = LogRecord(

                lsn=self.log_manager.get_next_lsn(),

                txn_id=txn_id,

                record_type=LogRecordType.COMMIT,

                prev_lsn=self.active_txns[txn_id]

            )

            self.log_manager.append_log(record)

            

            # 移除活跃事务

            del self.active_txns[txn_id]

            

            # 强制刷日志

            self.log_manager.flush()

            

            return True

    

    def abort_transaction(self, txn_id: int) -> bool:

        """中止事务"""

        with self.lock:

            if txn_id not in self.active_txns:

                return False

            

            # 写ABORT日志

            record = LogRecord(

                lsn=self.log_manager.get_next_lsn(),

                txn_id=txn_id,

                record_type=LogRecordType.ABORT,

                prev_lsn=self.active_txns[txn_id]

            )

            self.log_manager.append_log(record)

            

            # 回滚该事务的所有修改

            self.log_manager.rollback_transaction(txn_id)

            

            # 移除活跃事务

            del self.active_txns[txn_id]

            

            return True

    

    def get_active_txns(self) -> Set[int]:

        """获取活跃事务ID列表"""

        return set(self.active_txns.keys())





class LogManager:

    """

    日志管理器

    

    负责：

    - 日志的追加写入

    - 日志刷盘

    - 恢复时的日志重放

    """

    

    def __init__(self, log_dir: str = "./wal_logs", buffer_size: int = 4096):

        self.log_dir = log_dir

        self.buffer_size = buffer_size

        self.current_lsn = 0

        self.log_buffer: List[LogRecord] = []

        self.flushed_lsn = 0  # 已刷盘的最大LSN

        

        # 日志文件

        self.log_file = None

        self.log_num = 0

        

        # 脏页表

        self.dirty_pages: Dict[int, int] = {}  # page_id -> recLSN (最早修改该页的日志LSN)

        

        # 锁

        self.lock = threading.Lock()

        

        # 初始化

        self._init_log_file()

    

    def _init_log_file(self) -> None:

        """初始化日志文件"""

        os.makedirs(self.log_dir, exist_ok=True)

        self.log_num = self._get_max_log_num() + 1

        self._open_log_file()

    

    def _open_log_file(self) -> None:

        """打开新的日志文件"""

        if self.log_file:

            self.log_file.close()

        

        log_path = os.path.join(self.log_dir, f"log_{self.log_num:06d}.log")

        self.log_file = open(log_path, 'ab')

    

    def _get_max_log_num(self) -> int:

        """获取当前最大日志号"""

        if not os.path.exists(self.log_dir):

            return -1

        

        max_num = -1

        for fname in os.listdir(self.log_dir):

            if fname.startswith("log_") and fname.endswith(".log"):

                num = int(fname[4:-4])

                max_num = max(max_num, num)

        return max_num

    

    def get_next_lsn(self) -> int:

        """获取下一个LSN"""

        with self.lock:

            self.current_lsn += 1

            return self.current_lsn

    

    def append_log(self, record: LogRecord) -> None:

        """追加日志到缓冲区"""

        with self.lock:

            record.lsn = self.get_next_lsn()

            self.log_buffer.append(record)

            

            # 如果是UPDATE，更新脏页表

            if record.record_type == LogRecordType.UPDATE:

                if record.page_id not in self.dirty_pages:

                    self.dirty_pages[record.page_id] = record.lsn

            

            # 缓冲区满则刷盘

            if len(self.log_buffer) >= self.buffer_size:

                self.flush()

    

    def flush(self) -> None:

        """刷日志到磁盘"""

        with self.lock:

            if not self.log_buffer:

                return

            

            # 写日志到文件

            for record in self.log_buffer:

                data = record.serialize()

                self.log_file.write(struct.pack('I', len(data)))

                self.log_file.write(data)

            

            self.log_file.flush()

            os.fsync(self.log_file.fileno())

            

            # 更新flushed_lsn

            self.flushed_lsn = self.log_buffer[-1].lsn

            

            # 清空缓冲区

            self.log_buffer.clear()

            

            # 检查是否需要切换日志文件

            if self.log_file.tell() > 100 * 1024 * 1024:  # 100MB

                self.log_num += 1

                self._open_log_file()

    

    def rollback_transaction(self, txn_id: int) -> None:

        """

        回滚事务：重放该事务的更新日志并生成CLR

        """

        # 找到该事务的所有日志

        txn_logs = self._read_transaction_logs(txn_id)

        

        # 逆序回滚（从后往前）

        for record in reversed(txn_logs):

            if record.record_type == LogRecordType.UPDATE:

                # 生成CLR（补偿日志记录）

                clr = LogRecord(

                    txn_id=txn_id,

                    record_type=LogRecordType.COMPENSATE,

                    page_id=record.page_id,

                    offset=record.offset,

                    old_value=record.old_value,  # 回滚到旧值

                    new_value=record.new_value,

                    prev_lsn=record.lsn

                )

                self.append_log(clr)

    

    def _read_transaction_logs(self, txn_id: int) -> List[LogRecord]:

        """读取指定事务的所有日志"""

        logs = []

        

        # 扫描所有日志文件

        for log_num in range(self.log_num + 1):

            log_path = os.path.join(self.log_dir, f"log_{log_num:06d}.log")

            if not os.path.exists(log_path):

                continue

            

            with open(log_path, 'rb') as f:

                while True:

                    # 读取记录长度

                    len_bytes = f.read(4)

                    if not len_bytes:

                        break

                    

                    rec_len = struct.unpack('I', len_bytes)[0]

                    rec_data = f.read(rec_len)

                    

                    record = LogRecord.deserialize(rec_data)

                    if record.txn_id == txn_id:

                        logs.append(record)

        

        return logs

    

    def do_checkpoint(self) -> None:

        """执行检查点"""

        with self.lock:

            # 写CHECKPOINT日志，包含脏页表和活跃事务信息

            record = LogRecord(

                lsn=self.get_next_lsn(),

                record_type=LogRecordType.CHECKPOINT

            )

            self.append_log(record)

            self.flush()

    

    def recovery(self) -> Tuple[int, int]:

        """

        执行恢复

        

        返回:

            (重做的事务数, 回滚的事务数)

        """

        print("Starting recovery...")

        

        # 1. 分析阶段

        dirty_pages, active_txns = self._analysis()

        print(f"Analysis: dirty_pages={len(dirty_pages)}, active_txns={active_txns}")

        

        # 2. 重做阶段

        redo_count = self._redo(dirty_pages)

        print(f"Redo: {redo_count} records processed")

        

        # 3. 回滚阶段

        rollback_count = self._rollback(active_txns)

        print(f"Rollback: {rollback_count} transactions rolled back")

        

        return redo_count, rollback_count

    

    def _analysis(self) -> Tuple[Dict[int, int], Set[int]]:

        """分析阶段：扫描日志，构建脏页表和活跃事务表"""

        dirty_pages = {}

        active_txns = set()

        

        for log_num in range(self.log_num + 1):

            log_path = os.path.join(self.log_dir, f"log_{log_num:06d}.log")

            if not os.path.exists(log_path):

                continue

            

            with open(log_path, 'rb') as f:

                while True:

                    len_bytes = f.read(4)

                    if not len_bytes:

                        break

                    

                    rec_len = struct.unpack('I', len_bytes)[0]

                    rec_data = f.read(rec_len)

                    record = LogRecord.deserialize(rec_data)

                    

                    if record.record_type == LogRecordType.BEGIN:

                        active_txns.add(record.txn_id)

                    

                    elif record.record_type == LogRecordType.COMMIT:

                        active_txns.discard(record.txn_id)

                    

                    elif record.record_type == LogRecordType.ABORT:

                        active_txns.discard(record.txn_id)

                    

                    elif record.record_type == LogRecordType.UPDATE:

                        if record.page_id not in dirty_pages:

                            dirty_pages[record.page_id] = record.lsn

        

        return dirty_pages, active_txns

    

    def _redo(self, dirty_pages: Dict[int, int]) -> int:

        """重做阶段：重做所有修改"""

        count = 0

        

        for log_num in range(self.log_num + 1):

            log_path = os.path.join(self.log_dir, f"log_{log_num:06d}.log")

            if not os.path.exists(log_path):

                continue

            

            with open(log_path, 'rb') as f:

                while True:

                    len_bytes = f.read(4)

                    if not len_bytes:

                        break

                    

                    rec_len = struct.unpack('I', len_bytes)[0]

                    rec_data = f.read(rec_len)

                    record = LogRecord.deserialize(rec_data)

                    

                    if record.record_type == LogRecordType.UPDATE:

                        # 重做此操作

                        count += 1

        

        return count

    

    def _rollback(self, active_txns: Set[int]) -> int:

        """回滚阶段：回滚未提交事务"""

        count = 0

        for txn_id in active_txns:

            self.rollback_transaction(txn_id)

            count += 1

        return count





# ==================== 测试代码 ====================

if __name__ == "__main__":

    import shutil

    

    print("=" * 50)

    print("Write-Ahead Log (WAL) 测试")

    print("=" * 50)

    

    # 清理旧日志

    log_dir = "./test_wal"

    if os.path.exists(log_dir):

        shutil.rmtree(log_dir)

    

    # 创建日志管理器

    log_mgr = LogManager(log_dir=log_dir, buffer_size=100)

    txn_mgr = TransactionManager(log_mgr)

    

    # 测试基本事务

    print("\n--- 基本事务测试 ---")

    

    # 事务1: 插入

    txn1 = txn_mgr.begin_transaction()

    print(f"事务 {txn1} 开始")

    

    log_mgr.append_log(LogRecord(

        txn_id=txn1,

        record_type=LogRecordType.UPDATE,

        page_id=1,

        offset=100,

        old_value=b'old',

        new_value=b'new1'

    ))

    

    txn_mgr.commit_transaction(txn1)

    print(f"事务 {txn1} 提交")

    

    # 事务2: 另一个插入

    txn2 = txn_mgr.begin_transaction()

    print(f"事务 {txn2} 开始")

    

    log_mgr.append_log(LogRecord(

        txn_id=txn2,

        record_type=LogRecordType.UPDATE,

        page_id=2,

        offset=200,

        old_value=b'old',

        new_value=b'new2'

    ))

    

    # 事务3: 将要中止的事务

    txn3 = txn_mgr.begin_transaction()

    log_mgr.append_log(LogRecord(

        txn_id=txn3,

        record_type=LogRecordType.UPDATE,

        page_id=3,

        offset=300,

        old_value=b'old',

        new_value=b'new3'

    ))

    

    # 中止事务3

    txn_mgr.abort_transaction(txn3)

    print(f"事务 {txn3} 中止（将回滚）")

    

    # 检查点

    log_mgr.do_checkpoint()

    print("检查点完成")

    

    # 强制刷日志

    log_mgr.flush()

    

    # 检查活跃事务

    print(f"\n活跃事务: {txn_mgr.get_active_txns()}")

    print(f"脏页表: {log_mgr.dirty_pages}")

    

    # 模拟崩溃后恢复

    print("\n--- 模拟崩溃后恢复 ---")

    

    # 重置LSN模拟新启动

    log_mgr2 = LogManager(log_dir=log_dir)

    txn_mgr2 = TransactionManager(log_mgr2)

    

    redo_count, rollback_count = log_mgr2.recovery()

    print(f"恢复完成: 重做={redo_count}, 回滚={rollback_count}")

    

    # 性能测试

    print("\n--- 性能测试 ---")

    

    import time

    import random

    

    log_dir2 = "./test_wal_perf"

    if os.path.exists(log_dir2):

        shutil.rmtree(log_dir2)

    

    log_mgr3 = LogManager(log_dir=log_dir2, buffer_size=1000)

    txn_mgr3 = TransactionManager(log_mgr3)

    

    n_txns = 1000

    ops_per_txn = 5

    

    start = time.time()

    

    for i in range(n_txns):

        txn = txn_mgr3.begin_transaction()

        

        for j in range(ops_per_txn):

            log_mgr3.append_log(LogRecord(

                txn_id=txn,

                record_type=LogRecordType.UPDATE,

                page_id=random.randint(1, 100),

                offset=random.randint(0, 4000),

                old_value=b'x' * 100,

                new_value=b'y' * 100

            ))

        

        if i % 100 == 99:  # 每100个事务提交

            log_mgr3.flush()

        

        if random.random() < 0.1:  # 10%概率中止

            txn_mgr3.abort_transaction(txn)

        else:

            txn_mgr3.commit_transaction(txn)

    

    elapsed = time.time() - start

    

    print(f"执行 {n_txns} 事务，每事务 {ops_per_txn} 操作")

    print(f"耗时: {elapsed:.3f}秒")

    print(f"吞吐: {n_txns/elapsed:.0f} txn/s")

    

    # 清理

    if os.path.exists(log_dir):

        shutil.rmtree(log_dir)

    if os.path.exists(log_dir2):

        shutil.rmtree(log_dir2)

