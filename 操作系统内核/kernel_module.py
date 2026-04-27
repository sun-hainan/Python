# -*- coding: utf-8 -*-
"""
算法实现：操作系统内核 / kernel_module

本文件实现 kernel_module 相关的算法功能。
"""

from typing import Dict, List, Optional, Set, Callable, Any
from dataclasses import dataclass
import hashlib


@dataclass
class KernelSymbol:
    """内核符号"""
    name: str
    address: int
    namespace: str = ""  # 命名空间
    exported: bool = False  # 是否导出（EXPORT_SYMBOL）
    crc: int = 0  # CRC校验（用于模块验证）

    # 符号类型
    TYPE_FUNC = "function"
    TYPE_VAR = "variable"
    sym_type: str = TYPE_FUNC


class SymbolTable:
    """
    内核符号表

    存储所有内核符号和导出的符号。
    """

    def __init__(self):
        # 全部符号表
        self.symbols: Dict[str, KernelSymbol] = {}

        # 导出的符号（可被模块使用）
        self.exported_symbols: Dict[str, KernelSymbol] = {}

        # 命名空间
        self.namespaces: Dict[str, Set[str]] = {}

        # 地址分配器
        self.next_address = 0x10000000

    def add_symbol(self, name: str, sym_type: str = KernelSymbol.TYPE_FUNC,
                   namespace: str = "", exported: bool = False) -> int:
        """
        添加符号到符号表
        return: 符号地址
        """
        # 分配地址
        address = self.next_address
        self.next_address += 0x1000

        # 计算CRC
        crc = self._calculate_crc(name)

        symbol = KernelSymbol(
            name=name,
            address=address,
            namespace=namespace,
            exported=exported,
            crc=crc,
            sym_type=sym_type
        )

        self.symbols[name] = symbol

        if exported:
            self.exported_symbols[name] = symbol

        return address

    def _calculate_crc(self, name: str) -> int:
        """计算符号CRC"""
        return int(hashlib.crc32(name.encode()) & 0xFFFFFFFF)

    def get_symbol(self, name: str) -> Optional[KernelSymbol]:
        """获取符号"""
        return self.symbols.get(name)

    def get_exported_symbol(self, name: str) -> Optional[KernelSymbol]:
        """获取导出的符号"""
        return self.exported_symbols.get(name)

    def is_symbol_exported(self, name: str) -> bool:
        """检查符号是否导出"""
        sym = self.exported_symbols.get(name)
        return sym is not None

    def list_exported_symbols(self) -> List[str]:
        """列出所有导出符号"""
        return list(self.exported_symbols.keys())

    def list_symbols(self) -> List[KernelSymbol]:
        """列出所有符号"""
        return list(self.symbols.values())


class KernelModule:
    """
    内核模块

    可以在运行时加载/卸载的代码单元。
    """

    def __init__(self, name: str, symbol_table: SymbolTable):
        self.name = name
        self.symbol_table = symbol_table

        # 模块状态
        self.loaded: bool = False
        self.ref_count: int = 0

        # 模块依赖
        self.dependencies: Set[str] = set()

        # 导出的符号
        self.exported_symbols: Dict[str, int] = {}

        # 模块内存
        self.code_address: int = 0
        self.code_size: int = 0

        # init/exit函数
        self.init_func: Optional[Callable] = None
        self.exit_func: Optional[Callable] = None

    def register_init(self, func: Callable):
        """注册模块初始化函数"""
        self.init_func = func

    def register_exit(self, func: Callable):
        """注册模块退出函数"""
        self.exit_func = func

    def load(self) -> bool:
        """
        加载模块
        调用init函数
        """
        if self.loaded:
            return False

        # 检查依赖
        for dep in self.dependencies:
            if not self.symbol_table.is_symbol_exported(dep):
                print(f"  错误: 依赖 '{dep}' 未找到")
                return False

        # 分配内存（模拟）
        self.code_address = 0xC0000000  # 内核地址空间
        self.code_size = 4096

        # 调用init
        if self.init_func:
            result = self.init_func()
            if result != 0:
                print(f"  模块 {self.name} 初始化失败: {result}")
                return False

        self.loaded = True
        print(f"  模块 {self.name} 已加载")
        print(f"    代码地址: 0x{self.code_address:08X}")
        print(f"    代码大小: {self.code_size} bytes")
        print(f"    引用计数: {self.ref_count}")

        return True

    def unload(self) -> bool:
        """
        卸载模块
        调用exit函数
        """
        if not self.loaded:
            return False

        if self.ref_count > 0:
            print(f"  错误: 模块 {self.name} 正在使用中 (ref_count={self.ref_count})")
            return False

        # 调用exit
        if self.exit_func:
            self.exit_func()

        self.loaded = False
        print(f"  模块 {self.name} 已卸载")

        return True

    def add_dependency(self, symbol_name: str):
        """添加模块依赖"""
        self.dependencies.add(symbol_name)

    def export_symbol(self, name: str, address: int):
        """导出符号供其他模块使用"""
        self.exported_symbols[name] = address
        self.symbol_table.add_symbol(name, exported=True)


