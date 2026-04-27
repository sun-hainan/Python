# -*- coding: utf-8 -*-

"""

算法实现：程序分析 / dominators



本文件实现 dominators 相关的算法功能。

"""



from typing import Set, List, Dict, Tuple





class DominatorAnalyzer:

    """支配节点分析器"""



    def __init__(self, graph: Dict[int, List[int]]):

        """

        参数：

            graph: 邻接表 {node: [successors...]}

        """

        self.graph = graph

        self.nodes = list(graph.keys())

        self.entry = min(self.nodes)  # 假设最小节点是入口



    def analyze(self) -> Dict[int, Set[int]]:

        """计算每个节点的支配集合"""

        # 初始化：除了入口，其他节点的支配集都是全体

        dom = {n: set(self.nodes) for n in self.nodes}

        dom[self.entry] = {self.entry}



        changed = True

        iterations = 0

        while changed:

            changed = False

            iterations += 1



            for node in self.nodes:

                if node == self.entry:

                    continue



                preds = self._get_predecessors(node)

                if not preds:

                    continue



                # Dom(n) = {n} ∪ ∩(Dom(p) for p in preds)

                new_dom = {node}

                for pred in preds:

                    new_dom &= dom[pred]



                if new_dom != dom[node]:

                    dom[node] = new_dom

                    changed = True



        return dom



    def _get_predecessors(self, node: int) -> List[int]:

        """获取前驱节点"""

        preds = []

        for src, dsts in self.graph.items():

            if node in dsts:

                preds.append(src)

        return preds



    def get_idom(self, dom: Dict[int, Set[int]]) -> Dict[int, int]:

        """

        计算直接支配者（Immediate Dominator）



        idom(n) = 支配n且被n支配的其他节点中，最接近n的那个

        """

        idom = {}



        for node in self.nodes:

            if node == self.entry:

                continue



            dom_set = dom[node] - {node}



            # 找最近支配者

            candidates = [d for d in dom_set

                         if all(d in dom[other] for other in dom_set if other != d)]



            if candidates:

                # 选择深度最深的

                idom[node] = min(candidates, key=lambda x: len(dom[x]))



        return idom



    def build_dominator_tree(self, idom: Dict[int, int]) -> Dict[int, List[int]]:

        """构建支配树"""

        tree = {n: [] for n in self.nodes}



        for child, parent in idom.items():

            tree[parent].append(child)



        return tree





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 支配节点分析测试 ===\n")



    # 示例CFG：

    #     0

    #    / \

    #   1   2

    #   |\ /|

    #   | 3 |

    #    \ /

    #     4



    graph = {

        0: [1, 2],

        1: [2, 3],

        2: [3],

        3: [1, 4],

        4: [],

    }



    analyzer = DominatorAnalyzer(graph)



    print("CFG：")

    for node, succs in graph.items():

        print(f"  {node} -> {succs}")



    dom = analyzer.analyze()



    print("\n支配集合：")

    for node, dom_set in dom.items():

        print(f"  Dom({node}): {sorted(dom_set)}")



    idom = analyzer.get_idom(dom)



    print("\n直接支配者（IDOM）：")

    for node, parent in idom.items():

        print(f"  idom({node}) = {parent}")



    tree = analyzer.build_dominator_tree(idom)



    print("\n支配树：")

    for node, children in tree.items():

        if children:

            print(f"  {node}: {children}")



    print("\n说明：")

    print("  - 入口节点0支配所有节点")

    print("  - 节点3被{0,1,2,3}支配，直接支配者是节点2")

    print("  - 支配树反映了程序的嵌套结构")

