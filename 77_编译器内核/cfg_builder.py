# -*- coding: utf-8 -*-

"""

算法实现：编译器内核 / cfg_builder



本文件实现 cfg_builder 相关的算法功能。

"""



from dataclasses import dataclass, field

from typing import List, Dict, Set, Optional, Tuple

from collections import deque



from intermediate_representation import OpCode

from basic_block import BasicBlock, BasicBlockBuilder





@dataclass

class CFGNode:

    """CFG节点"""

    block: BasicBlock  # 对应的基本块

    dominators: Set[int] = field(default_factory=set)  # 支配节点集合

    dominated_by: List[int] = field(default_factory=list)  # 直接支配节点

    dom_tree_sons: List[int] = field(default_factory=list)  # 支配树子节点

    immediate_dominator: Optional[int] = None  # 立即支配节点

    post_order: int = -1  # 逆后序编号

    dfs_order: int = -1  # DFS序





class ControlFlowGraph:

    """

    控制流图



    支持:

    1. 基本块组织

    2. 前驱后继关系

    3. Dominator关系计算

    4. 循环检测

    5. 必经节点树(Dominator Tree)

    """



    def __init__(self, blocks: List[BasicBlock]):

        self.blocks: Dict[int, CFGNode] = {}  # block_id -> CFGNode

        self.entry_block: Optional[int] = None  # 入口块ID

        self.exit_block: Optional[int] = None  # 出口块ID

        self.reverse_post_order: List[int] = []  # 逆后序



        # 初始化节点

        for block in blocks:

            self.blocks[block.block_id] = CFGNode(block=block)



        # 构建CFG

        self._build_cfg(blocks)



    def _build_cfg(self, blocks: List[BasicBlock]):

        """从基本块构建CFG"""

        # 入口块是第一个基本块

        if blocks:

            self.entry_block = blocks[0].block_id



            # 出口块是最后一个有RETURN或FUNC_END的基本块

            for block in reversed(blocks):

                last = block.get_last_instruction()

                if last and last.op in [OpCode.RETURN, OpCode.FUNC_END]:

                    self.exit_block = block.block_id

                    break



    def add_edge(self, from_block: int, to_block: int):

        """添加边"""

        if from_block in self.blocks and to_block in self.blocks:

            from_node = self.blocks[from_block].block

            if to_block not in from_node.successors:

                from_node.successors.append(to_block)



            to_node = self.blocks[to_block].block

            if from_block not in to_node.predecessors:

                to_node.predecessors.append(from_block)



    def get_predecessors(self, block_id: int) -> List[int]:

        """获取前驱块列表"""

        if block_id in self.blocks:

            return self.blocks[block_id].block.predecessors

        return []



    def get_successors(self, block_id: int) -> List[int]:

        """获取后继块列表"""

        if block_id in self.blocks:

            return self.blocks[block_id].block.successors

        return []



    def compute_dominators(self):

        """

        计算所有节点的Dominator集合

        使用数据流迭代算法

        """

        if self.entry_block is None:

            return



        # 初始化: 入口节点的dominators只有自己

        for node in self.blocks.values():

            if node.block.block_id == self.entry_block:

                node.dominators = {self.entry_block}

            else:

                # 非入口节点的dominators初始为所有节点

                node.dominators = set(self.blocks.keys())



        # 迭代计算

        changed = True

        iterations = 0

        while changed and iterations < 100:

            changed = False

            iterations += 1



            for block_id, node in self.blocks.items():

                if block_id == self.entry_block:

                    continue



                preds = self.get_predecessors(block_id)

                if not preds:

                    continue



                # 新dominators = 所有前驱的dominators集合的交集 + 自己

                new_dom = set()

                for pred in preds:

                    if pred in self.blocks:

                        new_dom |= self.blocks[pred].dominators



                if block_id not in new_dom:

                    new_dom.add(block_id)



                if new_dom != node.dominators:

                    node.dominators = new_dom

                    changed = True



        # 计算立即支配节点

        self._compute_immediate_dominators()



    def _compute_immediate_dominators(self):

        """计算立即支配节点"""

        for block_id, node in self.blocks.items():

            if block_id == self.entry_block:

                node.immediate_dominator = None

                continue



            # 排除自己的所有dominators中,找一个最近的(被其他所有支配的)

            other_doms = node.dominators - {block_id}

            immediate = None



            for candidate in other_doms:

                is_immediate = True

                for other in other_doms:

                    if other != candidate and candidate not in self.blocks[other].dominators:

                        is_immediate = False

                        break

                if is_immediate:

                    immediate = candidate

                    break



            node.immediate_dominator = immediate



        # 构建支配树

        self._build_dom_tree()



    def _build_dom_tree(self):

        """构建支配树"""

        for block_id, node in self.blocks.items():

            node.dom_tree_sons = []



        for block_id, node in self.blocks.items():

            if node.immediate_dominator is not None:

                parent_node = self.blocks[node.immediate_dominator]

                parent_node.dom_tree_sons.append(block_id)



    def find_loops(self) -> List[Dict]:

        """

        检测循环



        返回:

            循环列表,每个循环包含 {header, blocks, depth}

        """

        loops = []

        visited = set()



        def dfs_find_back_edge(header: int, path: Set[int]):

            """DFS找回边"""

            visited.add(header)



            for succ in self.get_successors(header):

                if succ in path:

                    # 找到回边,形成循环

                    loop_blocks = path.copy()

                    # 找到header在path中的位置

                    header_pos = None

                    for i, b in enumerate(path):

                        if b == header:

                            header_pos = i

                            break

                    if header_pos is not None:

                        for b in list(path)[header_pos:]:

                            loop_blocks.add(b)

                        loops.append({

                            "header": header,

                            "blocks": list(loop_blocks),

                            "back_edge_from": succ

                        })

                elif succ not in visited:

                    path.add(succ)

                    dfs_find_back_edge(succ, path)

                    path.remove(succ)



        if self.entry_block is not None:

            dfs_find_back_edge(self.entry_block, {self.entry_block})



        # 合并嵌套循环

        loops.sort(key=lambda x: len(x["blocks"]))



        return loops



    def compute_reverse_post_order(self):

        """

        计算逆后序遍历顺序

        用于指令调度和寄存器分配

        """

        self.reverse_post_order = []

        visited = set()



        def dfs_rpo(block_id: int):

            if block_id in visited:

                return

            visited.add(block_id)



            # 先访问所有后继

            for succ in self.get_successors(block_id):

                dfs_rpo(succ)



            # 后序位置

            self.blocks[block_id].post_order = len(self.reverse_post_order)

            self.reverse_post_order.append(block_id)



        if self.entry_block is not None:

            dfs_rpo(self.entry_block)



        # reverse为逆后序

        self.reverse_post_order.reverse()



    def is_dominated_by(self, block_id: int, potential_dom: int) -> bool:

        """检查block_id是否被potential_dom支配"""

        if block_id in self.blocks and potential_dom in self.blocks:

            return potential_dom in self.blocks[block_id].dominators

        return False



    def get_dominance_frontier(self, block_id: int) -> Set[int]:

        """

        获取block_id的支配边界

        用于SSA构建

        """

        df = set()

        node = self.blocks.get(block_id)



        if not node:

            return df



        # 如果block有多个前驱,且这些前驱不被block支配

        for pred in node.block.predecessors:

            runner = pred

            if runner != block_id and not self.is_dominated_by(runner, block_id):

                df.add(runner)



        # 考虑后继的支配边界

        for succ in node.block.successors:

            if succ != block_id and not self.is_dominated_by(succ, block_id):

                df.add(succ)



        return df





