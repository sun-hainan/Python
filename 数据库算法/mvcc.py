# -*- coding: utf-8 -*-

"""

算法实现：数据库算法 / mvcc



本文件实现 mvcc 相关的算法功能。

"""



import time

from typing import Dict, List, Optional, Tuple, Any

from dataclasses import dataclass, field

from collections import defaultdict





@dataclass

class Version:

    """行数据的版本"""

    version_id: int                      # 版本号

    transaction_id: int                   # 创建该版本的事务ID

    status: str                           # 事务状态: ACTIVE, COMMITTED, ABORTED

    created_at: float                    # 创建时间

    commit_at: Optional[float] = None    # 提交时间（用于可见性判断）

    

    # 字段值

    values: Dict[str, Any] = field(default_factory=dict)

    

    # 指向旧版本的指针

    prev_version: Optional['Version'] = None





@dataclass

class Row:

    """数据库行"""

    row_id: str                           # 行ID（主键）

    table_id: str                         # 表ID

    

    # 版本链头指针

    latest_version: Optional[Version] = None

    

    # 锁信息（用于写操作）

    exclusive_lock: Optional[int] = None  # 持有排他锁的事务ID





class Transaction:

    """事务"""



    STATUS_ACTIVE = "ACTIVE"

    STATUS_COMMITTED = "COMMITTED"

    STATUS_ABORTED = "ABORTED"



    def __init__(self, transaction_id: int, isolation_level: str = "READ_COMMITTED"):

        self.transaction_id = transaction_id

        self.isolation_level = isolation_level

        self.status = self.STATUS_ACTIVE

        self.start_time = time.time()

        self.snapshot_xmin = 0             # 快照下界（可见的最早事务）

        self.snapshot_xmax = 0             # 快照上界（之后的事务不可见）

        self.active_txn_ids = set()       # 活跃事务ID集合

        

        # 事务本地写集（用于检测写偏斜）

        self.write_set: List[Tuple[str, str]] = []  # [(table_id, row_id), ...]



    def __repr__(self):

        return f"Transaction({self.transaction_id}, {self.status})"





