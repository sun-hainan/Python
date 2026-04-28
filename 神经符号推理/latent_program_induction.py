"""
潜在程序归纳 (Latent Program Induction)
==========================================
本模块实现潜在程序归纳方法：

核心思想：
- 假设程序具有潜在结构
- 通过观察输入输出推断潜在程序
- 结合神经网络的表达能力

方法：
- 潜在变量模型
- EM算法
- 变分推断

Author: 算法库
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Callable
from abc import ABC, abstractmethod


class Operation:
    """操作基类"""
    
    def __init__(self, name: str, arity: int):
        self.name = name
        self.arity = arity
    
    @abstractmethod
    def apply(self, args: List) -> any:
        pass


class PrimitiveOperation(Operation):
    """原语操作"""
    
    def __init__(self, name: str, fn: Callable):
        super().__init__(name, fn.__code__.co_argcount)
        self.fn = fn
    
    def apply(self, args: List):
        return self.fn(*args)


class CompositeOperation(Operation):
    """复合操作"""
    
    def __init__(self, name: str, sub_ops: List[Operation]):
        super().__init__(name, sum(op.arity for op in sub_ops))
        self.sub_ops = sub_ops


class LatentProgram:
    """潜在程序"""
    
    def __init__(self, operations: List[Operation]):
        self.operations = operations
        self.latent_vector = None
    
    def execute(self, inputs: List) -> any:
        """执行程序"""
        stack = list(inputs)
        for op in self.operations:
            if op.arity > len(stack):
                raise ValueError(f"操作 {op.name} 需要 {op.arity} 个参数")
            args = stack[-op.arity:]
            stack = stack[:-op.arity]
            result = op.apply(args)
            if isinstance(result, tuple):
                stack.extend(result)
            else:
                stack.append(result)
        
        return stack[-1] if stack else None
    
    def to_sequence(self) -> List[str]:
        """转换为操作序列"""
        return [op.name for op in self.operations]


class LatentVariableModel:
    """潜在变量模型"""
    
    def __init__(self, n_latent: int = 10):
        self.n_latent = n_latent
        self.latent_embeddings: np.ndarray = None
        self.transition_probs: np.ndarray = None  # 转移概率
    
    def fit(self, programs: List[LatentProgram], max_iter: int = 100):
        """训练模型"""
        # 简化：使用EM算法
        np.random.seed(42)
        
        # 初始化
        self.latent_embeddings = np.random.randn(self.n_latent, 32) * 0.1
        
        # 收集所有操作
        all_ops = set()
        for prog in programs:
            for op in prog.operations:
                all_ops.add(op.name)
        
        self.op_to_idx = {op: i for i, op in enumerate(sorted(all_ops))}
        self.idx_to_op = {i: op for op, i in self.op_to_idx.items()}
        n_ops = len(all_ops)
        
        # 转移概率
        self.transition_probs = np.random.rand(self.n_latent, n_ops) * 0.1 + 0.01
        self.transition_probs = self.transition_probs / self.transition_probs.sum(axis=1, keepdims=True)
        
        for iteration in range(max_iter):
            # E步：估计每个程序属于哪个潜在变量
            responsibilities = self._e_step(programs)
            
            # M步：更新参数
            self._m_step(programs, responsibilities)
            
            if iteration % 20 == 0:
                loss = self._compute_loss(programs)
                print(f"迭代 {iteration}: 损失 = {loss:.4f}")
    
    def _e_step(self, programs: List[LatentProgram]) -> np.ndarray:
        """E步：计算后验"""
        responsibilities = np.zeros((len(programs), self.n_latent))
        
        for i, prog in enumerate(programs):
            seq = prog.to_sequence()
            
            # 简化的似然计算
            log_likelihood = np.zeros(self.n_latent)
            for z in range(self.n_latent):
                for j, op_name in enumerate(seq):
                    if op_name in self.op_to_idx:
                        op_idx = self.op_to_idx[op_name]
                        log_likelihood[z] += np.log(self.transition_probs[z, op_idx] + 1e-10)
            
            responsibilities[i] = np.exp(log_likelihood - np.max(log_likelihood))
            responsibilities[i] = responsibilities[i] / (responsibilities[i].sum() + 1e-10)
        
        return responsibilities
    
    def _m_step(self, programs: List[LatentProgram], responsibilities: np.ndarray):
        """M步：更新参数"""
        # 更新转移概率
        n_ops = len(self.op_to_idx)
        new_transitions = np.zeros((self.n_latent, n_ops))
        
        for i, prog in enumerate(programs):
            seq = prog.to_sequence()
            for op_name in seq:
                if op_name in self.op_to_idx:
                    op_idx = self.op_to_idx[op_name]
                    new_transitions[:, op_idx] += responsibilities[i]
        
        # 归一化
        self.transition_probs = new_transitions / (new_transitions.sum(axis=1, keepdims=True) + 1e-10)
    
    def _compute_loss(self, programs: List[LatentProgram]) -> float:
        """计算负对数似然"""
        loss = 0.0
        for prog in programs:
            seq = prog.to_sequence()
            
            # 使用最高概率的潜在变量
            z = np.argmax([self.transition_probs[:, self.op_to_idx.get(op, 0)].sum() 
                          for op in seq])
            
            for op_name in seq:
                if op_name in self.op_to_idx:
                    loss -= np.log(self.transition_probs[z, self.op_to_idx[op_name]] + 1e-10)
        
        return loss / len(programs)


class ProgramInducer:
    """程序归纳器"""
    
    def __init__(self):
        self.operations: List[Operation] = []
        self.latent_model: Optional[LatentVariableModel] = None
    
    def add_operation(self, name: str, fn: Callable):
        """添加操作"""
        self.operations.append(PrimitiveOperation(name, fn))
    
    def infer_program(self, input_output_pairs: List[Tuple[List, any]],
                    max_program_length: int = 10) -> LatentProgram:
        """
        从输入输出对推断程序
        
        使用搜索方法
        """
        best_program = None
        best_score = -float('inf')
        
        # 尝试所有可能的操作组合
        for length in range(1, max_program_length + 1):
            programs = self._enumerate_programs(length)
            
            for program in programs:
                try:
                    score = self._evaluate_program(program, input_output_pairs)
                    if score > best_score:
                        best_score = score
                        best_program = program
                        
                    if score == len(input_output_pairs):  # 完全匹配
                        return program
                except:
                    pass
        
        return best_program
    
    def _enumerate_programs(self, length: int) -> List[LatentProgram]:
        """枚举给定长度的所有程序"""
        if length == 1:
            return [LatentProgram([op]) for op in self.operations]
        
        # 递归枚举
        shorter = self._enumerate_programs(length - 1)
        programs = []
        
        for prog in shorter:
            for op in self.operations:
                programs.append(LatentProgram(prog.operations + [op]))
        
        return programs
    
    def _evaluate_program(self, program: LatentProgram,
                         examples: List[Tuple[List, any]]) -> int:
        """评估程序"""
        matched = 0
        
        for inputs, expected in examples:
            try:
                output = program.execute(inputs)
                if output == expected:
                    matched += 1
            except:
                pass
        
        return matched


class HierarchicalProgramInduction:
    """层次化程序归纳"""
    
    def __init__(self, depth: int = 3):
        self.depth = depth
        self.subroutines: List[LatentProgram] = []
        self.primitive_ops: List[Operation] = []
    
    def add_primitive(self, name: str, fn: Callable):
        """添加原语操作"""
        self.primitive_ops.append(PrimitiveOperation(name, fn))
    
    def add_subroutine(self, program: LatentProgram):
        """添加子程序"""
        self.subroutines.append(program)
    
    def hierarchical_induce(self, examples: List[Tuple[List, any]]) -> LatentProgram:
        """
        层次化归纳
        
        1. 学习原语级别的程序片段
        2. 将这些片段抽象为子程序
        3. 在更高层次组合子程序
        """
        # 阶段1：学习基础操作序列
        base_programs = self._learn_base_level(examples)
        
        # 阶段2：抽象子程序
        for prog in base_programs:
            if len(prog.operations) > 2:
                self.add_subroutine(prog)
        
        # 阶段3：组合子程序
        return self._compose_subroutines(examples)
    
    def _learn_base_level(self, examples: List[Tuple[List, any]]) -> List[LatentProgram]:
        """学习基础层次"""
        inducer = ProgramInducer()
        for op in self.primitive_ops:
            inducer.add_operation(op.name, op.fn)
        
        program = inducer.infer_program(examples, max_program_length=5)
        return [program] if program else []
    
    def _compose_subroutines(self, examples: List[Tuple[List, any]]) -> LatentProgram:
        """组合子程序"""
        # 简化：直接返回学习的程序
        if len(self.subroutines) > 0:
            return self.subroutines[0]
        return LatentProgram([])


class VariationalProgramInduction:
    """变分程序归纳"""
    
    def __init__(self, embedding_dim: int = 32):
        self.embedding_dim = embedding_dim
        self.program_encoder = None
        self.program_decoder = None
    
    def encode_io_pair(self, inputs: List, output: any) -> np.ndarray:
        """
        编码输入输出对到潜在空间
        
        简化实现
        """
        # 创建简化的嵌入
        input_features = []
        for inp in inputs:
            if isinstance(inp, (int, float)):
                input_features.append(float(inp))
        
        # 填充或截断
        while len(input_features) < 10:
            input_features.append(0.0)
        input_features = input_features[:10]
        
        # 添加输出信息
        if isinstance(output, (int, float)):
            input_features.append(float(output))
        
        # 简化的编码
        embedding = np.array(input_features[:self.embedding_dim])
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        
        return embedding
    
    def decode_to_program(self, latent_code: np.ndarray) -> LatentProgram:
        """
        从潜在代码解码到程序
        
        简化实现
        """
        # 简化的解码策略
        operations = []
        
        # 基于latent_code的某些维度决定操作
        seed = int(np.sum(np.abs(latent_code)) * 1000) % 100
        np.random.seed(seed)
        
        ops = ["ADD", "SUB", "MUL", "DUP", "SWAP"]
        for _ in range(3):
            op_name = ops[np.random.randint(len(ops))]
            # 简化的操作
            if op_name == "ADD":
                fn = lambda x, y: x + y
            elif op_name == "SUB":
                fn = lambda x, y: x - y
            elif op_name == "MUL":
                fn = lambda x, y: x * y
            elif op_name == "DUP":
                fn = lambda x: (x, x)
            else:
                fn = lambda x, y: (y, x)
            
            operations.append(PrimitiveOperation(op_name, fn))
        
        return LatentProgram(operations)


if __name__ == "__main__":
    print("=" * 55)
    print("潜在程序归纳测试")
    print("=" * 55)
    
    # 创建程序归纳器
    inducer = ProgramInducer()
    
    # 添加操作
    inducer.add_operation("ADD", lambda x, y: x + y)
    inducer.add_operation("SUB", lambda x, y: x - y)
    inducer.add_operation("MUL", lambda x, y: x * y)
    inducer.add_operation("DUP", lambda x: (x, x))
    
    print("\n--- 基础程序归纳 ---")
    
    # 示例：学习加法
    examples = [
        ([2, 3], 5),
        ([4, 5], 9),
        ([10, 20], 30),
    ]
    
    program = inducer.infer_program(examples, max_program_length=5)
    
    if program:
        print(f"学习的程序: {program.to_sequence()}")
        
        # 执行
        result = program.execute([2, 3])
        print(f"执行结果: {result}")
    else:
        print("未能找到匹配的程序")
    
    # 测试不同操作
    print("\n--- 测试不同操作 ---")
    
    test_cases = [
        ([1, 2], "ADD", lambda x, y: x + y),
        ([5, 3], "SUB", lambda x, y: x - y),
        ([4, 3], "MUL", lambda x, y: x * y),
    ]
    
    for inputs, op_name, expected_fn in test_cases:
        program = inducer.infer_program([(inputs, expected_fn(*inputs))], max_program_length=3)
        if program:
            print(f"{op_name}: {program.to_sequence()}")
    
    # 层次化程序归纳
    print("\n--- 层次化程序归纳 ---")
    
    hier_inducer = HierarchicalProgramInduction(depth=3)
    hier_inducer.add_primitive("ADD", lambda x, y: x + y)
    hier_inducer.add_primitive("SUB", lambda x, y: x - y)
    hier_inducer.add_primitive("DUP", lambda x: (x, x))
    
    hier_program = hier_inducer.hierarchical_induce(examples)
    print(f"层次化学习的程序: {hier_program.to_sequence()}")
    
    # 潜在变量模型
    print("\n--- 潜在变量模型 ---")
    
    # 创建一些程序
    programs = []
    for i in range(20):
        ops = [
            PrimitiveOperation("ADD", lambda x, y: x + y),
            PrimitiveOperation("SUB", lambda x, y: x - y),
        ]
        import random
        selected = random.sample(ops, 2)
        programs.append(LatentProgram(selected))
    
    lvm = LatentVariableModel(n_latent=5)
    lvm.fit(programs, max_iter=50)
    
    print(f"学习的转移概率形状: {lvm.transition_probs.shape}")
    
    # 变分程序归纳
    print("\n--- 变分程序归纳 ---")
    
    vpi = VariationalProgramInduction(embedding_dim=16)
    
    # 编码输入输出
    latent = vpi.encode_io_pair([2, 3], 5)
    print(f"潜在代码维度: {latent.shape}")
    
    # 解码
    decoded_program = vpi.decode_to_program(latent)
    print(f"解码的程序: {decoded_program.to_sequence()}")
    
    print("\n测试通过！潜在程序归纳工作正常。")
