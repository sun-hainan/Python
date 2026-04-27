# -*- coding: utf-8 -*-

"""

算法实现：操作系统内核 / device_driver



本文件实现 device_driver 相关的算法功能。

"""



from typing import Dict, List, Optional, Set

from dataclasses import dataclass

from enum import Enum





class DeviceType(Enum):

    """设备类型"""

    CHAR = "char"

    BLOCK = "block"

    NETWORK = "network"





@dataclass

class Device:

    """设备"""

    dev_id: int              # 设备号

    name: str                # 设备名

    type: DeviceType         # 设备类型

    major: int = 0           # 主设备号

    minor: int = 0           # 次设备号



    # 设备操作

    fops: Optional['file_operations'] = None



    # 状态

    opened: bool = False

    ref_count: int = 0



    # 设备特定数据

    private_data: any = None





class file_operations:

    """文件操作（设备驱动）"""

    @staticmethod

    def open(inode, filp) -> int:

        return 0



    @staticmethod

    def release(inode, filp) -> int:

        return 0



    @staticmethod

    def read(filp, buf, size, pos) -> int:

        return 0



    @staticmethod

    def write(filp, buf, size, pos) -> int:

        return 0



    @staticmethod

    def ioctl(filp, cmd, arg) -> int:

        return 0





@dataclass

class CharDevice:

    """字符设备"""

    cdev: Device

    ops: 'cdev_operations' = None



    # 数据缓冲区

    buffer: bytes = b''

    buffer_size: int = 4096





class cdev_operations:

    """字符设备操作"""

    @staticmethod

    def open(inode, filp) -> int:

        print(f"  打开字符设备")

        return 0



    @staticmethod

    def read(filp, buf, size, pos) -> int:

        print(f"  读取 {size} 字节")

        return size



    @staticmethod

    def write(filp, buf, size, pos) -> int:

        print(f"  写入 {size} 字节")

        return size



    @staticmethod

    def ioctl(filp, cmd, arg) -> int:

        print(f"  ioctl cmd=0x{cmd:X}, arg=0x{arg:X}")

        return 0





@dataclass

class BlockDevice:

    """块设备"""

    bdev: Device



    # 块设备参数

    block_size: int = 512

    num_blocks: int = 1024



    # 缓冲区

    buffer: Dict[int, bytes] = {}  # block_nr -> data



    # 请求队列

    request_queue: List['Request'] = []



    # 已注册的分区

    partitions: List['Partition'] = []





@dataclass

class Partition:

    """磁盘分区"""

    start: int          # 起始块

    size: int           # 大小（块数）

    name: str           # 分区名





@dataclass

class Request:

    """块设备请求"""

    op: str             # READ or WRITE

    block_nr: int       # 块号

    size: int           # 大小

    data: bytes = b''





class ioctl_commands:

    """常见ioctl命令"""

    # 通用

    IOCTL_BASE = 0x00

    IOCTL_RESET = 0x01

    IOCTL_FLUSH = 0x02



    # 终端

    TCGETS = 0x5401

    TCSETS = 0x5402

    TCSETSW = 0x5403



    # 磁盘

    BLKRRPART = 0x1251  # 重读分区表

    BLKGETSIZE = 0x1260  # 获取大小

    BLKFLSBUF = 0x1261  # 刷新缓冲区





