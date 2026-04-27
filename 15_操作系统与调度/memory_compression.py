# -*- coding: utf-8 -*-
"""
算法实现：15_操作系统与调度 / memory_compression

本文件实现 memory_compression 相关的算法功能。
"""

from dataclasses import dataclass, field
from typing import Optional
import zlib


@dataclass
class CompressedPage:
    """压缩后的页"""
    original_pfn: int         # 原始页帧号
    compressed_data: bytes    # 压缩后的数据
    compress_ratio: float     # 压缩率
    is_evictable: bool = True  # 是否可驱逐


class PageTableEntry:
    """页表项（简化）"""
    def __init__(self, pfn: int, present: bool = True, swapped: bool = False):
        self.pfn = pfn
        self.present = present
        self.swapped = swapped
        self.compressed = False
        self.compressed_slot: Optional[int] = None


class MemoryCompressor:
    """
    内存压缩器（模拟zswap/zram）
    策略：
    1. 当内存使用超过阈值，启动压缩
    2. LRU淘汰最不活跃的页面
    3. 压缩后存储在内存的压缩池中
    4. 压缩率高时（>2x）才值得压缩
    """

    PAGE_SIZE = 4096
    COMPRESS_CHUNK_SIZE = 4096  # 压缩块大小

    def __init__(self, max_pool_mb: int = 256):
        self.compressed_pool: list[CompressedPage] = []
        self.max_pool_size = max_pool_mb * 1024 * 1024  # 池容量
        self.current_pool_size = 0

        # 统计
        self.compress_count = 0
        self.decompress_count = 0
        self.saved_pages = 0
        self.total_compress_time = 0.0

        # LRU链表
        self.lru: list[int] = []  # 压缩页索引，按访问频率排序

    def _get_compressed_size(self, data: bytes) -> int:
        """获取压缩后数据大小"""
        return len(data)

    def _compress_page(self, page_data: bytes) -> tuple[bytes, float]:
        """
        压缩单个页
        返回：(压缩数据, 压缩率)
        """
        import time
        start = time.perf_counter()

        compressed = zlib.compress(page_data, level=1)
        original_size = len(page_data)
        compressed_size = len(compressed)

        compress_ratio = original_size / compressed_size if compressed_size > 0 else 1.0

        elapsed = time.perf_counter() - start
        self.total_compress_time += elapsed

        return compressed, compress_ratio

    def _decompress_page(self, compressed_data: bytes) -> bytes:
        """解压页面"""
        return zlib.decompress(compressed_data)

    def store_page(self, pfn: int, page_data: bytes) -> Optional[int]:
        """
        存储压缩页到池中
        返回压缩槽ID，失败返回None
        """
        # 检查压缩率，不值得压缩则不存储
        compressed, ratio = self._compress_page(page_data)

        # 压缩率小于1.5不值得压缩
        if ratio < 1.5:
            return None

        # 检查池容量
        needed_size = len(compressed)
        if self.current_pool_size + needed_size > self.max_pool_size:
            # 需要驱逐一些页面
            evicted = self._evict_pages(needed_size)
            if not evicted:
                return None

        # 分配压缩槽
        slot_id = len(self.compressed_pool)
        cp = CompressedPage(
            original_pfn=pfn,
            compressed_data=compressed,
            compress_ratio=ratio
        )
        self.compressed_pool.append(cp)
        self.current_pool_size += needed_size
        self.compress_count += 1
        self.saved_pages += 1

        # 更新LRU
        self.lru.append(slot_id)

        return slot_id

    def _evict_pages(self, needed_size: int) -> bool:
        """驱逐LRU页面以释放空间"""
        while self.current_pool_size + needed_size > self.max_pool_size:
            if not self.lru:
                return False

            # 驱逐最久未访问的页面
            slot_id = self.lru.pop(0)
            if slot_id < len(self.compressed_pool):
                cp = self.compressed_pool[slot_id]
                self.current_pool_size -= len(cp.compressed_data)
                cp.compressed_data = b""  # 释放数据
                self.saved_pages -= 1

        return True

    def retrieve_page(self, slot_id: int) -> Optional[bytes]:
        """检索并解压页面"""
        if slot_id >= len(self.compressed_pool):
            return None

        cp = self.compressed_pool[slot_id]
        if not cp.compressed_data:
            return None

        # 解压
        page_data = self._decompress_page(cp.compressed_data)
        self.decompress_count += 1

        # 更新LRU（最近访问）
        if slot_id in self.lru:
            self.lru.remove(slot_id)
        self.lru.append(slot_id)

        return page_data

    def get_stats(self) -> dict:
        """获取压缩统计"""
        return {
            "compressed_pages": len(self.compressed_pool),
            "pool_size_mb": self.current_pool_size / (1024 * 1024),
            "max_pool_mb": self.max_pool_size / (1024 * 1024),
            "compress_count": self.compress_count,
            "decompress_count": self.decompress_count,
            "saved_pages": self.saved_pages,
            "avg_compress_time_us": (self.total_compress_time / self.compress_count * 1_000_000) if self.compress_count > 0 else 0,
        }


