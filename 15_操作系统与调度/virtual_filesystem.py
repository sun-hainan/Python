# -*- coding: utf-8 -*-
"""
算法实现：15_操作系统与调度 / virtual_filesystem

本文件实现 virtual_filesystem 相关的算法功能。
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class FileType(Enum):
    """文件类型"""
    REGULAR = 0       # 常规文件
    DIRECTORY = 1     # 目录
    SYMBOLIC = 2      # 符号链接
    BLOCK_DEVICE = 3  # 块设备
    CHAR_DEVICE = 4   # 字符设备
    FIFO = 5          # 命名管道
    SOCKET = 6        # 套接字


@dataclass
class Inode:
    """inode：文件系统中的文件元数据"""
    inode_id: int
    file_type: FileType
    size: int = 0
    permissions: int = 0o644
    uid: int = 0
    gid: int = 0
    atime: float = 0.0  # 访问时间
    mtime: float = 0.0  # 修改时间
    ctime: float = 0.0  # 创建时间
    link_count: int = 1  # 硬链接数
    blocks: int = 0      # 占用块数
    block_device: Optional[int] = None  # 块设备号
    # 索引节点指针（指向数据块）
    direct_blocks: list[int] = field(default_factory=list)
    indirect_block: Optional[int] = None  # 单间接块


@dataclass
class Dentry:
    """dentry：目录项，连接父目录与子文件"""
    name: str
    inode: Inode
    parent: Optional["Dentry"] = None
    children: list["Dentry"] = field(default_factory=list)

    def add_child(self, dentry: "Dentry"):
        dentry.parent = self
        self.children.append(dentry)

    def lookup(self, name: str) -> Optional["Dentry"]:
        """查找子目录项"""
        for child in self.children:
            if child.name == name:
                return child
        return None


@dataclass
class SuperBlock:
    """super_block：文件系统超级块"""
    fs_type: str             # 文件系统类型（ext4, xfs, btrfs...）
    block_size: int = 4096  # 块大小
    total_blocks: int = 0
    free_blocks: int = 0
    total_inodes: int = 0
    free_inodes: int = 0
    root_dentry: Optional[Dentry] = None
    mount_point: str = "/"


class VFSMount:
    """VFS挂载点"""
    def __init__(self, fs_type: str, device: str, mount_point: str, sb: SuperBlock):
        self.fs_type = fs_type
        self.device = device
        self.mount_point = mount_point
        self.sb = sb


class VirtualFileSystem:
    """
    虚拟文件系统
    支持：目录遍历、inode查找、挂载/卸载
    """

    def __init__(self):
        self.mounts: list[VFSMount] = []
        self.inode_cache: dict[int, Inode] = {}
        self.next_inode_id = 1

    def _alloc_inode_id(self) -> int:
        nid = self.next_inode_id
        self.next_inode_id += 1
        return nid

    def create_inode(self, file_type: FileType, name: str = "") -> Inode:
        """创建新inode"""
        inode = Inode(inode_id=self._alloc_inode_id(), file_type=file_type)
        self.inode_cache[inode.inode_id] = inode
        return inode

    def create_file(self, parent: Dentry, name: str, file_type: FileType = FileType.REGULAR) -> Dentry:
        """在父目录下创建文件"""
        inode = self.create_inode(file_type, name)
        dentry = Dentry(name=name, inode=inode)
        parent.add_child(dentry)
        return dentry

    def _find_mount(self, path: str) -> Optional[VFSMount]:
        """查找路径对应的挂载点"""
        for mount in sorted(self.mounts, key=lambda m: -len(m.mount_point)):
            if path.startswith(mount.mount_point):
                return mount
        return None

    def mount_filesystem(self, fs_type: str, device: str, mount_point: str):
        """挂载文件系统"""
        sb = SuperBlock(fs_type=fs_type, mount_point=mount_point)
        mount = VFSMount(fs_type, device, mount_point, sb)
        self.mounts.append(mount)

        # 创建根目录inode
        root_inode = self.create_inode(FileType.DIRECTORY)
        root_dentry = Dentry(name="/", inode=root_inode)
        sb.root_dentry = root_dentry

    def unmount(self, mount_point: str) -> bool:
        """卸载文件系统"""
        for i, m in enumerate(self.mounts):
            if m.mount_point == mount_point:
                self.mounts.pop(i)
                return True
        return False

    def resolve_path(self, path: str) -> Optional[Dentry]:
        """解析绝对路径到dentry"""
        if not path.startswith("/"):
            return None

        mount = self._find_mount(path)
        if mount is None or mount.sb.root_dentry is None:
            return None

        dentry = mount.sb.root_dentry
        components = [c for c in path.split("/") if c]

        for comp in components:
            if comp == "..":
                dentry = dentry.parent or dentry
            elif comp == ".":
                continue
            else:
                child = dentry.lookup(comp)
                if child is None:
                    return None
                dentry = child

        return dentry

    def stat(self, path: str) -> Optional[dict]:
        """获取文件信息（类似stat系统调用）"""
        dentry = self.resolve_path(path)
        if dentry is None:
            return None

        inode = dentry.inode
        return {
            "ino": inode.inode_id,
            "type": inode.file_type.name,
            "size": inode.size,
            "mode": oct(inode.permissions),
            "uid": inode.uid,
            "gid": inode.gid,
            "links": inode.link_count,
        }


if __name__ == "__main__":
    vfs = VirtualFileSystem()

    # 挂载文件系统
    print("=== 虚拟文件系统演示 ===")
    vfs.mount_filesystem("ext4", "/dev/sda1", "/")
    vfs.mount_filesystem("tmpfs", "none", "/tmp")

    # 创建目录结构
    root = vfs.resolve_path("/")
    vfs.create_file(root, "home", FileType.DIRECTORY)
    vfs.create_file(root, "etc", FileType.DIRECTORY)
    vfs.create_file(root, "usr", FileType.DIRECTORY)

    home = vfs.resolve_path("/home")
    vfs.create_file(home, "user", FileType.DIRECTORY)
    vfs.create_file(home, "alice", FileType.DIRECTORY)

    user_home = vfs.resolve_path("/home/user")
    vfs.create_file(user_home, "readme.txt", FileType.REGULAR)
    vfs.create_file(user_home, "script.py", FileType.REGULAR)

    # 路径解析测试
    print("\n=== 路径解析 ===")
    test_paths = ["/", "/home", "/home/user", "/home/user/readme.txt", "/etc/passwd"]
    for p in test_paths:
        dentry = vfs.resolve_path(p)
        if dentry:
            print(f"{p}: {dentry.name} (inode={dentry.inode.inode_id}, type={dentry.inode.file_type.name})")
        else:
            print(f"{p}: 未找到")

    # stat测试
    print("\n=== Stat信息 ===")
    for p in ["/home/user", "/home/user/readme.txt"]:
        info = vfs.stat(p)
        if info:
            print(f"{p}: {info}")

    # 目录遍历
    print("\n=== 目录遍历 ===")
    def list_dir(dentry: Dentry, indent: int = 0):
        prefix = "  " * indent
        print(f"{prefix}{dentry.name}/")
        for child in dentry.children:
            list_dir(child, indent + 1)

    root_dentry = vfs.resolve_path("/")
    if root_dentry:
        list_dir(root_dentry)