def print_cfg(cfg: ControlFlowGraph):

    """打印CFG"""

    print("=== 控制流图 ===")

    print(f"Entry Block: B{cfg.entry_block}")

    print(f"Exit Block: B{cfg.exit_block}")



    print("\n基本块:")

    for block_id, node in cfg.blocks.items():

        block = node.block

        print(f"\n  B{block_id}:")

        print(f"    Pred: {block.predecessors}")

        print(f"    Succ: {block.successors}")

        print(f"    IDom: {node.immediate_dominator}")

        print(f"    Dom: {sorted(node.dominators)}")

        if node.block.label:

            print(f"    Label: {node.block.label}")



    print("\n支配树:")

    for block_id, node in cfg.blocks.items():

        if not node.dom_tree_sons:

            print(f"  B{block_id} (leaf)")

        else:

            print(f"  B{block_id} -> {[f'B{s}' for s in node.dom_tree_sons]}")





if __name__ == "__main__":

    # 使用basic_block测试中的IR构建CFG

    from intermediate_representation import IRGenerator, Address



    gen = IRGenerator()

    gen.emit_func_begin("max")

    gen.emit(OpCode.LOAD_PARAM, arg1=Address.temp("a"))

    gen.emit(OpCode.LOAD_PARAM, arg1=Address.temp("b"))

    gen.emit_binary(OpCode.GT, Address.temp("t1"), Address.temp("a"), Address.temp("b"))

    gen.emit(OpCode.JUMP_IF, result=Address.label("Ltrue"), arg1=Address.temp("t1"))

    gen.emit_return(Address.variable("b"))

    gen.emit_jump("Lend")

    gen.emit_label("Ltrue")

    gen.emit_return(Address.variable("a"))

    gen.emit_label("Lend")

    gen.emit_func_end("max")



    # 构建基本块

    builder = BasicBlockBuilder()

    blocks = builder.build(gen.generate())



    # 构建CFG

    cfg = ControlFlowGraph(blocks)



    print_cfg(cfg)



    # 计算Dominators

    print("\n=== Dominator分析 ===")

    cfg.compute_dominators()

    for block_id, node in cfg.blocks.items():

        print(f"B{block_id}: Dom = {sorted(node.dominators)}, IDom = {node.immediate_dominator}")



    # 检测循环

    print("\n=== 循环检测 ===")

    loops = cfg.find_loops()

    if loops:

        for loop in loops:

            print(f"循环: header=B{loop['header']}, blocks={loop['blocks']}")

    else:

        print("未发现循环")



    # 逆后序

    print("\n=== 逆后序 ===")

    cfg.compute_reverse_post_order()

    print(f"顺序: {[f'B{b}' for b in cfg.reverse_post_order]}")

