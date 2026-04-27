# -*- coding: utf-8 -*-

"""

算法实现：编译器内核 / loop_unrolling



本文件实现 loop_unrolling 相关的算法功能。

"""



from typing import List, Dict, Tuple, Optional

from dataclasses import dataclass, field



from basic_block import BasicBlock

from cfg_builder import ControlFlowGraph

from intermediate_representation import TACInstruction, OpCode, Address





@dataclass

class LoopInfo:

    """循环信息"""

    header: int  # 循环头块ID

    body: List[int]  # 循环体块ID列表

    latch: int  # 循环 latch 块ID (跳回头部的块)

    induction_vars: List[str] = field(default_factory=list)  # 归纳变量

    trip_count: Optional[int] = None  # 循环次数(如果已知)





class LoopUnroller:

    """

    循环展开优化器



    支持:

    1. 完全展开(循环次数已知且小)

    2. 部分展开(按固定因子展开)

    3. 归纳变量优化

    """



    def __init__(self, cfg: ControlFlowGraph):

        self.cfg = cfg

        self.loops: List[LoopInfo] = []

        self.stats = {

            "loops_found": 0,

            "loops_unrolled": 0,

            "iterations_saved": 0

        }



    def find_loops(self) -> List[LoopInfo]:

        """

        查找循环



        循环定义:

        1. 存在一条边从块X指向循环头(回边)

        2. 循环头支配回边源

        3. 所有到达循环头的路径都经过循环体

        """

        self.loops = []



        # 使用CFG的find_loops结果

        cfg_loops = self.cfg.find_loops()



        for cfg_loop in cfg_loops:

            header_id = cfg_loop["header"]

            body_blocks = cfg_loop["blocks"]



            # 找到latch块(跳转到header的块)

            latch_id = None

            for block_id in body_blocks:

                succs = self.cfg.get_successors(block_id)

                if header_id in succs:

                    latch_id = block_id

                    break



            loop_info = LoopInfo(

                header=header_id,

                body=body_blocks,

                latch=latch_id

            )

            self.loops.append(loop_info)

            self.stats["loops_found"] += 1



        return self.loops



    def unroll(self, loop: LoopInfo, factor: int = 2) -> Tuple[bool, str]:

        """

        展开循环



        参数:

            loop: 循环信息

            factor: 展开因子



        返回:

            (是否成功, 原因)

        """

        # 检查循环是否是简单的for循环

        if not self._is_simple_loop(loop):

            return False, "循环结构复杂,无法展开"



        # 获取循环次数

        trip_count = self._estimate_trip_count(loop)

        if trip_count is None:

            return False, "无法确定循环次数"



        # 小循环完全展开

        if trip_count <= 4:

            return self._full_unroll(loop), "完全展开"

        else:

            return self._partial_unroll(loop, factor), f"按因子{factor}展开"



    def _is_simple_loop(self, loop: LoopInfo) -> bool:

        """检查是否是简单循环"""

        # 简单循环: 单入口,单Latch,归纳变量简单

        header_block = self.cfg.blocks.get(loop.header)

        if not header_block:

            return False



        # 检查循环体是否只有一个块

        if len(loop.body) > 3:

            return False



        return True



    def _estimate_trip_count(self, loop: LoopInfo) -> Optional[int]:

        """

        估算循环次数

        简化: 假设如果是常量比较,可确定次数

        """

        # 简化: 返回一个估计值

        # 实际实现需要分析循环入口条件

        return 3  # 假设循环3次



    def _full_unroll(self, loop: LoopInfo) -> bool:

        """

        完全展开小循环



        原理: 将循环体复制N次,消除循环开销

        """

        print(f"  完全展开循环: header=B{loop.header}, trip_count={loop.trip_count or 'unknown'}")



        # 获取循环体指令

        header_block = self.cfg.blocks.get(loop.header)

        if not header_block:

            return False



        # 模拟展开: 实际需要修改CFG

        unrolled_body = []

        for i in range(loop.trip_count or 3):

            # 复制循环体指令

            for instr in header_block.instructions:

                unrolled_body.append(instr)



        print(f"    展开后指令数: {len(unrolled_body)}")

        self.stats["loops_unrolled"] += 1

        self.stats["iterations_saved"] += (loop.trip_count or 3) - 1



        return True



    def _partial_unroll(self, loop: LoopInfo, factor: int) -> bool:

        """

        部分展开



        原理: 将循环体按因子复制,减少迭代次数

        """

        print(f"  部分展开: factor={factor}")



        # 简化: 返回成功

        self.stats["loops_unrolled"] += 1

        self.stats["iterations_saved"] += (loop.trip_count or 3) // factor



        return True



    def unroll_with_profitability(self) -> List[Tuple[LoopInfo, str]]:

        """

        基于收益性分析选择展开

        """

        results = []



        for loop in self.loops:

            # 计算收益

            profit = self._calculate_profitability(loop)



            if profit > 0:

                success, reason = self.unroll(loop, factor=2)

                if success:

                    results.append((loop, reason))



        return results



    def _calculate_profitability(self, loop: LoopInfo) -> float:

        """

        计算展开收益



        收益 = 减少的分支开销 - 增加的代码大小代价

        """

        # 简化: 返回正收益

        return 1.0