class DeviceDriver:

    """

    设备驱动模型



    管理字符设备和块设备。

    """



    def __init__(self):

        # 设备注册表

        self.char_devices: Dict[int, CharDevice] = {}  # major -> device

        self.block_devices: Dict[int, BlockDevice] = {}

        self.major_numbers: Dict[int, str] = {}  # major -> device_name



        # 下一个可用的设备号

        self.next_major = 1

        self.next_minor = 0



        # 设备类

        self.device_classes: Dict[str, List[Device]] = {}



    def register_chrdev(self, name: str, major: int = 0, ops=None) -> int:

        """

        注册字符设备

        return: 主设备号

        """

        if major == 0:

            # 动态分配

            major = self.next_major

            self.next_major += 1



        device = Device(

            dev_id=major,

            name=name,

            type=DeviceType.CHAR,

            major=major,

            minor=self.next_minor

        )



        cdev = CharDevice(cdev=device, ops=ops or cdev_operations())

        self.char_devices[major] = cdev

        self.major_numbers[major] = name



        print(f"  注册字符设备: {name}, major={major}")



        return major



    def register_blkdev(self, name: str, major: int = 0, ops=None) -> int:

        """

        注册块设备

        return: 主设备号

        """

        if major == 0:

            major = self.next_major

            self.next_major += 1



        device = Device(

            dev_id=major,

            name=name,

            type=DeviceType.BLOCK,

            major=major,

            minor=self.next_minor

        )



        bdev = BlockDevice(bdev=device)

        self.block_devices[major] = bdev

        self.major_numbers[major] = name



        print(f"  注册块设备: {name}, major={major}")



        return major



    def unregister_chrdev(self, major: int):

        """注销字符设备"""

        if major in self.char_devices:

            name = self.major_numbers.get(major, "?")

            del self.char_devices[major]

            del self.major_numbers[major]

            print(f"  注销字符设备: {name}, major={major}")



    def open_device(self, major: int, minor: int = 0) -> bool:

        """打开设备"""

        if major in self.char_devices:

            cdev = self.char_devices[major]

            cdev.cdev.opened = True

            cdev.cdev.ref_count += 1

            return True

        return False



    def close_device(self, major: int) -> bool:

        """关闭设备"""

        if major in self.char_devices:

            cdev = self.char_devices[major]

            cdev.cdev.ref_count -= 1

            if cdev.cdev.ref_count <= 0:

                cdev.cdev.opened = False

            return True

        return False



    def read_device(self, major: int, size: int) -> int:

        """读取设备"""

        if major in self.char_devices:

            cdev = self.char_devices[major]

            return len(cdev.buffer) if cdev.buffer else 0

        return -1



    def write_device(self, major: int, data: bytes) -> int:

        """写入设备"""

        if major in self.char_devices:

            cdev = self.char_devices[major]

            cdev.buffer = data

            return len(data)

        return -1



    def ioctl_device(self, major: int, cmd: int, arg: int) -> int:

        """设备ioctl控制"""

        if major in self.char_devices:

            cdev = self.char_devices[major]

            return cdev.ops.ioctl(None, cmd, arg) if cdev.ops else 0

        return -1



    def get_device_list(self) -> List[Dict]:

        """获取设备列表"""

        devices = []

        for major, cdev in self.char_devices.items():

            devices.append({

                'type': 'char',

                'name': cdev.cdev.name,

                'major': major,

                'minor': cdev.cdev.minor,

                'ref_count': cdev.cdev.ref_count

            })

        for major, bdev in self.block_devices.items():

            devices.append({

                'type': 'block',

                'name': bdev.bdev.name,

                'major': major,

                'minor': bdev.bdev.minor,

                'blocks': bdev.num_blocks

            })

        return devices





def simulate_device_driver():

    """

    模拟设备驱动

    """

    print("=" * 60)

    print("设备驱动模型：字符设备 / 块设备")

    print("=" * 60)



    driver = DeviceDriver()



    # 注册设备

    print("\n注册设备:")

    print("-" * 50)



    major_tty = driver.register_chrdev("tty", major=4)  # 传统TTY主设备号

    major_null = driver.register_chrdev("null", major=1)  # 传统null主设备号

    major_sda = driver.register_blkdev("sda", major=8)  # SCSI磁盘主设备号



    # 打开设备

    print("\n打开设备:")

    print("-" * 50)



    driver.open_device(major_tty)

    print(f"  打开 tty, 引用计数={driver.char_devices[major_tty].cdev.ref_count}")



    driver.open_device(major_sda)

    print(f"  打开 sda")



    # 读写设备

    print("\n设备I/O:")

    print("-" * 50)



    data = b"Hello, device!"

    written = driver.write_device(major_null, data)

    print(f"  写入 null: {written} 字节")



    read_size = driver.read_device(major_null)

    print(f"  从 null 读取: {read_size} 字节")



    # ioctl演示

    print("\nioctl控制:")

    print("-" * 50)



    # TTY ioctl

    driver.ioctl_device(major_tty, ioctl_commands.TCGETS, 0)

    driver.ioctl_device(major_tty, ioctl_commands.TCSETS, 0)



    # 块设备ioctl

    driver.ioctl_device(major_sda, ioctl_commands.BLKRRPART, 0)

    driver.ioctl_device(major_sda, ioctl_commands.BLKGETSIZE, 0)



    # 关闭设备

    print("\n关闭设备:")

    print("-" * 50)



    driver.close_device(major_tty)

    print(f"  关闭 tty")



    # 设备列表

    print("\n设备列表:")

    print("-" * 50)

    print(f"  {'类型':<8} {'名称':<12} {'主设备号':<10} {'次设备号':<10}")

    print(f"  {'-'*50}")



    for dev in driver.get_device_list():

        print(f"  {dev['type']:<8} {dev['name']:<12} {dev['major']:<10} {dev['minor']:<10}")



    # 块设备操作演示

    print("\n" + "=" * 60)

    print("块设备操作")

    print("=" * 60)



    bdev = driver.block_devices[major_sda]



    print("\n块设备信息:")

    print(f"  块大小: {bdev.block_size} bytes")

    print(f"  块数量: {bdev.num_blocks}")

    print(f"  总容量: {bdev.block_size * bdev.num_blocks / 1024 / 1024:.1f} MB")



    # 模拟读写块

    print("\n块设备I/O:")

    print("-" * 50)



    request = Request(op="WRITE", block_nr=100, size=512, data=b"Block data!")

    bdev.request_queue.append(request)

    print(f"  提交写请求: 块={request.block_nr}, 大小={request.size}")



    request = Request(op="READ", block_nr=100, size=512)

    bdev.request_queue.append(request)

    print(f"  提交读请求: 块={request.block_nr}, 大小={request.size}")





if __name__ == "__main__":

    simulate_device_driver()

