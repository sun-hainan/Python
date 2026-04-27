# -*- coding: utf-8 -*-
"""
算法实现：数据库内核 / replication

本文件实现 replication 相关的算法功能。
"""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import IntEnum
import time
import threading

# ========== Binlog格式 ==========

class BinlogEventType(IntEnum):
    """Binlog事件类型"""
    QUERY = 1           # 查询事件（如DDL）
    TABLE_MAP = 2       # 表映射事件
    WRITE_ROWS = 3      # 插入行事件
    UPDATE_ROWS = 4     # 更新行事件
    DELETE_ROWS = 5     # 删除行事件
    XID = 6             # 事务提交事件
    GTID = 7            # GTID事件


@dataclass
class BinlogPosition:
    """Binlog位置"""
    file_name: str          # binlog文件名
    offset: int             # 文件偏移量
    gtid: Optional[str] = None  # GTID（如果使用GTID模式）
    
    def __repr__(self):
        return f"BinlogPosition({self.file_name}:{self.offset}, gtid={self.gtid})"


@dataclass
class RowEvent:
    """行事件"""
    table_id: int
    table_name: str
    event_type: BinlogEventType
    rows: List[Dict[str, Any]]  # 变更的行
    before_image: bool = False   # 是否有修改前的镜像
    timestamp: float = field(default_factory=time.time)
    
    def __repr__(self):
        return f"RowEvent({self.table_name}, {self.event_type.name}, {len(self.rows)} rows)"


class BinlogWriter:
    """
    Binlog写入器
    将数据库变更写入Binlog
    """
    
    def __init__(self, log_dir: str = "./binlog"):
        self.log_dir = log_dir
        self.current_file: Optional[str] = None
        self.current_offset = 0
        self.sequence_number = 0
        self.events: List[bytes] = []
    
    def write_event(self, event_type: BinlogEventType, 
                    data: Any, tx_id: int = 0) -> BinlogPosition:
        """
        写入Binlog事件
        返回: 写入后的位置
        """
        # 构造事件头
        event_header = struct.pack("<IBQI", 
                                  event_type.value,  # 事件类型
                                  tx_id,             # 事务ID
                                  self.current_offset,  # 位置
                                  int(time.time())  # 时间戳
        )
        
        # 序列化事件数据
        event_data = self._serialize_event(event_type, data)
        
        # 组合完整事件
        event_bytes = event_header + event_data
        self.events.append(event_bytes)
        
        pos = BinlogPosition(
            file_name=self.current_file or "binlog.000001",
            offset=self.current_offset,
            gtid=self._generate_gtid(tx_id) if tx_id else None
        )
        
        self.current_offset += len(event_bytes)
        return pos
    
    def _serialize_event(self, event_type: BinlogEventType, data: Any) -> bytes:
        """序列化事件数据"""
        if event_type == BinlogEventType.ROW_EVENT or isinstance(data, RowEvent):
            return self._serialize_row_event(data)
        return str(data).encode('utf-8')
    
    def _serialize_row_event(self, event: RowEvent) -> bytes:
        """序列化行事件"""
        result = f"{event.table_name}|".encode('utf-8')
        
        for row in event.rows:
            row_data = ",".join(f"{k}={v}" for k, v in row.items())
            result += f"{row_data};".encode('utf-8')
        
        return result
    
    def _generate_gtid(self, tx_id: int) -> str:
        """生成GTID"""
        return f"{self.sequence_number}-{tx_id}-{int(time.time() * 1000)}"
    
    def rotate(self, new_file: str):
        """轮转Binlog文件"""
        self.current_file = new_file
        self.current_offset = 0
        self.sequence_number += 1
    
    def flush(self):
        """刷盘（模拟）"""
        # 实际应该写入磁盘
        pass


# ========== 复制协议 ==========

@dataclass
class ReplicationSlot:
    """复制槽（Master端）"""
    slot_name: str
    confirmed_flush: BinlogPosition  # 已确认刷盘的位点
    restart_lsn: BinlogPosition     # 允许从该位点重启
    client_id: Optional[int] = None
    
    def __repr__(self):
        return f"ReplicationSlot({self.slot_name}, confirmed={self.confirmed_flush})"


class MasterState:
    """主库状态"""
    def __init__(self):
        self.server_id = 0
        self.binlog_files: List[str] = []
        self.current_binlog: Optional[BinlogPosition] = None
        self.gtid_executed: Dict[str, int] = {}  # gtid -> tx_count
        self.replication_slots: Dict[str, ReplicationSlot] = {}


