# -*- coding: utf-8 -*-
"""
算法实现：15_操作系统与调度 / slab_allocator

本文件实现 slab_allocator 相关的算法功能。
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SlabDescriptor:
    """Slab描述符：管理一组对象"""
    slab_id: int
    num_objects: int          # 对象数量
    object_size: int          # 对象大小
    free_count: int           # 空闲对象数
    free_list: list[int] = field(default_factory=list)  # 空闲对象索引栈


class SlabAllocator:
    """
    Slab分配器（简化版）
    结构：cache -> slabs -> objects
    设计思路：
    - 每个缓存（cache）专门管理一种对象类型
    - 每个slab管理一组物理连续的page
    - 对象分配：从当前slab的free_list弹出
    - 释放对象：推入对应slab的free_list
    """

    def __init__(self, cache_name: str, object_size: int, cache_size: int = 64):
        self.cache_name = cache_name
        self.object_size = object_size          # 单对象大小
        self.slab_order = self._calc_slab_order()  # 每个slab占用页数

        self.slabs: list[SlabDescriptor] = []
        self.cache_size = cache_size  # 每slab对象数
        self.slab_id_counter = 0

        # 预分配一个slab
        self._allocate_slab()

    def _calc_slab_order(self) -> int:
        """计算每个slab占用的页数（根据对象大小）"""
        PAGE_SIZE = 4096
        objects_per_slab = 16  # 至少16个对象
        estimated_size = objects_per_slab * self.object_size
        order = 0
        while (1 << order) * PAGE_SIZE < estimated_size:
            order += 1
        return min(order, 4)  # 最多4个页（16KB）

    def _allocate_slab(self) -> SlabDescriptor:
        """分配新的slab"""
        slab = SlabDescriptor(
            slab_id=self.slab_id_counter,
            num_objects=self.cache_size,
            object_size=self.object_size,
            free_count=self.cache_size
        )
        slab.free_list = list(range(self.cache_size))
        self.slabs.append(slab)
        self.slab_id_counter += 1
        return slab

    def allocate(self) -> Optional[int]:
        """
        分配对象
        返回对象索引（简化：slab_id * cache_size + offset）
        """
        # 查找有空闲对象的slab
        for slab in self.slabs:
            if slab.free_count > 0:
                offset = slab.free_list.pop()
                slab.free_count -= 1
                return slab.slab_id * self.cache_size + offset

        # 所有slab满了，分配新slab
        new_slab = self._allocate_slab()
        offset = new_slab.free_list.pop()
        new_slab.free_count -= 1
        return new_slab.slab_id * self.cache_size + offset

    def free(self, obj_id: int) -> bool:
        """释放对象"""
        slab_id = obj_id // self.cache_size
        offset = obj_id % self.cache_size

        # 找到对应slab
        for slab in self.slabs:
            if slab.slab_id == slab_id:
                slab.free_list.append(offset)
                slab.free_count += 1
                return True

        return False

    def get_cache_stats(self) -> dict:
        """获取缓存统计"""
        total_objects = sum(slab.num_objects for slab in self.slabs)
        free_objects = sum(slab.free_count for slab in self.slabs)
        return {
            "cache_name": self.cache_name,
            "num_slabs": len(self.slabs),
            "total_objects": total_objects,
            "free_objects": free_objects,
            "usage": f"{(total_objects - free_objects) / total_objects * 100:.1f}%" if total_objects > 0 else "0%"
        }


# 预定义的slab缓存（模拟Linux内核常用缓存）
SLAB_CACHES = {
    "task_struct": SlabAllocator("task_struct", object_size=1760, cache_size=128),
    "inode_cache": SlabAllocator("inode_cache", object_size=608, cache_size=256),
    "dentry": SlabAllocator("dentry", object_size=192, cache_size=256),
    "buffer_head": SlabAllocator("buffer_head", object_size=128, cache_size=512),
    "vm_area_struct": SlabAllocator("vm_area_struct", object_size=216, cache_size=256),
}


if __name__ == "__main__":
    print("=== Slab分配器测试 ===")

    # 创建task_struct缓存
    task_cache = SLAB_CACHES["task_struct"]
    print(f"task_struct缓存: 对象大小={task_cache.object_size} bytes, slab阶={task_cache.slab_order}")

    # 分配对象
    obj_ids = []
    for i in range(10):
        obj_id = task_cache.allocate()
        obj_ids.append(obj_id)

    print(f"分配10个对象: {obj_ids}")
    stats = task_cache.get_cache_stats()
    print(f"统计: {stats}")

    # 释放部分对象
    for obj_id in obj_ids[5:]:
        task_cache.free(obj_id)

    print(f"\n释放5个对象后: {task_cache.get_cache_stats()}")

    # 综合测试
    print("\n=== 多种缓存测试 ===")
    cache_names = ["task_struct", "dentry", "buffer_head"]
    for name in cache_names:
        cache = SLAB_CACHES[name]
        # 分配一些对象
        ids = [cache.allocate() for _ in range(50)]
        stats = cache.get_cache_stats()
        print(f"{name}: {stats}")

        # 释放
        for oid in ids:
            cache.free(oid)

    # 内存布局演示
    print("\n=== 简化内存布局 ===")
    print("+-------------+")
    print("|   task_struct slab (order=1)  |")
    print("|  [obj0][obj1]...[obj127]      |")
    print("+-------------+")
    print("|   inode_cache slab (order=1)  |")
    print("|  [obj0][obj1]...[obj255]      |")
    print("+-------------+")
