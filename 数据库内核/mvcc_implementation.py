# -*- coding: utf-8 -*-

"""

算法实现：数据库内核 / mvcc_implementation



本文件实现 mvcc_implementation 相关的算法功能。

"""



import time

import threading

from dataclasses import dataclass, field

from typing import Dict, List, Optional, Tuple, Any

from enum import IntEnum





class TransactionStatus(IntEnum):

    """事务状态"""

    ACTIVE = 0  # 活跃

    COMMITTED = 1  # 已提交

    ABORTED = 2  # 已中止





class IsolationLevel(IntEnum):

    """隔离级别"""

    READ_COMMITTED = 1  # 读已提交

    REPEATABLE_READ = 2  # 可重复读

    SERIALIZABLE = 3  # 串行化





@dataclass

class Version:

    """数据版本"""

    tx_id: int  # 创建版本的事务ID

    status: TransactionStatus  # 事务状态

    value: Any  # 数据值

    created_at: float  # 创建时间

    is_deleted: bool = False  # 是否被删除





@dataclass

class Transaction:

    """事务上下文"""

    tx_id: int  # 事务ID

    status: TransactionStatus = TransactionStatus.ACTIVE  # 事务状态

    start_time: float = field(default_factory=time.time)  # 开始时间

    isolation_level: IsolationLevel = IsolationLevel.REPEATABLE_READ  # 隔离级别

    snapshot: Tuple[int, List[int]] = field(default=None)  # 快照(时间戳,活跃事务列表)

    read_set: List[str] = field(default_factory=list)  # 读集

    write_set: List[str] = field(default_factory=list)  # 写集





class MVCCStore:

    """

    MVCC存储引擎核心



    支持:

    - 多版本数据存储

    - 快照读取(ReadView)

    - First-Write-Win冲突检测

    - 垃圾回收

    """



    def __init__(self):

        self.data: Dict[str, List[Version]] = {}  # key -> 版本链

        self.lock = threading.RLock()  # 全局锁

        self.tx_counter = 0  # 事务计数器

        self.active_transactions: Dict[int, Transaction] = {}  # 活跃事务



    def begin_tx(self, isolation_level: IsolationLevel = IsolationLevel.REPEATABLE_READ) -> Transaction:

        """

        开启新事务

        创建事务快照

        """

        with self.lock:

            self.tx_counter += 1

            tx = Transaction(

                tx_id=self.tx_counter,

                isolation_level=isolation_level,

                snapshot=self._create_snapshot()

            )

            self.active_transactions[tx.tx_id] = tx

            return tx



    def _create_snapshot(self) -> Tuple[int, List[int]]:

        """创建当前时刻的快照"""

        active_ids = list(self.active_transactions.keys())

        return (self.tx_counter, active_ids)



    def read(self, tx: Transaction, key: str) -> Optional[Any]:

        """

        读取数据(快照读)

        根据事务隔离级别和快照确定可见版本

        """

        with self.lock:

            if key not in self.data:

                return None



            versions = self.data[key]

            tx_snapshot_time, tx_active = tx.snapshot



            # 根据隔离级别选择可见版本

            if tx.isolation_level == IsolationLevel.READ_COMMITTED:

                # 读已提交: 读取最新已提交版本

                visible_version = self._find_latest_committed(versions)

            else:

                # 可重复读: 读取事务开始时的快照

                visible_version = self._find_version_at_snapshot(versions, tx_snapshot_time, tx_active)



            if visible_version is None or visible_version.is_deleted:

                return None



            tx.read_set.append(key)  # 加入读集

            return visible_version.value



    def _find_latest_committed(self, versions: List[Version]) -> Optional[Version]:

        """查找最新已提交版本"""

        for v in reversed(versions):

            if v.status == TransactionStatus.COMMITTED:

                return v

        return None



    def _find_version_at_snapshot(self, versions: List[Version],

                                   snapshot_time: int,

                                   active_transactions: List[int]) -> Optional[Version]:

        """

        查找快照时刻的可见版本

        规则:

        1. 版本由未提交事务创建 -> 不可见

        2. 版本在快照之后创建 -> 不可见

        3. 版本标记删除 -> 不可见

        """

        candidates = []

        for v in versions:

            # 规则1: 排除活跃事务创建的未提交版本

            if v.tx_id in active_transactions and v.status == TransactionStatus.ACTIVE:

                continue

            # 规则2: 排除快照时间之后提交的版本

            if v.status == TransactionStatus.COMMITTED:

                candidates.append(v)



        if not candidates:

            return None

        return max(candidates, key=lambda x: x.created_at)



    def write(self, tx: Transaction, key: str, value: Any):

        """

        写入数据(写放大模式)

        创建新版本，标记旧版本

        """

        with self.lock:

            if key not in self.data:

                self.data[key] = []



            new_version = Version(

                tx_id=tx.tx_id,

                status=TransactionStatus.ACTIVE,

                value=value,

                created_at=time.time()

            )

            self.data[key].append(new_version)

            tx.write_set.append(key)



    def commit(self, tx: Transaction) -> bool:

        """

        提交事务

        验证First-Write-Win，批量提交所有版本

        """

        with self.lock:

            if tx.tx_id not in self.active_transactions:

                raise ValueError(f"事务 {tx.tx_id} 不存在")



            # First-Write-Win检查: 确保没有其他事务在我们之前修改了相同key

            for key in tx.write_set:

                if key in self.data:

                    latest = self.data[key][-1]

                    # 如果最新版本是在此事务开始后被其他事务提交的 -> 冲突

                    if latest.tx_id != tx.tx_id and latest.status == TransactionStatus.COMMITTED:

                        self.abort(tx)

                        return False



            # 批量提交所有版本

            for key in tx.write_set:

                if key in self.data:

                    for v in self.data[key]:

                        if v.tx_id == tx.tx_id:

                            v.status = TransactionStatus.COMMITTED



            tx.status = TransactionStatus.COMMITTED

            del self.active_transactions[tx.tx_id]

            return True



    def abort(self, tx: Transaction):

        """中止事务，回滚所有修改"""

        with self.lock:

            # 标记所有版本为中止

            for key in tx.write_set:

                if key in self.data:

                    for v in self.data[key]:

                        if v.tx_id == tx.tx_id:

                            v.status = TransactionStatus.ABORTED

                            v.is_deleted = True



            tx.status = TransactionStatus.ABORTED

            if tx.tx_id in self.active_transactions:

                del self.active_transactions[tx.tx_id]



    def vacuum(self, keep_versions: int = 3):

        """

        垃圾回收: 保留每个key最近N个有效版本

        删除已中止事务的版本和无用版本

        """

        with self.lock:

            for key, versions in self.data.items():

                # 过滤掉中止事务的版本

                valid_versions = [v for v in versions

                                  if v.status != TransactionStatus.ABORTED]

                # 保留最近N个版本

                self.data[key] = valid_versions[-keep_versions:] if len(valid_versions) > keep_versions else valid_versions





