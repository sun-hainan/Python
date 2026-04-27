# -*- coding: utf-8 -*-

"""

算法实现：15_操作系统与调度 / io_uring_impl



本文件实现 io_uring_impl 相关的算法功能。

"""



from enum import IntEnum

from dataclasses import dataclass, field

from typing import Optional, Callable

import threading





class IORingOp(IntEnum):

    """io_uring操作码"""

    NOP = 0

    READ = 1

    WRITE = 2

    POLL_ADD = 6

    SYNC_FILE_RANGE = 20

    OPENAT = 49

    CLOSE = 41

    FSYNC = 47

    READ_FIXED = 27

    WRITE_FIXED = 28





class IOUCqeFlags(IntEnum):

    """Completion Queue Entry 标志"""

    CQE_F_MORE = 1 << 0  # 同一请求有多个cqe





@dataclass

class SubmissionEntry:

    """SQ（提交队列）条目"""

    opcode: IORingOp

    fd: int = -1

    addr: int = 0        # 用户缓冲区地址

    len: int = 0         # 缓冲区长度

    user_data: int = 0   # 标识符（传回CQE）

    flags: int = 0      # IOSQE_* 标志

    offset: int = 0      # 文件偏移

    read_offset: int = 0 # READ_FIXED的偏移





@dataclass

class CompletionEntry:

    """CQ（完成队列）条目"""

    user_data: int   # 关联的SQe标识

    res: int         # 结果（返回值或-errno）

    flags: int       # CQE_F_*





class RingBuffer:

    """环形缓冲区（共享内存模拟）"""



    def __init__(self, capacity: int):

        self.capacity = capacity

        self.entries = [None] * capacity

        self.head = 0   # 消费者索引

        self.tail = 0   # 生产者索引

        self.lock = threading.Lock()



    def push(self, item) -> bool:

        """生产者写入（不覆盖）"""

        with self.lock:

            next_tail = (self.tail + 1) % self.capacity

            if next_tail == self.head:

                return False  # 满

            self.entries[self.tail] = item

            self.tail = next_tail

            return True



    def pop(self) -> Optional:

        """消费者读取"""

        with self.lock:

            if self.head == self.tail:

                return None  # 空

            item = self.entries[self.head]

            self.head = (self.head + 1) % self.capacity

            return item





class IORingContext:

    """io_uring上下文"""



    def __init__(self, depth: int = 32):

        self.sq_depth = depth

        self.cq_depth = depth * 2  # CQ通常比SQ大



        # 环形缓冲区

        self.sq_ring = RingBuffer(depth)   # Submission Queue

        self.cq_ring = RingBuffer(self.cq_depth)  # Completion Queue



        # 内存映射区域（简化）

        self.sq_entries = [SubmissionEntry(opcode=IORingOp.NOP) for _ in range(depth)]

        self.cq_entries = [CompletionEntry(user_data=0, res=0, flags=0) for _ in range(self.cq_depth)]



        # 状态

        self.submitted = 0

        self.completed = 0

        self.is_setup = True



    def get_sqe(self) -> Optional[SubmissionEntry]:

        """获取空闲的SQ条目"""

        sqe = SubmissionEntry(opcode=IORingOp.NOP, user_data=self.submitted)

        if self.sq_ring.push(sqe):

            return sqe

        return None



    def submit_sqe(self, sqe: SubmissionEntry) -> int:

        """提交SQ条目到内核"""

        # 找到对应的数组索引

        for i in range(self.sq_depth):

            if self.sq_entries[i].opcode == IORingOp.NOP:

                self.sq_entries[i] = sqe

                break

        self.submitted += 1

        return 0



    def get_cqe(self) -> Optional[CompletionEntry]:

        """获取完成的CQE"""

        return self.cq_ring.pop()



    def advance_cq(self, count: int):

        """推进CQ头指针"""

        for _ in range(count):

            self.cq_ring.pop()





class IORingFile:

    """包装文件描述符进行io_uring操作"""



    def __init__(self, ring: IORingContext, fd: int):

        self.ring = ring

        self.fd = fd



    def read(self, buf: bytearray, offset: int = 0) -> int:

        """异步读操作"""

        sqe = self.ring.get_sqe()

        if sqe is None:

            return -1



        sqe.opcode = IORingOp.READ

        sqe.fd = self.fd

        sqe.addr = id(buf)  # 简化：使用Python对象地址

        sqe.len = len(buf)

        sqe.offset = offset

        sqe.user_data = id(buf)  # 用buf的id作为标识



        self.ring.submit_sqe(sqe)

        return 0



    def write(self, data: bytes, offset: int = 0) -> int:

        """异步写操作"""

        sqe = self.ring.get_sqe()

        if sqe is None:

            return -1



        sqe.opcode = IORingOp.WRITE

        sqe.fd = self.fd

        sqe.addr = id(data)

        sqe.len = len(data)

        sqe.offset = offset

        sqe.user_data = id(data)



        self.ring.submit_sqe(sqe)

        return 0



    def fsync(self) -> int:

        """文件同步"""

        sqe = self.ring.get_sqe()

        if sqe is None:

            return -1



        sqe.opcode = IORingOp.FSYNC

        sqe.fd = self.fd

        sqe.user_data = self.fd



        self.ring.submit_sqe(sqe)

        return 0





def simulate_io_uring():

    """模拟io_uring操作流程"""

    ring = IORingContext(depth=16)



    print("=== io_uring 模拟演示 ===")

    print(f"SQ深度: {ring.sq_depth}, CQ深度: {ring.cq_depth}")



    # 模拟提交读请求

    print("\n--- 提交读请求 ---")

    sqe = ring.get_sqe()

    if sqe:

        sqe.opcode = IORingOp.READ

        sqe.fd = 5

        sqe.user_data = 1001

        ring.submit_sqe(sqe)

        print(f"提交READ: fd=5, user_data=1001")



    # 模拟提交写请求

    print("\n--- 提交写请求 ---")

    sqe = ring.get_sqe()

    if sqe:

        sqe.opcode = IORingOp.WRITE

        sqe.fd = 5

        sqe.user_data = 1002

        ring.submit_sqe(sqe)

        print(f"提交WRITE: fd=5, user_data=1002")



    # 模拟完成事件

    print("\n--- 模拟完成事件 ---")

    cqe = CompletionEntry(user_data=1001, res=1024, flags=0)

    ring.cq_ring.push(cqe)

    cqe = CompletionEntry(user_data=1002, res=512, flags=0)

    ring.cq_ring.push(cqe)



    # 收集完成结果

    print("收集CQE:")

    while True:

        cqe = ring.get_cqe()

        if cqe is None:

            break

        ring.completed += 1

        print(f"  user_data={cqe.user_data}, res={cqe.res}")



    print(f"\n提交: {ring.submitted}, 完成: {ring.completed}")





if __name__ == "__main__":

    simulate_io_uring()



    print("\n=== io_uring vs 传统系统调用 ===")

    print("传统: read/write → 每次系统调用 → 用户态/内核态切换")

    print("io_uring: 批量提交 → 共享内存 → 减少系统调用")

    print("\n关键优势:")

    print("1. 零系统调用提交（sqe直接写入共享内存）")

    print("2. 批量完成通知（CQE轮询）")

    print("3. 支持固定文件缓冲（fixed file）")

    print("4. POLL模式无需epoll")

    print("5. 支持顺序读写（SQE顺序）")