@dataclass
class ReplicaState:
    """从库状态"""
    master_server_id: int
    master_link: str                          # Master连接信息
    replicated_position: BinlogPosition        # 已复制的位置
    last_io_time: float = 0.0                 # 上次IO线程活动时间
    io_running: bool = False                  # IO线程是否运行
    sql_running: bool = False                 # SQL线程是否运行
    replica_io_err: Optional[str] = None    # IO错误
    replica_sql_err: Optional[str] = None   # SQL错误
    
    def __repr__(self):
        return f"ReplicaState(pos={self.replicated_position}, io={self.io_running}, sql={self.sql_running})"


class GTIDManager:
    """
    GTID（Global Transaction Identifier）管理器
    提供全局唯一的事务ID，简化复制位点管理
    """
    
    def __init__(self, server_uuid: str):
        self.server_uuid = server_uuid
        self.executed: Dict[str, List[int]] = {}  # source_id -> [interval列表]
        self.auto_position_threshold = 1000       # 自动定位阈值
    
    def generate_gtid(self, tx_id: int) -> str:
        """生成GTID"""
        return f"{self.server_uuid}:{tx_id}"
    
    def parse_gtid(self, gtid: str) -> Tuple[str, int]:
        """解析GTID为(source_id, tx_num)"""
        parts = gtid.split(":")
        return parts[0], int(parts[1])
    
    def add_executed_gtid(self, gtid: str):
        """记录已执行的GTID"""
        source_id, tx_num = self.parse_gtid(gtid)
        
        if source_id not in self.executed:
            self.executed[source_id] = []
        
        self.executed[source_id].append(tx_num)
        self.executed[source_id].sort()
    
    def get_executed_intervals(self, source_id: str) -> List[Tuple[int, int]]:
        """
        获取已执行的GTID区间
        用于复制过滤
        """
        if source_id not in self.executed:
            return []
        
        intervals = []
        tx_list = self.executed[source_id]
        
        # 合并连续的事务号为区间
        start = tx_list[0]
        end = start
        
        for tx_num in tx_list[1:]:
            if tx_num == end + 1:
                end += 1
            else:
                intervals.append((start, end))
                start = tx_num
                end = tx_num
        
        intervals.append((start, end))
        return intervals
    
    def is_gtid_executed(self, gtid: str) -> bool:
        """检查GTID是否已执行"""
        source_id, tx_num = self.parse_gtid(gtid)
        
        if source_id not in self.executed:
            return False
        
        return tx_num in self.executed[source_id]
    
    def compute_new_gtids(self, source_id: str, 
                          available_intervals: List[Tuple[int, int]]) -> List[str]:
        """
        计算需要复制的GTID集合
        available: Master上可用的区间
        返回: 需要复制的GTID列表
        """
        need_replicate = []
        executed_intervals = self.get_executed_intervals(source_id)
        
        for start, end in available_intervals:
            # 检查已执行区间
            for exec_start, exec_end in executed_intervals:
                if end < exec_start:
                    # 区间完全未执行
                    for tx_num in range(start, end + 1):
                        need_replicate.append(self.generate_gtid(tx_num))
                elif start > exec_end:
                    # 区间部分未执行
                    for tx_num in range(max(start, exec_end + 1), end + 1):
                        need_replicate.append(self.generate_gtid(tx_num))
        
        return need_replicate


class ReplicationFilter:
    """
    复制过滤器
    过滤不需要复制的表或数据库
    """
    
    def __init__(self):
        self.do_db: List[str] = []           # 需要复制的数据库
        self.ignore_db: List[str] = []        # 忽略的数据库
        self.do_table: List[str] = []         # 需要复制的表
        self.ignore_table: List[str] = []     # 忽略的表
        self.replicate_wild_do_table: List[str] = []   # 模糊匹配需要复制
        self.replicate_wild_ignore_table: List[str] = []  # 模糊匹配忽略
    
    def should_replicate(self, db_name: str, table_name: str) -> bool:
        """判断是否应该复制"""
        # 检查精确匹配
        full_name = f"{db_name}.{table_name}"
        
        if self.do_table and full_name in self.do_table:
            return True
        if full_name in self.ignore_table:
            return False
        
        # 检查模糊匹配
        for pattern in self.replicate_wild_do_table:
            if self._match_wildcard(full_name, pattern):
                return True
        
        for pattern in self.replicate_wild_ignore_table:
            if self._match_wildcard(full_name, pattern):
                return False
        
        # 检查数据库级别
        if self.do_db and db_name in self.do_db:
            return True
        if db_name in self.ignore_db:
            return False
        
        return len(self.do_db) == 0  # 如果没有do_db规则，默认复制
    
    def _match_wildcard(self, name: str, pattern: str) -> bool:
        """简单的通配符匹配（*）"""
        import fnmatch
        return fnmatch.fnmatch(name, pattern)


