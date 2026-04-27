# -*- coding: utf-8 -*-

"""

算法实现：操作系统内核 / vfs



本文件实现 vfs 相关的算法功能。

"""



from typing import Dict, List, Optional, Set

from dataclasses import dataclass, field

from enum import Enum

import time





class FileType(Enum):

    """文件类型"""

    REGULAR_FILE = "regular"

    DIRECTORY = "directory"

    CHARACTER_DEVICE = "char_device"

    BLOCK_DEVICE = "block_device"

    FIFO = "fifo"

    SOCKET = "socket"

    SYMBOLIC_LINK = "symlink"





@dataclass

class SuperBlock:

    """超级块 - 文件系统元信息"""

    s_blocksize: int = 4096           # 块大小

    s_maxbytes: int = 1024 * 1024 * 1024  # 最大文件大小

    s_magic: int = 0xEF53            # 文件系统魔数

    s_op: Optional['super_operations'] = None  # 超级块操作

    s_root: Optional['inode'] = None  # 根目录inode



    # 统计信息

    s_files: int = 0                 # 文件数

    s_ifree: int = 0                 # 空闲inode数

    s_iused: int = 0                 # 已用inode数

    s_blocks: int = 0                # 总块数

    s_bfree: int = 0                 # 空闲块数





@dataclass

class Inode:

    """索引节点 (inode) - 文件元信息"""

    i_ino: int                       # inode编号

    i_mode: int = 0                  # 文件类型和权限

    i_uid: int = 0                   # 用户ID

    i_gid: int = 0                   # 组ID

    i_size: int = 0                  # 文件大小

    i_atime: int = 0                 # 访问时间

    i_mtime: int = 0                 # 修改时间

    i_ctime: int = 0                 # 改变时间



    # 文件类型

    i_filetype: FileType = FileType.REGULAR_FILE



    # 引用计数

    i_count: int = 1                 # 引用计数

    i_nlink: int = 1                 # 硬链接数



    # 操作函数

    i_op: Optional['inode_operations'] = None

    i_fop: Optional['file_operations'] = None



    # 文件数据

    i_data: Optional[bytes] = None   # 文件数据（简化）



    def is_dir(self) -> bool:

        return self.i_filetype == FileType.DIRECTORY



    def is_file(self) -> bool:

        return self.i_filetype == FileType.REGULAR_FILE





@dataclass

class Dentry:

    """目录项 (dentry) - 目录条目的缓存"""

    d_name: str                      # 文件名

    d_inode: Optional[Inode]         # 指向的inode

    d_parent: Optional['Dentry']     # 父目录

    d_subdirs: List['Dentry'] = field(default_factory=list)  # 子目录



    # 引用计数

    d_count: int = 1



    def add_child(self, dentry: 'Dentry'):

        """添加子目录项"""

        if dentry not in self.d_subdirs:

            self.d_subdirs.append(dentry)

            dentry.d_parent = self





@dataclass

class File:

    """打开的文件实例"""

    f_path: str                      # 文件路径

    f_inode: Inode                   # 对应的inode

    f_pos: int = 0                   # 文件位置

    f_flags: int = 0                 # 打开标志

    f_mode: int = 0                 # 打开模式



    # 操作函数

    f_op: Optional['file_operations'] = None



    # 引用计数

    f_count: int = 1





# 操作函数定义

class super_operations:

    """超级块操作"""

    @staticmethod

    def alloc_inode(sb: SuperBlock) -> Inode:

        pass



    @staticmethod

    def write_inode(inode: Inode):

        pass



    @staticmethod

    def put_super(sb: SuperBlock):

        pass





class inode_operations:

    """inode操作"""

    @staticmethod

    def create(inode: Inode, dentry: Dentry, mode: int) -> int:

        pass



    @staticmethod

    def lookup(inode: Inode, dentry: Dentry) -> Optional[Inode]:

        pass



    @staticmethod

    def mkdir(inode: Inode, dentry: Dentry, mode: int) -> int:

        pass





class file_operations:

    """文件操作"""

    @staticmethod

    def open(inode: Inode, file: File) -> int:

        pass



    @staticmethod

    def read(file: File, buf: bytes, size: int, pos: int) -> int:

        pass



    @staticmethod

    def write(file: File, buf: bytes, size: int, pos: int) -> int:

        pass



    @staticmethod

    def release(inode: Inode, file: File) -> int:

        pass





