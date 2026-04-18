"""
基数排序 (Radix Sort) - 中文注释版
==========================================

算法原理：
    基数排序是一种非比较排序算法，按数字的位数进行排序。
    从最低位（个位）开始，依次到最高位。
    每轮按当前位上的数字将元素分配到 0-9 共 10 个桶中，
    然后按顺序收集，再进行下一位排序。

核心思想：
    "桶"的思想：按位分散 → 收集 → 再按下一位分散

时间复杂度：
    - 平均: O(n * k)，k 为数字位数
    - 最坏: O(n * k)
    - 最好: O(n * k)

空间复杂度：O(n + k)

算法特点：
    - 稳定排序
    - 非比较排序
    - 适合整数排序，特别是范围较大的整数
    - 通常配合计数排序作为桶排序使用（LSD 版本）
"""

from __future__ import annotations

RADIX = 10  # 十进制基数


def radix_sort(list_of_ints: list[int]) -> list[int]:
    """
    基数排序（LSD - 最低位优先）

    参数:
        list_of_ints: 整数列表

    返回:
        排序后的整数列表

    示例:
        >>> radix_sort([0, 5, 3, 2, 2])
        [0, 2, 2, 3, 5]
        >>> radix_sort(list(range(15))) == sorted(range(15))
        True
        >>> radix_sort([1,100,10,1000]) == sorted([1,100,10,1000])
        True
    """
    # 找出最大数字，确定排序轮数
    placement = 1  # 当前处理的位数（1=个位，10=十位，100=百位...）
    max_digit = max(list_of_ints)

    # 从个位到最高位，逐位排序
    while placement <= max_digit:
        # 创建 10 个桶（对应 0-9）
        buckets: list[list] = [[] for _ in range(RADIX)]

        # 将元素分配到对应桶中
        for i in list_of_ints:
            tmp = int((i / placement) % RADIX)  # 取当前位的数字
            buckets[tmp].append(i)

        # 按桶顺序收集元素，形成新一轮序列
        a = 0
        for b in range(RADIX):
            for i in buckets[b]:
                list_of_ints[a] = i
                a += 1

        # 处理下一位
        placement *= RADIX

    return list_of_ints


if __name__ == "__main__":
    import doctest

    doctest.testmod()

    user_input = input("输入以逗号分隔的数字:\n").strip()
    unsorted = [int(item) for item in user_input.split(",")]
    print(radix_sort(unsorted))