class MVCCDatabase:

    """MVCC数据库引擎"""



    def __init__(self):

        self.tables: Dict[str, Dict[str, Row]] = {}  # table_id -> {row_id -> Row}

        self.transactions: Dict[int, Transaction] = {}  # tid -> Transaction

        self.global_transaction_counter = 0

        

        # undo日志（用于回滚）

        self.undo_log: Dict[Tuple[int, str, str], Version] = {}  # (tid, table, row) -> old version

        

        # 统计

        self.stats = {

            "reads": 0,

            "writes": 0,

            "commits": 0,

            "aborts": 0

        }



    def begin_transaction(self, isolation_level: str = "READ_COMMITTED") -> Transaction:

        """

        开始新事务

        

        Args:

            isolation_level: 隔离级别（READ_COMMITTED, REPEATABLE_READ, SERIALIZABLE）

            

        Returns:

            Transaction对象

        """

        self.global_transaction_counter += 1

        tid = self.global_transaction_counter

        

        txn = Transaction(tid, isolation_level)

        self.transactions[tid] = txn

        

        # 获取快照信息

        txn.snapshot_xmax = self.global_transaction_counter

        

        # 收集活跃事务（用于快照）

        active = [t for t in self.transactions.values() if t.status == Transaction.STATUS_ACTIVE]

        txn.snapshot_xmin = min([t.transaction_id for t in active]) if active else tid

        

        return txn



    def commit(self, transaction_id: int) -> bool:

        """

        提交事务

        

        Args:

            transaction_id: 事务ID

            

        Returns:

            是否成功提交

        """

        if transaction_id not in self.transactions:

            return False

        

        txn = self.transactions[transaction_id]

        if txn.status != Transaction.STATUS_ACTIVE:

            return False

        

        # 更新事务状态

        txn.status = Transaction.STATUS_COMMITTED

        

        # 更新所有版本的commit时间

        self._update_version_commit_time(transaction_id)

        

        # 释放所有持有的锁

        self._release_locks(transaction_id)

        

        self.stats["commits"] += 1

        return True



    def abort(self, transaction_id: int) -> bool:

        """

        中止事务（回滚）

        

        Args:

            transaction_id: 事务ID

            

        Returns:

            是否成功中止

        """

        if transaction_id not in self.transactions:

            return False

        

        txn = self.transactions[transaction_id]

        txn.status = Transaction.STATUS_ABORTED

        

        # 回滚所有写操作

        self._rollback_writes(transaction_id)

        

        # 释放锁

        self._release_locks(transaction_id)

        

        self.stats["aborts"] += 1

        return True



    def _update_version_commit_time(self, transaction_id: int):

        """更新事务创建版本的commit时间"""

        for table_id, rows in self.tables.items():

            for row_id, row in rows.items():

                version = row.latest_version

                while version:

                    if version.transaction_id == transaction_id:

                        version.commit_at = time.time()

                        version.status = Transaction.STATUS_COMMITTED

                    version = version.prev_version



    def _rollback_writes(self, transaction_id: int):

        """回滚事务的所有写操作"""

        for table_id, rows in self.tables.items():

            for row_id, row in rows.items():

                version = row.latest_version

                prev = None

                

                # 找到该事务创建的版本

                while version and version.transaction_id == transaction_id:

                    # 恢复到前一个版本

                    if prev:

                        row.latest_version = prev

                    else:

                        # 没有更早的版本

                        if row.latest_version.prev_version:

                            row.latest_version = row.latest_version.prev_version

                        else:

                            # 整行都是这个事务创建的，可能需要删除

                            row.latest_version = None

                    

                    version_to_remove = version

                    version = prev

                    prev = version_to_remove.prev_version

                    version_to_remove.prev_version = None



    def _release_locks(self, transaction_id: int):

        """释放事务持有的所有锁"""

        for table_id, rows in self.tables.items():

            for row_id, row in rows.items():

                if row.exclusive_lock == transaction_id:

                    row.exclusive_lock = None



    def insert(self, transaction_id: int, table_id: str, row_id: str, values: Dict[str, Any]) -> bool:

        """

        插入行

        

        Args:

            transaction_id: 事务ID

            table_id: 表ID

            row_id: 行ID

            values: 字段值

            

        Returns:

            是否成功

        """

        if transaction_id not in self.transactions:

            return False

        

        txn = self.transactions[transaction_id]

        if txn.status != Transaction.STATUS_ACTIVE:

            return False

        

        # 确保表存在

        if table_id not in self.tables:

            self.tables[table_id] = {}

        

        # 检查行是否已存在

        if row_id in self.tables[table_id]:

            return False

        

        # 创建新行

        row = Row(row_id=row_id, table_id=table_id)

        

        # 创建版本

        version = Version(

            version_id=1,

            transaction_id=transaction_id,

            status=Transaction.STATUS_ACTIVE,

            created_at=time.time(),

            values=values.copy()

        )

        

        row.latest_version = version

        self.tables[table_id][row_id] = row

        

        # 记录到写集

        txn.write_set.append((table_id, row_id))

        

        self.stats["writes"] += 1

        return True



    def read(self, transaction_id: int, table_id: str, row_id: str) -> Optional[Dict[str, Any]]:

        """

        读取行（使用MVCC可见性判断）

        

        Args:

            transaction_id: 事务ID

            table_id: 表ID

            row_id: 行ID

            

        Returns:

            行的可见版本的值，None表示不可见或不存在

        """

        if transaction_id not in self.transactions:

            return None

        

        txn = self.transactions[transaction_id]

        self.stats["reads"] += 1

        

        if table_id not in self.tables or row_id not in self.tables[table_id]:

            return None

        

        row = self.tables[table_id][row_id]

        version = row.latest_version

        

        # 遍历版本链，找到可见版本

        while version:

            if self._is_version_visible(txn, version):

                return version.values.copy()

            version = version.prev_version

        

        return None



    def _is_version_visible(self, txn: Transaction, version: Version) -> bool:

        """

        判断版本对事务是否可见

        

        Args:

            txn: 读取事务

            version: 数据版本

            

        Returns:

            是否可见

        """

        # 版本由未提交的事务创建 -> 不可见

        if version.status == Transaction.STATUS_ACTIVE:

            # 检查事务是否就是当前事务

            if version.transaction_id == txn.transaction_id:

                return True  # 自己创建的可见

            return False

        

        # 根据隔离级别判断

        if txn.isolation_level == "READ_COMMITTED":

            # READ_COMMITTED: 只有已提交版本的可见

            return version.status == Transaction.STATUS_COMMITTED

        

        elif txn.isolation_level == "REPEATABLE_READ":

            # REPEATABLE_READ: 基于事务开始时的快照

            if version.commit_at and version.commit_at > txn.start_time:

                return False

            

            if version.transaction_id >= txn.snapshot_xmax:

                return False

            

            return True

        

        elif txn.isolation_level == "SERIALIZABLE":

            # SERIALIZABLE: 最严格

            return self._is_version_visible_serializable(txn, version)

        

        return False



    def _is_version_visible_serializable(self, txn: Transaction, version: Version) -> bool:

        """SERIALIZABLE隔离级别下的可见性判断"""

        if version.commit_at and version.commit_at > txn.start_time:

            return False

        return True



    def update(self, transaction_id: int, table_id: str, row_id: str,

               new_values: Dict[str, Any]) -> bool:

        """

        更新行（创建新版本）

        

        Args:

            transaction_id: 事务ID

            table_id: 表ID

            row_id: 行ID

            new_values: 新值

            

        Returns:

            是否成功

        """

        if transaction_id not in self.transactions:

            return False

        

        txn = self.transactions[transaction_id]

        if txn.status != Transaction.STATUS_ACTIVE:

            return False

        

        if table_id not in self.tables or row_id not in self.tables[table_id]:

            return False

        

        row = self.tables[table_id][row_id]

        

        # 检查排他锁

        if row.exclusive_lock is not None and row.exclusive_lock != transaction_id:

            return False

        

        # 获取旧版本（用于undo）

        old_version = row.latest_version

        

        # 创建新版本

        new_version = Version(

            version_id=old_version.version_id + 1 if old_version else 1,

            transaction_id=transaction_id,

            status=Transaction.STATUS_ACTIVE,

            created_at=time.time(),

            values=new_values.copy()

        )

        

        # 链接到版本链

        new_version.prev_version = old_version

        row.latest_version = new_version

        

        # 记录undo日志

        self.undo_log[(transaction_id, table_id, row_id)] = old_version

        

        # 记录到写集

        txn.write_set.append((table_id, row_id))

        

        self.stats["writes"] += 1

        return True



    def delete(self, transaction_id: int, table_id: str, row_id: str) -> bool:

        """

        删除行（标记为删除）

        

        Args:

            transaction_id: 事务ID

            table_id: 表ID

            row_id: 行ID

            

        Returns:

            是否成功

        """

        if transaction_id not in self.transactions:

            return False

        

        txn = self.transactions[transaction_id]

        if txn.status != Transaction.STATUS_ACTIVE:

            return False

        

        if table_id not in self.tables or row_id not in self.tables[table_id]:

            return False

        

        row = self.tables[table_id][row_id]

        

        # 标记删除（通过创建一个特殊的墓碑版本）

        tombstone = Version(

            version_id=row.latest_version.version_id + 1,

            transaction_id=transaction_id,

            status=Transaction.STATUS_ACTIVE,

            created_at=time.time(),

            values={"__deleted__": True}

        )

        tombstone.prev_version = row.latest_version

        row.latest_version = tombstone

        

        txn.write_set.append((table_id, row_id))

        

        self.stats["writes"] += 1

        return True



    def get_version_chain(self, table_id: str, row_id: str) -> List[Version]:

        """获取版本链"""

        if table_id not in self.tables or row_id not in self.tables[table_id]:

            return []

        

        row = self.tables[table_id][row_id]

        chain = []

        version = row.latest_version

        

        while version:

            chain.append(version)

            version = version.prev_version

        

        return chain





