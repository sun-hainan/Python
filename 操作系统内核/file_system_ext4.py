# -*- coding: utf-8 -*-
"""
算法实现：操作系统内核 / file_system_ext4

本文件实现 file_system_ext4 相关的算法功能。
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


# 块大小
BLOCK_SIZE = 4096
# inode大小
INODE_SIZE = 256


class Extent:
    """Extent（连续块）"""
    def __init__(self, start: int, length: int):
        self.ee_start = start    # 起始块号
        self.ee_len = length    # 长度（块数）
        self.ee_block = 0       # 逻辑块号


class ExtentNode:
    """Extent树节点"""
    def __init__(self):
        self.eh_entries = 0  # 条目数
        self.eh_max = 0     # 最大条目数
        self.eh_depth = 0   # 树深度
        self.extents: List[Extent] = []


@dataclass
class Ext4Inode:
    """ext4 inode"""
    i_mode: int = 0          # 文件类型和权限
    i_uid: int = 0            # UID
    i_size: int = 0          # 文件大小
    i_atime: int = 0         # 访问时间
    i_ctime: int = 0         # 修改时间
    i_mtime: int = 0         # 变更时间
    i_dtime: int = 0         # 删除时间
    i_gid: int = 0           # GID
    i_links_count: int = 1   # 硬链接数
    i_blocks: int = 0        # 块数（512字节为单位）
    i_flags: int = 0        # 标志

    # extents
    i_extent_tree: Optional[ExtentNode] = None

    # 文件数据块
    i_block: List[int] = field(default_factory=lambda: [0] * 15)


class Ext4SuperBlock:
    """ext4超级块"""
    def __init__(self):
        self.s_inodes_count = 0          # inode总数
        self.s_blocks_count = 0         # 块总数
        self.s_r_blocks_count = 0       # 预留块数
        self.s_free_blocks_count = 0    # 空闲块数
        self.s_free_inodes_count = 0   # 空闲inode数
        self.s_first_data_block = 0     # 第一个数据块
        self.s_log_block_size = 0        # 块大小
        self.s_blocks_per_group = 0     # 每组块数
        self.s_inodes_per_group = 0      # 每组inode数
        self.s_magic = 0xEF53            # 魔数
        self.s_state = 0                # 文件系统状态
        self.s_first_ino = 11           # 第一个非预留inode


class Ext4GroupDescriptor:
    """块组描述符"""
    def __init__(self, group: int):
        self.bg_block_bitmap = 0         # 块位图块号
        self.bg_inode_bitmap = 0         # inode位图块号
        self.bg_inode_table = 0         # inode表块号
        self.bg_free_blocks_count = 0   # 空闲块数
        self.bg_free_inodes_count = 0   # 空闲inode数
        self.bg_used_dirs_count = 0      # 目录数
        self.bg_block_group = group


class Ext4FileSystem:
    """
    ext4文件系统

    使用extents管理文件数据。
    """

    def __init__(self, device_size: int):
        self.device_size = device_size

        # 超级块
        self.sb = Ext4SuperBlock()

        # 块组描述符表
        self.group_descriptors: List[Ext4GroupDescriptor] = []

        # inode表
        self.inodes: Dict[int, Ext4Inode] = {}

        # 位图
        self.block_bitmap: Set[int] = set()
        self.inode_bitmap: Set[int] = set()

        # 初始化
        self._init_filesystem()

    def _init_filesystem(self):
        """初始化文件系统"""
        blocks = self.device_size // BLOCK_SIZE

        # 设置超级块
        self.sb.s_blocks_count = blocks
        self.sb.s_inodes_count = blocks // 4
        self.sb.s_free_blocks_count = blocks - 1
        self.sb.s_free_inodes_count = self.sb.s_inodes_count - 11

        # 计算块组数
        blocks_per_group = 32768
        num_groups = (blocks + blocks_per_group - 1) // blocks_per_group

        # 创建块组描述符
        for i in range(num_groups):
            gd = Ext4GroupDescriptor(i)
            self.group_descriptors.append(gd)

        # 创建根目录inode
        root_inode = Ext4Inode()
        root_inode.i_mode = 0o40755  # d---r-xr-x
        root_inode.i_size = BLOCK_SIZE
        root_inode.i_extent_tree = ExtentNode()
        self.inodes[2] = root_inode  # ext4的根目录inode是2

    def allocate_block(self) -> Optional[int]:
        """分配块"""
        for block in range(1, self.sb.s_blocks_count):
            if block not in self.block_bitmap:
                self.block_bitmap.add(block)
                self.sb.s_free_blocks_count -= 1
                return block
        return None

    def free_block(self, block: int):
        """释放块"""
        if block in self.block_bitmap:
            self.block_bitmap.remove(block)
            self.sb.s_free_blocks_count += 1

    def allocate_inode(self) -> Optional[int]:
        """分配inode"""
        for ino in range(11, self.sb.s_inodes_count):
            if ino not in self.inode_bitmap:
                self.inode_bitmap.add(ino)
                self.sb.s_free_inodes_count -= 1
                return ino
        return None

    def create_file(self, parent_ino: int, name: str) -> Optional[int]:
        """创建文件"""
        ino = self.allocate_inode()
        if ino is None:
            return None

        inode = Ext4Inode()
        inode.i_mode = 0o100644  # 普通文件
        self.inodes[ino] = inode

        print(f"  创建文件 {name}, inode={ino}")
        return ino

    def write_extent(self, inode: Ext4Inode, start_block: int, data_blocks: List[int]):
        """写入extent"""
        if inode.i_extent_tree is None:
            inode.i_extent_tree = ExtentNode()

        # 创建extent
        extent = Extent(start=data_blocks[0], length=len(data_blocks))
        inode.i_extent_tree.extents.append(extent)

    def get_file_blocks(self, inode: Ext4Inode) -> List[int]:
        """获取文件的所有块"""
        blocks = []
        if inode.i_extent_tree:
            for extent in inode.i_extent_tree.extents:
                for i in range(extent.ee_len):
                    blocks.append(extent.ee_start + i)
        return blocks


def simulate_ext4():
    """
    模拟ext4文件系统
    """
    print("=" * 60)
    print("ext4文件系统")
    print("=" * 60)

    # 创建文件系统
    fs = Ext4FileSystem(device_size=100 * 1024 * 1024)  # 100MB

    print("\n文件系统信息:")
    print("-" * 50)
    print(f"  总块数: {fs.sb.s_blocks_count}")
    print(f"  总inode数: {fs.sb.s_inodes_count}")
    print(f"  空闲块数: {fs.sb.s_free_blocks_count}")
    print(f"  块组数: {len(fs.group_descriptors)}")

    # 创建文件
    print("\n文件操作:")
    print("-" * 50)

    ino = fs.create_file(2, "test.txt")
    if ino:
        inode = fs.inodes[ino]
        print(f"  文件大小: {inode.i_size}")
        print(f"  文件模式: 0o{inode.i_mode:o}")

    # 分配数据块
    print("\n分配数据块:")
    data_blocks = []
    for i in range(8):
        block = fs.allocate_block()
        if block:
            data_blocks.append(block)
            print(f"  分配块 {i}: block #{block}")

    # 写入extent
    if ino:
        fs.write_extent(fs.inodes[ino], 0, data_blocks)
        print(f"\n  extent树深度: {fs.inodes[ino].i_extent_tree.eh_depth}")
        print(f"  extent数量: {len(fs.inodes[ino].i_extent_tree.extents)}")

    # ext4特性总结
    print("\n" + "=" * 60)
    print("ext4 vs ext3 主要改进")
    print("=" * 60)
    print("""
    ┌─────────────┬─────────────────────────────────────────┐
    │ 特性         │ 改进                                     │
    ├─────────────┼─────────────────────────────────────────┤
    │ Extents     │ 减少元数据开销，支持大文件               │
    │ 延迟分配    │ 合并写入操作，提高性能                 │
    │ 日志校验和   │ 检测日志损坏                           │
    │ 无限制目录   │ 子目录数量无限制                       │
    │ 快速fsck    │ 检查点机制                             │
    │ 多块分配    │ 一次分配多个块                         │
    └─────────────┴─────────────────────────────────────────┘
    """)


if __name__ == "__main__":
    simulate_ext4()