class ReplicationIOThread:
    """
    复制IO线程
    从主库拉取Binlog并写入中继日志
    """
    
    def __init__(self, replica_state: ReplicaState, 
                 master_state: MasterState,
                 gtid_manager: GTIDManager,
                 binlog_writer: BinlogWriter):
        self.replica_state = replica_state
        self.master_state = master_state
        self.gtid_manager = gtid_manager
        self.binlog_writer = binlog_writer
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def start(self):
        """启动IO线程"""
        self.running = True
        self.replica_state.io_running = True
        self.thread = threading.Thread(target=self._io_loop)
        self.thread.start()
    
    def stop(self):
        """停止IO线程"""
        self.running = False
        self.replica_state.io_running = False
        if self.thread:
            self.thread.join()
    
    def _io_loop(self):
        """IO线程主循环"""
        while self.running:
            # 模拟从主库读取Binlog
            # 实际实现需要网络通信
            pass


if __name__ == "__main__":
    print("=" * 60)
    print("主从复制演示")
    print("=" * 60)
    
    # 1. Binlog写入
    print("\n--- Binlog写入 ---")
    binlog = BinlogWriter()
    
    # 模拟事务1：INSERT
    tx1_pos = binlog.write_event(
        BinlogEventType.WRITE_ROWS,
        RowEvent(
            table_id=1,
            table_name="orders",
            event_type=BinlogEventType.WRITE_ROWS,
            rows=[{"id": 1, "amount": 100}, {"id": 2, "amount": 200}]
        ),
        tx_id=1
    )
    print(f"事务1写入位置: {tx1_pos}")
    
    # 模拟事务2：UPDATE
    tx2_pos = binlog.write_event(
        BinlogEventType.UPDATE_ROWS,
        RowEvent(
            table_id=1,
            table_name="orders",
            event_type=BinlogEventType.UPDATE_ROWS,
            rows=[{"id": 1, "amount": 150}]
        ),
        tx_id=2
    )
    print(f"事务2写入位置: {tx2_pos}")
    
    # 2. GTID管理
    print("\n--- GTID管理 ---")
    gtid_mgr = GTIDManager("server-001")
    
    # 生成GTID
    gtid1 = gtid_mgr.generate_gtid(1)
    gtid2 = gtid_mgr.generate_gtid(2)
    print(f"GTID1: {gtid1}")
    print(f"GTID2: {gtid2}")
    
    # 标记为已执行
    gtid_mgr.add_executed_gtid(gtid1)
    gtid_mgr.add_executed_gtid(gtid2)
    
    # 查询已执行区间
    intervals = gtid_mgr.get_executed_intervals("server-001")
    print(f"已执行GTID区间: {intervals}")
    
    # 3. 复制过滤
    print("\n--- 复制过滤 ---")
    repl_filter = ReplicationFilter()
    repl_filter.do_db = ["app_db"]
    repl_filter.ignore_table = ["app_db.sensitive_data"]
    
    test_tables = [
        ("app_db", "users"),
        ("app_db", "orders"),
        ("app_db", "sensitive_data"),
        ("other_db", "data")
    ]
    
    for db, table in test_tables:
        result = repl_filter.should_replicate(db, table)
        print(f"  {db}.{table}: {'复制' if result else '忽略'}")
    
    # 4. 从库状态
    print("\n--- 从库状态 ---")
    replica_state = ReplicaState(
        master_server_id=1,
        master_link="mysql://master:3306",
        replicated_position=BinlogPosition("binlog.000001", 1024),
        io_running=True,
        sql_running=True
    )
    print(f"从库状态: {replica_state}")
    
    print("\n复制模式对比:")
    print("  传统位置复制: 依赖文件名+偏移量，需精确追踪")
    print("  GTID复制: 全局唯一事务ID，自动定位，无需记录文件偏移量")
    print("  优势: 故障切换简单，避免复制位点漂移")
