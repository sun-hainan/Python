# -*- coding: utf-8 -*-

"""

算法实现：生物信息学 / de_bruijn_graph



本文件实现 de_bruijn_graph 相关的算法功能。

"""



from collections import defaultdict





class DeBruijnGraph:

    """De Bruijn图"""



    def __init__(self, k: int):

        self.k = k

        self.graph = defaultdict(list)  # prefix -> [suffixes]

        self.in_degree = defaultdict(int)

        self.out_degree = defaultdict(int)



    def add_sequence(self, sequence: str):

        """添加一条序列（reads）"""

        if len(sequence) < self.k:

            return



        for i in range(len(sequence) - self.k + 1):

            kmer = sequence[i:i+self.k]

            prefix = kmer[:-1]

            suffix = kmer[1:]

            self.graph[prefix].append(suffix)

            self.out_degree[prefix] += 1

            self.in_degree[suffix] += 1



    def get_eulerian_path(self) -> str:

        """

        找欧拉路径（重构序列）



        返回：重构的序列

        """

        # 找起点（出度 - 入度 = 1）

        start = None

        for node in self.graph:

            if self.out_degree[node] - self.in_degree[node] == 1:

                start = node

                break



        if start is None:

            start = list(self.graph.keys())[0]



        # Hierholzer算法

        path = []

        stack = [start]



        while stack:

            node = stack[-1]

            if self.graph[node]:

                next_node = self.graph[node].pop()

                stack.append(next_node)

            else:

                path.append(stack.pop())



        path.reverse()



        # 将节点连成序列

        if not path:

            return ""



        result = path[0]

        for node in path[1:]:

            result += node[-1]



        return result



    def simplify(self):

        """简化图（去除悬垂边等）"""

        # 移除度为1的中间节点（路径压缩）

        changed = True

        while changed:

            changed = False

            to_remove = []



            for node in self.graph:

                if len(self.graph[node]) == 1 and self.in_degree[node] == 1 and self.out_degree[node] == 1:

                    # 中间节点，可以压缩

                    nxt = self.graph[node][0]

                    self.graph[node] = []  # 标记删除

                    to_remove.append(node)



            for node in to_remove:

                del self.graph[node]





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== De Bruijn图测试 ===\n")



    k = 3

    reads = [

        "ACTGATCGATCGTACG",

        "CGATCGTACGATCGT",

        "ATCGTACGATCGTAG"

    ]



    print(f"k-mer长度: {k}")

    print(f"Reads: {reads}")



    # 构建图

    dbg = DeBruijnGraph(k)

    for read in reads:

        dbg.add_sequence(read)



    print(f"\n图中的边:")

    for prefix, suffixes in dbg.graph.items():

        for s in suffixes:

            print(f"  {prefix} -> {s}")



    # 重构

    genome = dbg.get_eulerian_path()

    print(f"\n重构的基因组序列: {genome}")



    print("\n说明：")

    print("  - De Bruijn图将序列组装问题转化为欧拉路径问题")

    print("  - k选择：太小导致连通性差，太大导致组合爆炸")

    print("  - 实际组装工具（SPAdes）会处理重复、错误等问题")