class VFS:

    """

    虚拟文件系统



    提供统一的文件操作接口。

    """



    def __init__(self):

        # 超级块表

        self.super_blocks: Dict[int, SuperBlock] = {}



        # inode缓存

        self.inode_cache: Dict[int, Inode] = {}



        # dentry缓存

        self.dentry_cache: Dict[str, Dentry] = {}



        # 打开的文件表

        self.files: Dict[int, File] = {}

        self.next_fd = 3  # 0=stdin, 1=stdout, 2=stderr



        # 挂载点

        self.mounts: Dict[str, SuperBlock] = {}



    def mount(self, device: str, mount_point: str, fs_type: str) -> bool:

        """

        挂载文件系统

        """

        print(f"  挂载 {fs_type} 从 {device} 到 {mount_point}")



        # 创建超级块

        sb = SuperBlock(s_root=None)

        sb.s_op = super_operations()



        self.super_blocks[id(sb)] = sb

        self.mounts[mount_point] = sb



        return True



    def umount(self, mount_point: str) -> bool:

        """卸载文件系统"""

        if mount_point in self.mounts:

            del self.mounts[mount_point]

            print(f"  卸载 {mount_point}")

            return True

        return False



    def alloc_inode(self, sb: SuperBlock) -> Inode:

        """分配inode"""

        ino = len(self.inode_cache) + 1

        inode = Inode(i_ino=ino)

        inode.i_op = inode_operations()

        inode.i_fop = file_operations()

        inode.i_atime = inode.i_mtime = inode.i_ctime = int(time.time())



        self.inode_cache[ino] = inode

        sb.s_iused += 1



        return inode



    def create_file(self, path: str, mode: int = 0o644) -> Optional[Inode]:

        """创建文件"""

        # 解析路径

        parts = path.strip('/').split('/')

        filename = parts[-1]



        # 创建inode

        inode = self.alloc_inode(self.super_blocks.get(1, SuperBlock()))

        inode.i_mode = 0o100644  # 常规文件

        inode.i_filetype = FileType.REGULAR_FILE

        inode.i_data = b''



        print(f"  创建文件 {path} (inode={inode.i_ino})")

        return inode



    def create_directory(self, path: str, mode: int = 0o755) -> Optional[Inode]:

        """创建目录"""

        inode = self.alloc_inode(self.super_blocks.get(1, SuperBlock()))

        inode.i_mode = 0o40444  # 目录

        inode.i_filetype = FileType.DIRECTORY



        print(f"  创建目录 {path} (inode={inode.i_ino})")

        return inode



    def open(self, path: str, flags: int = 0, mode: int = 0o644) -> Optional[int]:

        """

        打开文件

        return: 文件描述符

        """

        # 简化：创建新文件

        inode = self.create_file(path, mode)



        # 创建file结构

        file = File(f_path=path, f_inode=inode, f_flags=flags, f_mode=mode)

        file.f_op = file_operations()



        fd = self.next_fd

        self.next_fd += 1

        self.files[fd] = file



        print(f"  打开文件 {path} -> fd={fd}")

        return fd



    def read(self, fd: int, size: int = 4096) -> Optional[bytes]:

        """读取文件"""

        if fd not in self.files:

            return None



        file = self.files[fd]

        inode = file.f_inode



        if inode.i_data:

            return inode.i_data[file.f_pos:file.f_pos + size]

        return b''



    def write(self, fd: int, data: bytes) -> int:

        """写入文件"""

        if fd not in self.files:

            return -1



        file = self.files[fd]

        inode = file.f_inode



        if inode.i_data is None:

            inode.i_data = b''



        inode.i_data += data

        inode.i_size = len(inode.i_data)

        file.f_pos += len(data)



        return len(data)



    def close(self, fd: int) -> int:

        """关闭文件"""

        if fd in self.files:

            file = self.files[fd]

            file.f_count -= 1

            if file.f_count <= 0:

                del self.files[fd]

            print(f"  关闭 fd={fd}")

            return 0

        return -1



    def stat(self, path: str) -> Optional[Dict]:

        """获取文件状态"""

        # 简化：返回模拟数据

        return {

            'st_ino': 1,

            'st_size': 0,

            'st_mode': 0o100644,

            'st_nlink': 1,

            'st_uid': 0,

            'st_gid': 0,

        }





def simulate_vfs():

    """

    模拟VFS

    """

    print("=" * 60)

    print("虚拟文件系统 (VFS)")

    print("=" * 60)



    vfs = VFS()



    # 挂载文件系统

    print("\n挂载文件系统:")

    print("-" * 50)

    vfs.mount("/dev/sda1", "/", "ext4")

    vfs.mount("/dev/sdb1", "/mnt/usb", "vfat")



    # 创建文件

    print("\n创建文件:")

    print("-" * 50)

    vfs.create_file("/etc/passwd")

    vfs.create_file("/home/user/test.txt")



    # 创建目录

    print("\n创建目录:")

    print("-" * 50)

    vfs.create_directory("/home")

    vfs.create_directory("/home/user")



    # 打开文件

    print("\n文件操作:")

    print("-" * 50)

    fd1 = vfs.open("/tmp/test.txt")

    if fd1:

        vfs.write(fd1, b"Hello, VFS!")

        vfs.read(fd1, 100)

        vfs.close(fd1)



    # 显示VFS状态

    print("\nVFS状态:")

    print("-" * 50)

    print(f"  超级块数: {len(vfs.super_blocks)}")

    print(f"  inode缓存数: {len(vfs.inode_cache)}")

    print(f"  打开文件数: {len(vfs.files)}")

    print(f"  挂载点数: {len(vfs.mounts)}")



    # 显示目录结构

    print("\n目录结构示例:")

    print("-" * 50)



    # 创建模拟的目录树

    root = Dentry(d_name="/", d_inode=None)

    etc = Dentry(d_name="etc", d_inode=Inode(i_ino=2, i_filetype=FileType.DIRECTORY))

    home = Dentry(d_name="home", d_inode=Inode(i_ino=3, i_filetype=FileType.DIRECTORY))



    root.add_child(etc)

    root.add_child(home)



    def print_tree(dentry: Dentry, indent: int = 0):

        prefix = "  " * indent

        inode_info = f"(inode={dentry.d_inode.i_ino})" if dentry.d_inode else ""

        print(f"{prefix}{dentry.d_name}{inode_info}")

        for child in dentry.d_subdirs:

            print_tree(child, indent + 1)



    print_tree(root)





if __name__ == "__main__":

    simulate_vfs()

