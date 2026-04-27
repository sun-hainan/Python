# -*- coding: utf-8 -*-
"""
算法实现：在线算法 / paging_algorithm

本文件实现 paging_algorithm 相关的算法功能。
"""

from typing import List, Set
from collections import OrderedDict


def fifo_page_replacement(pages: List[int], frame_count: int) -> int:
    """
    FIFO页面置换

    最简单的策略：淘汰最早进入的页面

    参数：
        pages: 访问序列
        frame_count: 物理页框数

    返回：缺页次数
    """
    frames = []
    page_faults = 0
    queue = []  # 记录进入顺序

    for page in pages:
        if page in frames:
            # 命中
            continue

        page_faults += 1

        if len(frames) < frame_count:
            frames.append(page)
            queue.append(page)
        else:
            # FIFO: 淘汰最早进入的
            oldest = queue.pop(0)
            frames.remove(oldest)
            frames.append(page)
            queue.append(page)

    return page_faults


def lru_page_replacement(pages: List[int], frame_count: int) -> int:
    """
    LRU页面置换（Least Recently Used）

    淘汰最近最少使用的页面

    参数：
        pages: 访问序列
        frame_count: 物理页框数

    返回：缺页次数
    """
    frames = []
    page_faults = 0
    access_order = OrderedDict()  # 记录访问顺序

    for page in pages:
        if page in frames:
            # 命中，更新访问顺序
            access_order.move_to_end(page)
            continue

        page_faults += 1

        if len(frames) < frame_count:
            frames.append(page)
            access_order[page] = True
        else:
            # LRU: 淘汰最久未访问的
            lru_page = next(iter(access_order))
            del access_order[lru_page]
            frames.remove(lru_page)
            frames.append(page)
            access_order[page] = True

    return page_faults


def optimal_page_replacement(pages: List[int], frame_count: int) -> int:
    """
    OPT页面置换（最佳置换）

    淘汰未来最长时间不使用的页面

    这是理想算法，实际不可实现（需要预知未来）

    参数：
        pages: 访问序列
        frame_count: 物理页框数

    返回：缺页次数
    """
    frames = []
    page_faults = 0

    for i, page in enumerate(pages):
        if page in frames:
            continue

        page_faults += 1

        if len(frames) < frame_count:
            frames.append(page)
        else:
            # 找未来最久不用的
            future_use = {}
            for p in frames:
                try:
                    future_use[p] = pages[i+1:].index(p)
                except ValueError:
                    future_use[p] = float('inf')

            victim = max(future_use, key=future_use.get)
            frames.remove(victim)
            frames.append(page)

    return page_faults


def lfu_page_replacement(pages: List[int], frame_count: int) -> int:
    """
    LFU页面置换（Least Frequently Used）

    淘汰使用频率最低的页面
    """
    frames = []
    freq = {}  # 页面访问频率
    page_faults = 0

    for page in pages:
        freq[page] = freq.get(page, 0) + 1

        if page in frames:
            continue

        page_faults += 1

        if len(frames) < frame_count:
            frames.append(page)
        else:
            # 找最低频的
            min_freq_page = min(frames, key=lambda p: freq[p])
            frames.remove(min_freq_page)
            frames.append(page)

    return page_faults


def simulate_all(pages: List[int], frame_count: int) -> dict:
    """
    对比所有算法
    """
    results = {
        'FIFO': fifo_page_replacement(pages, frame_count),
        'LRU': lru_page_replacement(pages, frame_count),
        'OPT': optimal_page_replacement(pages, frame_count),
        'LFU': lfu_page_replacement(pages, frame_count),
    }

    return results


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 页面置换算法测试 ===\n")

    # 页面访问序列
    pages = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]

    print(f"页面访问序列: {pages}")
    print(f"序列长度: {len(pages)}")
    print()

    for frame_count in [3, 4]:
        print(f"--- 页框数 = {frame_count} ---")
        results = simulate_all(pages, frame_count)

        for algo, faults in results.items():
            hit = len(pages) - faults
            print(f"  {algo}: 缺页{faults}次, 命中{hit}次, 缺页率={faults/len(pages)*100:.1f}%")
        print()

    # Belady现象演示
    print("=== Belady现象（抖动）===")
    print("增加页框数可能导致更多缺页（FIFO特有）")
    print()

    pages2 = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
    print(f"序列: {pages2}")
    print(f"FIFO: 页框3 -> {fifo_page_replacement(pages2, 3)} 次缺页")
    print(f"FIFO: 页框4 -> {fifo_page_replacement(pages2, 4)} 次缺页")

    print("\n说明：")
    print("  - FIFO最简单但会抖动（Belady现象）")
    print("  - LRU实际效果好，但实现开销大")
    print("  - OPT是理想基准，无法实际实现")
