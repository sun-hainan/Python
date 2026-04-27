# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / bucket_sort

本文件实现 bucket_sort 相关的算法功能。
"""

from __future__ import annotations

#!/usr/bin/env python3
"""
Illustrate how to implement bucket sort algorithm.

Author: OMKAR PATHAK
This program will illustrate how to implement bucket sort algorithm

Wikipedia says: Bucket sort, or bin sort, is a sorting algorithm that works
by distributing the elements of an array into a number of buckets.
Each bucket is then sorted individually, either using a different sorting
algorithm, or by recursively applying the bucket sorting algorithm. It is a
distribution sort, and is a cousin of radix sort in the most to least
significant digit flavour.
Bucket sort is a generalization of pigeonhole sort. Bucket sort can be
implemented with comparisons and therefore can also be considered a
comparison sort algorithm. The computational complexity estimates involve the
number of buckets.

Time Complexity of Solution:
Worst case scenario occurs when all the elements are placed in a single bucket.
The overall performance would then be dominated by the algorithm used to sort each
bucket. In this case, O(n log n), because of TimSort

Average Case O(n + (n^2)/k + k), where k is the number of buckets

If k = O(n), time complexity is O(n)

Source: https://en.wikipedia.org/wiki/Bucket_sort
"""




# bucket_sort 函数实现
def bucket_sort(my_list: list, bucket_count: int = 10) -> list:
    """
    >>> data = [-1, 2, -5, 0]
    >>> bucket_sort(data) == sorted(data)
    True
    >>> data = [9, 8, 7, 6, -12]
    >>> bucket_sort(data) == sorted(data)
    True
    >>> data = [.4, 1.2, .1, .2, -.9]
    >>> bucket_sort(data) == sorted(data)
    True
    >>> bucket_sort([]) == sorted([])
    True
    >>> data = [-1e10, 1e10]
    >>> bucket_sort(data) == sorted(data)
    True
    >>> import random
    >>> collection = random.sample(range(-50, 50), 50)
    >>> bucket_sort(collection) == sorted(collection)
    True
    >>> data = [1, 2, 2, 1, 1, 3]
    >>> bucket_sort(data) == sorted(data)
    True
    >>> data = [5, 5, 5, 5, 5]
    >>> bucket_sort(data) == sorted(data)
    True
    >>> data = [1000, -1000, 500, -500, 0]
    >>> bucket_sort(data) == sorted(data)
    True
    >>> data = [5.5, 2.2, -1.1, 3.3, 0.0]
    >>> bucket_sort(data) == sorted(data)
    True
    >>> bucket_sort([1]) == [1]
    True
    >>> data = [-1.1, -1.5, -3.4, 2.5, 3.6, -3.3]
    >>> bucket_sort(data) == sorted(data)
    True
    >>> data = [9, 2, 7, 1, 5]
    >>> bucket_sort(data) == sorted(data)
    True
    """

    if len(my_list) == 0 or bucket_count <= 0:
    # 条件判断
        return []
    # 返回结果

    min_value, max_value = min(my_list), max(my_list)
    if min_value == max_value:
    # 条件判断
        return my_list
    # 返回结果

    bucket_size = (max_value - min_value) / bucket_count
    buckets: list[list] = [[] for _ in range(bucket_count)]

    for val in my_list:
    # 遍历循环
        index = min(int((val - min_value) / bucket_size), bucket_count - 1)
        buckets[index].append(val)

    return [val for bucket in buckets for val in sorted(bucket)]
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    from doctest import testmod

    testmod()
    assert bucket_sort([4, 5, 3, 2, 1]) == [1, 2, 3, 4, 5]
    assert bucket_sort([0, 1, -10, 15, 2, -2]) == [-10, -2, 0, 1, 2, 15]
    assert bucket_sort([1.1, 1.2, -1.2, 0, 2.4]) == [-1.2, 0, 1.1, 1.2, 2.4]
    assert bucket_sort([5, 5, 5, 5, 5]) == [5, 5, 5, 5, 5]
    assert bucket_sort([-5, -1, -6, -2]) == [-6, -5, -2, -1]