class ZswapDriver:
    """
    zswap驱动（Linux内核模块的简化模拟）
    工作流程：
    1. 内存压力时，内核尝试将页面换出
    2. zswap拦截换出请求
    3. 尝试压缩页面
    4. 如果压缩率高（>1.5x），存储到zswap池
    5. 如果压缩率低或池满，回退到原始swap设备
    """

    def __init__(self):
        self.compressor = MemoryCompressor(max_pool_mb=128)
        self.frontswap_enabled = True  # 启用frontswap接口
        self.same_filled_pages_enabled = True  # 相同内容页面优化

    def writeback_to_zswap(self, pfn: int, page_data: bytes) -> tuple[bool, int]:
        """
        尝试将页面写入zswap
        返回：(是否成功, 压缩槽ID或-1)
        """
        if not self.frontswap_enabled:
            return False, -1

        # 特殊处理：全零页面（zero page）
        if page_data == bytes(len(page_data)):
            # 全零页面不需要存储，虚拟存储
            return True, -2  # 特殊标记

        # 尝试压缩存储
        slot_id = self.compressor.store_page(pfn, page_data)
        if slot_id is not None:
            return True, slot_id

        return False, -1

    def readback_from_zswap(self, slot_id: int) -> Optional[bytes]:
        """从zswap读取并解压页面"""
        if slot_id == -2:
            # 全零页面
            return bytes(4096)

        return self.compressor.retrieve_page(slot_id)


if __name__ == "__main__":
    print("=== 内存压缩（zswap/zram）演示 ===")

    driver = ZswapDriver()

    # 模拟内存压缩操作
    print("\n--- 模拟页面压缩 ---")

    test_pages = [
        ("P001", bytes(4096)),  # 全零页（高效压缩）
        ("P002", b"\x00" * 2048 + b"\xFF" * 2048),  # 混合格式（压缩率一般）
        ("P003", bytes([i % 256 for i in range(4096)])),  # 重复模式（高压缩率）
        ("P004", bytes([random.randint(0, 255) for _ in range(4096)])),  # 随机（低压缩率）
    ]

    for pfn, data in test_pages:
        success, slot = driver.writeback_to_zswap(pfn, data)
        if success:
            if slot == -2:
                print(f"{pfn}: 全零页优化（无需存储）")
            else:
                cp = driver.compressor.compressed_pool[slot]
                print(f"{pfn}: 压缩成功 (slot={slot}, ratio={cp.compress_ratio:.2f}x)")
        else:
            print(f"{pfn}: 压缩失败（压缩率不足）")

    # 统计信息
    print("\n--- zswap统计 ---")
    stats = driver.compressor.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # 演示解压
    print("\n--- 页面解压测试 ---")
    for i, cp in enumerate(driver.compressor.compressed_pool):
        if cp.compressed_data:
            recovered = driver.readback_from_zswap(i)
            if recovered:
                print(f"Slot {i}: 解压成功，恢复{len(recovered)}字节")

    # 性能对比
    print("\n=== zswap vs 传统swap ===")
    print("| 指标        | 传统swap (SSD) | zswap (内存压缩) |")
    print("|-------------|-----------------|-------------------|")
    print("| 写入延迟    | ~500μs          | ~10μs             |")
    print("| 读取延迟    | ~300μs          | ~10μs             |")
    print("| 带宽        | ~200 MB/s       | ~2 GB/s           |")
    print("| 寿命影响    | SSD写入寿命     | 无（内存操作）     |")
    print("| 适用场景    | 内存严重不足    | 轻度内存压力       |")
