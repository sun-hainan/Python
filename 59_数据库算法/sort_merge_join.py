# -*- coding: utf-8 -*-

"""

算法实现：数据库算法 / sort_merge_join



本文件实现 sort_merge_join 相关的算法功能。

"""



from typing import List, Tuple, Callable





def sort_merge_join(table1: List[dict], table2: List[dict],

                   key1: str, key2: str,

                   sort_key1: Callable = None, sort_key2: Callable = None) -> List[Tuple[dict, dict]]:

    """

    排序合并连接



    参数：

        table1: 第一个表（字典列表）

        table2: 第二个表

        key1, key2: 连接键

        sort_key1, sort_key2: 排序键函数



    返回：(row1, row2) 对列表

    """

    if not table1 or not table2:

        return []



    # 排序

    if sort_key1:

        sorted1 = sorted(table1, key=sort_key1)

    else:

        sorted1 = sorted(table1, key=lambda r: r[key1])



    if sort_key2:

        sorted2 = sorted(table2, key=sort_key2)

    else:

        sorted2 = sorted(table2, key=lambda r: r[key2])



    # 合并扫描

    results = []

    i, j = 0, 0



    while i < len(sorted1) and j < len(sorted2):

        v1 = sorted1[i][key1]

        v2 = sorted2[j][key2]



        if v1 < v2:

            i += 1

        elif v1 > v2:

            j += 1

        else:

            # 相等，输出所有匹配

            # 先收集所有匹配

            k = j

            while k < len(sorted2) and sorted2[k][key2] == v1:

                results.append((sorted1[i], sorted2[k]))

                k += 1

            i += 1



    return results





def external_sort_merge_join(file1: str, file2: str,

                             key1: str, key2: str,

                             chunk_size: int = 10000) -> int:

    """

    外部排序合并连接（处理大数据）



    参数：

        file1, file2: 输入文件路径

        key1, key2: 连接键

        chunk_size: 每次能加载进内存的记录数



    返回：匹配对数量

    """

    # 简化实现

    # 实际需要：

    # 1. 分块排序（外部排序）

    # 2. 归并阶段

    # 3. 多路归并

    return 0





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 排序合并连接测试 ===\n")



    # 表1: Customers

    customers = [

        {'id': 1, 'name': 'Alice', 'city_id': 101},

        {'id': 2, 'name': 'Bob', 'city_id': 102},

        {'id': 3, 'name': 'Charlie', 'city_id': 101},

        {'id': 4, 'name': 'David', 'city_id': 103},

    ]



    # 表2: Orders

    orders = [

        {'order_id': 100, 'customer_id': 1, 'amount': 250},

        {'order_id': 101, 'customer_id': 3, 'amount': 150},

        {'order_id': 102, 'customer_id': 1, 'amount': 300},

        {'order_id': 103, 'customer_id': 5, 'amount': 100},

    ]



    print("Customers:")

    for c in customers:

        print(f"  {c}")



    print("\nOrders:")

    for o in orders:

        print(f"  {o}")



    # 执行 Join

    results = sort_merge_join(customers, orders, 'id', 'customer_id')



    print(f"\nJoin 结果 ({len(results)} 对):")

    for c, o in results:

        print(f"  Customer({c['id']}, {c['name']}) -> Order({o['order_id']}, ${o['amount']})")



    print("\n说明：")

    print("  - 如果数据已排序，Sort-Merge Join很高效")

    print("  - 否则需要额外排序开销")

    print("  - Hash Join适合等值连接")

