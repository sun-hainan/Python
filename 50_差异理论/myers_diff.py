# -*- coding: utf-8 -*-

"""

算法实现：差异理论 / myers_diff



本文件实现 myers_diff 相关的算法功能。

"""



def myers_diff(seq_a, seq_b):

    """

    计算两个序列之间的Myers diff

    

    参数:

        seq_a: 第一个序列（原始序列）

        seq_b: 第二个序列（目标序列）

    

    返回:

        编辑脚本列表，每个元素为(op, index, value)元组

        op为'insert'(插入), 'delete'(删除), 'equal'(相同)

    """

    # 获取两个序列的长度

    n = len(seq_a)

    m = len(seq_b)

    

    # 处理空序列的边界情况

    if n == 0:

        return [('insert', i, seq_b[i]) for i in range(m)]

    if m == 0:

        return [('delete', i, seq_a[i]) for i in range(n)]

    

    # 计算最大编辑距离（最多需要N+M步）

    max_dist = n + m

    

    # 保存所有可达的位置，V[d] = {x坐标, y坐标} 

    # 其中y = x + d，用于跟踪在给定编辑距离下可以到达的位置

    v = {}

    

    # 记录是否到达终点以及对应的编辑距离

    reached_end = False

    end_x = 0

    end_y = 0

    

    # 存储编辑脚本结果

    trace = []

    

    # 主循环：逐步增加编辑距离，直到找到解

    for d in range(max_dist + 1):

        # 在当前编辑距离d下，存储所有可达的x坐标

        v[d] = set()

        

        # 遍历所有可能的k值（k = x - y，对角线索引）

        for k in range(-d, d + 1, 2):

            # 确定起点的x坐标

            # 如果k是边界(-d或d)，只能从特定方向到达

            if k == -d or (k != d and v[d-1].get(k-1, -1) < v[d-1].get(k+1, -1)):

                # 从上方下来（删除操作）

                x = v[d-1].get(k+1, 0) if k == -d else v[d-1].get(k+1, 0)

            else:

                # 从左方过来（插入操作）

                x = v[d-1].get(k-1, 0) + 1

            

            # 计算对应的y坐标

            y = x - k

            

            # 沿着对角线向右下方向走，记录所有匹配

            while x < n and y < m and seq_a[x] == seq_b[y]:

                x += 1

                y += 1

            

            # 记录在这个编辑距离下到达的x坐标

            v[d][k] = x

            

            # 检查是否到达终点

            if x >= n and y >= m:

                reached_end = True

                end_x = x

                end_y = y

                trace.append((d, k, x))

                break

        

        if reached_end:

            break

        

        trace.append((d, None, dict(v[d])))

    

    # 回溯找出编辑脚本

    return backtrack(trace, seq_a, seq_b, n, m)





def backtrack(trace, seq_a, seq_b, n, m):

    """

    从trace回溯构建编辑脚本

    

    参数:

        trace: 编辑路径的跟踪记录

        seq_a: 原始序列

        seq_b: 目标序列

        n: 序列a的长度

        m: 序列b的长度

    

    返回:

        编辑脚本列表

    """

    # 如果trace为空，返回空脚本

    if not trace:

        return []

    

    # 从最后一个编辑距离开始回溯

    edits = []

    x = n

    y = m

    

    # 逆序遍历trace

    for d, k, val in reversed(trace):

        if k is None:

            continue

            

        # 确定上一步的位置

        if k == -d or (k != d and (k+1 not in val or val[k-1] < val[k+1])):

            # 从上方下来：删除操作

            prev_k = k + 1

        else:

            # 从左方过来：插入操作

            prev_k = k - 1

        

        prev_d = d - 1

        prev_x = val[prev_k] if prev_k in val else 0

        prev_y = prev_x - prev_k

        

        # 回溯过程中的操作

        while x > prev_x and y > prev_y:

            # 匹配操作

            x -= 1

            y -= 1

            edits.append(('equal', x, seq_a[x]))

        

        if d > 0:

            if x > prev_x:

                # 删除操作

                edits.append(('delete', prev_x, seq_a[prev_x]))

            elif y > prev_y:

                # 插入操作

                edits.append(('insert', prev_y, seq_b[prev_y]))

    

    # 反转得到正确顺序

    edits.reverse()

    return edits





def format_diff(edits):

    """

    格式化编辑脚本为可读字符串

    

    参数:

        edits: 编辑脚本列表

    

    返回:

        格式化的字符串

    """

    result = []

    for op, idx, val in edits:

        if op == 'insert':

            result.append(f"+ {val}")  # 插入用+号

        elif op == 'delete':

            result.append(f"- {val}")  # 删除用-号

        else:

            result.append(f"  {val}")  # 相同用空格

    return '\n'.join(result)





# ==================== 测试代码 ====================

if __name__ == "__main__":

    # 测试用例1：简单字符串diff

    print("=" * 50)

    print("测试1: 简单字符串比较")

    print("=" * 50)

    

    seq_a = "ABCABBA"

    seq_b = "CBABAC"

    print(f"原始序列: {seq_a}")

    print(f"目标序列: {seq_b}")

    

    edits = myers_diff(seq_a, seq_b)

    print("\n编辑脚本:")

    print(format_diff(edits))

    

    # 测试用例2：单词列表diff

    print("\n" + "=" * 50)

    print("测试2: 单词列表比较")

    print("=" * 50)

    

    words_a = ["The", "quick", "brown", "fox", "jumps"]

    words_b = ["The", "slow", "brown", "fox", "walks"]

    print(f"原始: {words_a}")

    print(f"目标: {words_b}")

    

    edits = myers_diff(words_a, words_b)

    print("\n编辑脚本:")

    print(format_diff(edits))

    

    # 测试用例3：空序列

    print("\n" + "=" * 50)

    print("测试3: 空序列边界情况")

    print("=" * 50)

    

    edits = myers_diff("", "hello")

    print("空序列到'hello'的编辑脚本:")

    print(format_diff(edits))

    

    # 测试用例4：相同序列

    print("\n" + "=" * 50)

    print("测试4: 相同序列")

    print("=" * 50)

    

    edits = myers_diff("same", "same")

    print("'same'到'same'的编辑脚本:")

    print(format_diff(edits))