def print_tx_info(tx: Transaction, store: MVCCStore):

    """打印事务信息"""

    print(f"事务{tx.tx_id}: 状态={tx.status.name}, 隔离级别={tx.isolation_level.name}")

    print(f"  读集: {tx.read_set}")

    print(f"  写集: {tx.write_set}")





if __name__ == "__main__":

    store = MVCCStore()



    # 开启事务T1 (可重复读)

    print("=== 开启事务T1 ===")

    tx1 = store.begin_tx(IsolationLevel.REPEATABLE_READ)

    print_tx_info(tx1, store)



    # T1写入初始数据

    store.write(tx1, "balance", 1000)

    store.write(tx1, "name", "Alice")

    print(f"T1 写入: balance=1000, name=Alice")



    # 开启事务T2 (读已提交)

    print("\n=== 开启事务T2 ===")

    tx2 = store.begin_tx(IsolationLevel.READ_COMMITTED)

    print_tx_info(tx2, store)



    # T2读取数据(此时T1未提交,读已提交应该看不到)

    val1 = store.read(tx2, "balance")

    val2 = store.read(tx2, "name")

    print(f"T2 读取: balance={val1}, name={val2}")



    # 提交T1

    print("\n=== 提交T1 ===")

    success = store.commit(tx1)

    print(f"T1 提交结果: {'成功' if success else '失败'}")



    # T2再次读取(读已提交能看到T1提交)

    val1 = store.read(tx2, "balance")

    val2 = store.read(tx2, "name")

    print(f"T2 再次读取: balance={val1}, name={val2}")



    # 开启事务T3 (可重复读),验证快照

    print("\n=== 开启事务T3 (可重复读) ===")

    tx3 = store.begin_tx(IsolationLevel.REPEATABLE_READ)

    print_tx_info(tx3, store)



    # T3读取,应该看到T1提交前的快照

    val1 = store.read(tx3, "balance")

    print(f"T3 读取: balance={val1} (T3快照时间在T1提交前)")



    # 开启事务T4修改数据

    print("\n=== 开启事务T4,修改balance ===")

    tx4 = store.begin_tx()

    store.write(tx4, "balance", 2000)

    print(f"T4 写入: balance=2000")



    # T3再读,验证可重复读

    val1 = store.read(tx3, "balance")

    print(f"T3 再次读取: balance={val1} (应该与之前一致)")



    # 提交T4

    store.commit(tx4)

    print("T4 已提交")



    # T3再读,验证可重复读

    val1 = store.read(tx3, "balance")

    print(f"T3 最后读取: balance={val1} (快照不变)")



    # 垃圾回收测试

    print("\n=== 垃圾回收 ===")

    store.vacuum(keep_versions=2)

    print("GC完成,保留每个key最近2个版本")



    # 打印最终状态

    print("\n=== 最终数据状态 ===")

    for key, versions in store.data.items():

        print(f"{key}: {[f'v{v.tx_id}({v.value},{v.status.name})' for v in versions]}")

