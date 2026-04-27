"""

并行算法相关算法实现。



文件名: __init__.py

"""



# -*- coding: utf-8 -*-

"""

并行算法包



本包包含各种并行算法的Python实现。



主要模块：

- parallel_reduction: 树形并行归约

- blelloch_scan: Blelloch并行前缀和

- bitonic_sort: 双调排序

- work_pool: 工作池并行模式

- thread_pool: 线程池实现

- parallel_matrix_multiply: Fox算法并行矩阵乘法

- parallel_sort: 并行排序算法

- parallel_merge: 并行合并算法



使用方法：

    from parallel_reduction import parallel_sum

    result = parallel_sum([1, 2, 3, 4, 5])

"""



# 版本信息

__version__ = "1.0.0"

__all__ = [

    "parallel_reduction",

    "blelloch_scan",

    "bitonic_sort",

    "work_pool",

    "thread_pool",

    "parallel_matrix_multiply",

    "parallel_sort",

    "parallel_merge",

]



if __name__ == "__main__":

    # 基础功能测试

    # 请在此添加测试代码

    pass

