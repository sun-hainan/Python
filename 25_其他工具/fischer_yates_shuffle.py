# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / fischer_yates_shuffle

本文件实现 fischer_yates_shuffle 相关的算法功能。
"""

#!/usr/bin/python
"""
The Fisher-Yates shuffle is an algorithm for generating a random permutation of a
finite sequence.
For more details visit
wikipedia/Fischer-Yates-Shuffle.
"""

import random
from typing import Any



# fisher_yates_shuffle 函数实现
def fisher_yates_shuffle(data: list) -> list[Any]:
    for _ in range(len(data)):
    # 遍历循环
        a = random.randint(0, len(data) - 1)
        b = random.randint(0, len(data) - 1)
        data[a], data[b] = data[b], data[a]
    return data
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    integers = [0, 1, 2, 3, 4, 5, 6, 7]
    strings = ["python", "says", "hello", "!"]
    print("Fisher-Yates Shuffle:")
    print("List", integers, strings)
    print("FY Shuffle", fisher_yates_shuffle(integers), fisher_yates_shuffle(strings))