class ModuleManager:
    """
    模块管理器

    管理所有已加载的内核模块。
    """

    def __init__(self):
        self.modules: Dict[str, KernelModule] = {}
        self.symbol_table = SymbolTable()

        # 预加载一些基础符号
        self._init_kernel_symbols()

    def _init_kernel_symbols(self):
        """初始化内核符号"""
        # 添加基础内核符号
        base_symbols = [
            "printk",
            "kmalloc",
            "kfree",
            "register_chrdev",
            "unregister_chrdev",
            "copy_from_user",
            "copy_to_user",
            "schedule",
            "wake_up_process",
        ]

        for sym in base_symbols:
            self.symbol_table.add_symbol(sym, exported=True)

    def register_module(self, module: KernelModule) -> bool:
        """注册模块"""
        if module.name in self.modules:
            print(f"  模块 {module.name} 已存在")
            return False

        self.modules[module.name] = module
        print(f"  模块 {module.name} 已注册")
        return True

    def load_module(self, name: str) -> bool:
        """加载模块"""
        if name not in self.modules:
            print(f"  模块 {name} 未注册")
            return False

        module = self.modules[name]
        return module.load()

    def unload_module(self, name: str) -> bool:
        """卸载模块"""
        if name not in self.modules:
            print(f"  模块 {name} 未加载")
            return False

        module = self.modules[name]
        return module.unload()

    def get_module(self, name: str) -> Optional[KernelModule]:
        """获取模块"""
        return self.modules.get(name)

    def list_modules(self) -> List[str]:
        """列出所有已注册模块"""
        return list(self.modules.keys())

    def list_loaded_modules(self) -> List[str]:
        """列出已加载的模块"""
        return [name for name, mod in self.modules.items() if mod.loaded]


def create_example_module(name: str, manager: ModuleManager) -> KernelModule:
    """创建示例模块"""

    module = KernelModule(name, manager.symbol_table)

    # 定义init函数
    def module_init():
        print(f"  [{name}] 初始化中...")
        print(f"  [{name}] 模块初始化完成")
        return 0

    # 定义exit函数
    def module_exit():
        print(f"  [{name}] 模块退出中...")
        print(f"  [{name}] 模块已卸载")

    module.register_init(module_init)
    module.register_exit(module_exit)

    # 导出一些符号
    module.export_symbol(f"{name}_function", 0x1000)

    return module


def simulate_kernel_modules():
    """
    模拟内核模块
    """
    print("=" * 60)
    print("内核模块：init/exit 与符号表")
    print("=" * 60)

    # 创建模块管理器
    manager = ModuleManager()

    # 显示内核符号表
    print("\n内核符号表 (部分导出符号):")
    print("-" * 50)
    exported = manager.symbol_table.list_exported_symbols()
    for i, sym in enumerate(exported[:10]):
        print(f"  {sym}")

    # 创建模块
    print("\n" + "-" * 50)
    print("创建模块:")
    print("-" * 50)

    # 模块1: 字符设备驱动
    cdev_module = create_example_module("cdev_driver", manager)
    cdev_module.add_dependency("register_chrdev")
    cdev_module.add_dependency("unregister_chrdev")
    manager.register_module(cdev_module)

    # 模块2: 网络驱动
    net_module = create_example_module("net_driver", manager)
    net_module.add_dependency("kmalloc")
    manager.register_module(net_module)

    # 模块3: 文件系统
    fs_module = create_example_module("ext4_driver", manager)
    fs_module.add_dependency("printk")
    manager.register_module(fs_module)

    # 列出已注册模块
    print("\n已注册模块:")
    print("-" * 50)
    for name in manager.list_modules():
        mod = manager.get_module(name)
        print(f"  {name}: loaded={mod.loaded}, deps={mod.dependencies}")

    # 加载模块
    print("\n" + "-" * 50)
    print("加载模块:")
    print("-" * 50)

    manager.load_module("cdev_driver")
    manager.load_module("net_driver")
    manager.load_module("ext4_driver")

    # 显示已加载模块
    print("\n已加载模块:")
    print("-" * 50)
    for name in manager.list_loaded_modules():
        print(f"  {name}")

    # 模块引用计数
    print("\n" + "-" * 50)
    print("模块引用计数:")
    print("-" * 50)

    cdev_module.ref_count = 2
    net_module.ref_count = 1
    print(f"  cdev_driver: ref_count={cdev_module.ref_count}")
    print(f"  net_driver: ref_count={net_module.ref_count}")

    # 卸载模块
    print("\n" + "-" * 50)
    print("卸载模块:")
    print("-" * 50)

    # 先减少引用计数
    cdev_module.ref_count = 0
    net_module.ref_count = 0

    manager.unload_module("net_driver")
    manager.unload_module("cdev_driver")

    # 模块间依赖演示
    print("\n" + "=" * 60)
    print("模块依赖关系")
    print("=" * 60)

    # 重新加载cdev_driver
    cdev_module.load()

    print("\n依赖检查:")
    print("-" * 50)
    for dep in cdev_module.dependencies:
        exported = manager.symbol_table.is_symbol_exported(dep)
        print(f"  {dep}: {'✓ 可用' if exported else '✗ 不可用'}")

    # 符号解析
    print("\n符号解析:")
    print("-" * 50)
    sym = manager.symbol_table.get_exported_symbol("kmalloc")
    if sym:
        print(f"  kmalloc: 地址=0x{sym.address:08X}, CRC=0x{sym.crc:08X}")


if __name__ == "__main__":
    simulate_kernel_modules()