# ==================== 测试代码 ====================

if __name__ == "__main__":

    print("=" * 70)

    print("多版本并发控制（MVCC）测试")

    print("=" * 70)



    db = MVCCDatabase()



    # 场景1：READ_COMMITTED隔离级别

    print("\n--- 场景1：READ_COMMITTED - 读写不阻塞 ---")

    

    # T1: 插入数据

    txn1 = db.begin_transaction("READ_COMMITTED")

    print(f"  T1 开始 (隔离级别: {txn1.isolation_level})")

    

    db.insert(txn1.transaction_id, "accounts", "acc_1", {"name": "Alice", "balance": 1000})

    print(f"  T1 插入 acc_1: balance=1000")

    

    # T2: 在T1提交前读取

    txn2 = db.begin_transaction("READ_COMMITTED")

    result = db.read(txn2.transaction_id, "accounts", "acc_1")

    print(f"  T2 读取 acc_1 (T1未提交): {result}")  # 应该看不到

    

    # T1提交

    db.commit(txn1.transaction_id)

    print(f"  T1 提交")

    

    # T2再次读取

    result = db.read(txn2.transaction_id, "accounts", "acc_1")

    print(f"  T2 再次读取 acc_1: {result}")  # 现在应该能看到



    # 场景2：版本链演示

    print("\n--- 场景2：多版本链 ---")

    

    txn3 = db.begin_transaction("READ_COMMITTED")

    db.update(txn3.transaction_id, "accounts", "acc_1", {"name": "Alice", "balance": 900})

    print(f"  T3 更新 acc_1: balance=900")

    

    txn4 = db.begin_transaction("READ_COMMITTED")

    db.update(txn4.transaction_id, "accounts", "acc_1", {"name": "Alice", "balance": 800})

    print(f"  T4 更新 acc_1: balance=800")

    

    db.commit(txn3.transaction_id)

    db.commit(txn4.transaction_id)

    

    # 查看版本链

    chain = db.get_version_chain("accounts", "acc_1")

    print(f"  版本链长度: {len(chain)}")

    for v in chain:

        status = "COMMITTED" if v.commit_at else "ACTIVE"

        print(f"    版本{v.version_id}: T{v.transaction_id}, {status}, balance={v.values.get('balance')}")



    # 场景3：快照读 vs 当前读

    print("\n--- 场景3：快照隔离 ---")

    

    txn5 = db.begin_transaction("REPEATABLE_READ")

    print(f"  T5 开始 REPEATABLE_READ")

    

    balance1 = db.read(txn5.transaction_id, "accounts", "acc_1")

    print(f"  T5 第一次读取: balance={balance1['balance']}")

    

    # 另一个事务修改

    txn6 = db.begin_transaction("READ_COMMITTED")

    db.update(txn6.transaction_id, "accounts", "acc_1", {"name": "Alice", "balance": 500})

    db.commit(txn6.transaction_id)

    print(f"  T6 更新 balance=500 并提交")

    

    # T5再次读取（应该还是旧值）

    balance2 = db.read(txn5.transaction_id, "accounts", "acc_1")

    print(f"  T5 第二次读取: balance={balance2['balance']} (快照读，旧值)")



    # 场景4：回滚

    print("\n--- 场景4：事务回滚 ---")

    

    txn7 = db.begin_transaction("READ_COMMITTED")

    db.insert(txn7.transaction_id, "accounts", "acc_2", {"name": "Bob", "balance": 2000})

    print(f"  T7 插入 acc_2: balance=2000")

    

    db.update(txn7.transaction_id, "accounts", "acc_2", {"name": "Bob", "balance": 1500})

    print(f"  T7 更新 acc_2: balance=1500")

    

    # 回滚

    db.abort(txn7.transaction_id)

    print(f"  T7 回滚")

    

    # 验证acc_2不存在

    result = db.read(txn5.transaction_id, "accounts", "acc_2")  # 用一个已存在的事务

    print(f"  acc_2 是否存在: {result}")



    print("\n" + "=" * 70)

    print("统计:", db.stats)

    print("=" * 70)