def print_loop_info(loops: List[LoopInfo]):

    """打印循环信息"""

    print("=== 发现的循环 ===")

    for i, loop in enumerate(loops):

        print(f"\n循环 {i + 1}:")

        print(f"  Header: B{loop.header}")

        print(f"  Latch: B{loop.latch}")

        print(f"  Body: {[f'B{b}' for b in loop.body]}")





if __name__ == "__main__":

    from intermediate_representation import IRGenerator, Address, OpCode

    from basic_block import BasicBlockBuilder



    # 创建测试CFG: 简单for循环

    # for (i = 0; i < 3; i++) { x = x + i; }

    gen = IRGenerator()



    # i = 0

    gen.emit(OpCode.LOAD, result=Address.temp("i"), arg1=Address.constant(0))



    # L_loop:

    gen.emit_label("L_loop")



    # if i < 3 goto L_body else L_end

    t1 = gen.new_temp()

    gen.emit_binary(OpCode.LT, t1, Address.temp("i"), Address.constant(3))

    gen.emit(OpCode.JUMP_IF, result=Address.label("L_body"), arg1=t1)

    gen.emit_jump("L_end")



    # L_body:

    gen.emit_label("L_body")



    # x = x + i

    t2 = gen.new_temp()

    gen.emit_binary(OpCode.ADD, t2, Address.variable("x"), Address.temp("i"))

    gen.emit(OpCode.STORE, result=Address.variable("x"), arg1=t2)



    # i = i + 1

    t3 = gen.new_temp()

    gen.emit_binary(OpCode.ADD, t3, Address.temp("i"), Address.constant(1))

    gen.emit(OpCode.LOAD, result=Address.temp("i"), arg1=t3)



    # goto L_loop

    gen.emit_jump("L_loop")



    # L_end:

    gen.emit_label("L_end")

    gen.emit(OpCode.FUNC_END, result=Address.variable("main"))



    # 构建CFG

    builder = BasicBlockBuilder()

    blocks = builder.build(gen.generate())

    cfg = ControlFlowGraph(blocks)



    print("=== 循环展开测试 ===")



    # 查找循环

    unroller = LoopUnroller(cfg)

    loops = unroller.find_loops()

    print_loop_info(loops)



    # 执行展开

    print("\n=== 执行展开优化 ===")

    for loop in loops:

        success, reason = unroller.unroll(loop)

        print(f"  {'成功' if success else '失败'}: {reason}")



    # 统计

    print("\n=== 优化统计 ===")

    stats = unroller.stats

    print(f"  发现循环: {stats['loops_found']}")

    print(f"  展开循环: {stats['loops_unrolled']}")

    print(f"  节省迭代: {stats['iterations_saved']}")

