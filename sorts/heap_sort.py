"""
堆排序 (Heap Sort) - 中文注释版
==========================================

算法原理：
    堆排序利用堆这种数据结构进行排序。
    堆是一种完全二叉树，分为最大堆和最小堆。
    这里使用最大堆：父节点的值大于子节点的值。

堆的基本概念：
    - 完全二叉树：除了最后一层，其他层节点数都达到最大
    - 父节点 i 的左子节点：2i + 1
    - 父节点 i 的右子节点：2i + 2
    - 子节点 i 的父节点：(i - 1) // 2

算法步骤：
    1. 构建最大堆：将数组重新排列成最大堆
    2. 逐个取出堆顶最大元素，放到数组末尾
    3. 调整剩余元素保持最大堆性质
    4. 重复直到堆中只剩一个元素

时间复杂度：
    - 平均: O(n log n)
    - 最坏: O(n log n)
    - 最好: O(n log n)

空间复杂度：O(1) - 原地排序

算法特点：
    - 不稳定排序
    - 利用堆这种特殊数据结构实现高效排序
    - 适合需要求 Top-K 元素的场景
"""


def heapify(unsorted: list[int], index: int, heap_size: int) -> None:
    """
    堆化操作：将指定节点向下调整为最大堆

    算法思想：
        从当前节点开始，比较它与左右子节点的值。
        如果子节点中较大的值大于当前节点，则交换它们的位置。
        然后继续向下调整，直到满足最大堆性质或到达叶子节点。

    参数:
        unsorted:  未排序的数组（作为堆的底层存储）
        index:    当前要调整的节点索引
        heap_size: 堆的有效大小（用于限定操作范围）

    示例:
        >>> unsorted = [1, 4, 3, 5, 2]
        >>> heapify(unsorted, 0, len(unsorted))
        >>> unsorted
        [4, 5, 3, 1, 2]
    """
    largest = index           # 假设当前节点是最大值
    left_index = 2 * index + 1   # 左子节点
    right_index = 2 * index + 2  # 右子节点

    # 检查左子节点是否大于当前最大值
    if left_index < heap_size and unsorted[left_index] > unsorted[largest]:
        largest = left_index

    # 检查右子节点是否大于当前最大值
    if right_index < heap_size and unsorted[right_index] > unsorted[largest]:
        largest = right_index

    # 如果最大值不是当前节点，则交换并继续向下调整
    if largest != index:
        unsorted[largest], unsorted[index] = (unsorted[index], unsorted[largest])
        heapify(unsorted, largest, heap_size)


def heap_sort(unsorted: list[int]) -> list[int]:
    """
    堆排序主函数

    参数:
        unsorted: 要排序的可变集合

    返回:
        同一个集合，按升序排列

    示例:
        >>> heap_sort([0, 5, 3, 2, 2])
        [0, 2, 2, 3, 5]
        >>> heap_sort([])
        []
        >>> heap_sort([-2, -5, -45])
        [-45, -5, -2]
        >>> heap_sort([3, 7, 9, 28, 123, -5, 8, -30, -200, 0, 4])
        [-200, -30, -5, 0, 3, 4, 7, 8, 9, 28, 123]
    """
    n = len(unsorted)

    # 步骤1：构建最大堆（从最后一个非叶子节点向前堆化）
    # 最后一个非叶子节点索引 = n // 2 - 1
    for i in range(n // 2 - 1, -1, -1):
        heapify(unsorted, i, n)

    # 步骤2：逐个取出堆顶最大元素，放到数组末尾
    for i in range(n - 1, 0, -1):
        # 将堆顶（最大值）与当前堆的最后一个元素交换
        unsorted[0], unsorted[i] = unsorted[i], unsorted[0]
        # 调整堆，排除已排序的元素
        heapify(unsorted, 0, i)

    return unsorted


if __name__ == "__main__":
    import doctest

    doctest.testmod()
    user_input = input("输入以逗号分隔的数字:\n").strip()
    if user_input:
        unsorted = [int(item) for item in user_input.split(",")]
        print(f"排序结果: {heap_sort(unsorted)}")
