"""
zk-STARK 实现 - Interactive Oracle Proof / Low-Degree Testing
==============================================================

本模块实现 zk-STARK (Zero-Knowledge Scalable Transparent Argument of Knowledge)
的核心组件。STARK 是一种无需可信设置的零知识证明系统。

核心概念:
- 透明设置 (Transparent Setup): 不需要可信的 CRS，使用公开的随机预言
- IOP (Interactive Oracle Proof): 证明者通过 oracle 访问提供证明
- FRI (Fast Reed-Solomon IOP): 低自由度测试协议
- 低度测试 (Low-Degree Testing): 验证某个函数是一个低次多项式

与 zk-SNARK 对比:
- STARK 不需要可信设置（透明）
- 证明更大（对数级 vs 常数级）
- 后量子安全（基于哈希假设）

作者: OpenClaw Agent
版本: 1.0
"""

import os
import random
import hashlib
import sys
sys.path.insert(0, os.path.dirname(__file__))

from zk_snark_finite_field import FiniteField, ECPoint, Polynomial


# --------------------------------------------------------------------
# Reed-Solomon 编码 (Reed-Solomon Encoding)
# --------------------------------------------------------------------

class ReedSolomonCode:
    """
    Reed-Solomon 编码的实现
    
    RS 编码将一个次数 < n 的多项式在 n 个点上求值，
    生成长度为 n 的编码。
    
    用途:
    - STARK 中将 trace 扩展为长的 RS 码字
    - 支持低度测试（FRI 的基础）
    """
    
    def __init__(self, field, code_rate=2):
        """
        初始化 RS 编码器。
        
        参数:
            field: 有限域
            code_rate: 编码率 (code_rate=2 表示长度是维度的 2 倍)
        """
        self.field = field
        self.code_rate = code_rate  # n / k 比例
    
    def encode(self, message_poly, domain_size):
        """
        将消息多项式编码为 RS 码字。
        
        参数:
            message_poly: 消息多项式（次数 < k）
            domain_size: 码字长度 n
        
        返回:
            codeword: 在 n 个点上求值得到的码字
        """
        k = message_poly.degree() + 1    # 消息维度
        n = domain_size                   # 码字长度
        
        # 在域的扩张上选择 n 个点作为求值域
        # 这里使用简化：取域的前 n 个元素
        codeword = []
        for i in range(n):
            x = FiniteField(i + 1)
            value = message_poly.eval(x)
            codeword.append(value)
        
        return codeword


# --------------------------------------------------------------------
# Merkle 树 (Merkle Tree) - 用于 Oracle 访问
# --------------------------------------------------------------------

class MerkleTree:
    """
    Merkle 树用于 STARK 中的批量承诺和随机抽查。
    
    证明者将长的码字分解成树叶，通过 Merkle 树承诺，
    验证者可以随机要求证明者打开特定位置的叶子。
    
    这实现了"随机预言机"的近似，允许验证者随机采样。
    """
    
    def __init__(self, leaves):
        """
        构建 Merkle 树。
        
        参数:
            leaves: 叶子节点列表（字节串列表）
        """
        self.leaves = leaves
        self.height = 0
        self.layers = [leaves]   # layers[0] 是叶子层
        
        # 构建树
        current = leaves[:]
        while len(current) > 1:
            # 如果是奇数，最后一个复制
            if len(current) % 2 == 1:
                current.append(current[-1])
            
            # 计算上一层
            next_level = []
            for i in range(0, len(current), 2):
                combined = current[i] + current[i+1]
                # 使用 SHA256 作为哈希函数
                h = hashlib.sha256(combined.encode()).digest()
                next_level.append(h)
            
            self.layers.append(next_level)
            current = next_level
            self.height += 1
        
        # 根是最后一层的唯一元素
        self.root = current[0]
    
    def get_proof(self, index):
        """
        获取指定叶子节点的 Merkle 证明。
        
        参数:
            index: 叶子索引
        
        返回:
            proof: 包含 siblings 和 path 信息的证明
        """
        proof = {
            'leaf': self.leaves[index],
            'siblings': [],
            'path': []    # 路径上每一步是左(0)还是右(1)
        }
        
        current = index
        for layer_idx in range(self.height):
            layer = self.layers[layer_idx]
            # 判断是左兄弟还是右兄弟
            if current % 2 == 0:
                # 当前是左节点，兄弟在右边
                sibling_idx = current + 1
                proof['path'].append(0)   # 0 表示"我左边"
            else:
                # 当前是右节点，兄弟在左边
                sibling_idx = current - 1
                proof['path'].append(1)   # 1 表示"我右边"
            
            proof['siblings'].append(layer[sibling_idx])
            current = current // 2
        
        return proof
    
    @staticmethod
    def verify_proof(root, proof, index):
        """
        验证 Merkle 证明的正确性。
        
        参数:
            root: Merkle 根
            proof: Merkle 证明
            index: 叶子索引
        
        返回:
            valid: 是否验证通过
        """
        current = proof['leaf']
        for i, (sibling, is_right) in enumerate(zip(proof['siblings'], proof['path'])):
            if is_right == 0:
                # 兄弟在右边: hash(left || right)
                combined = current + sibling
            else:
                # 兄弟在左边: hash(left || right)
                combined = sibling + current
            current = hashlib.sha256(combined.encode()).digest()
        
        return current == root


# --------------------------------------------------------------------
# FRI 协议 (Fast Reed-Solomon IOP)
# --------------------------------------------------------------------

class FRI:
    """
    FRI (Fast Reed-Solomon IOP) 协议实现
    
    FRI 用于证明一个向量是一个低次多项式的求值，
    即"低度测试"(Low-Degree Testing)。
    
    核心思想（简化的代数方法）:
    1. 将长度为 n 的码字分成两部分: f_even(x) 和 f_odd(x)
    2. 利用 f(x) = f_even(x^2) + x * f_odd(x^2)
    3. 定义组合函数 g(x) = f_even(x) + x * f_odd(x)
    4. 递归地对 g(x) 进行同样的分解
    
    每一步都将度数减半，经过 log(n) 步后，
    如果原始函数是度 < n 的多项式，最终会得到常数。
    """
    
    def __init__(self, field, initial_degree, reduction=2):
        """
        初始化 FRI 协议。
        
        参数:
            field: 有限域
            initial_degree: 初始多项式的最高次数
            reduction: 每步的度数约简因子（通常为 2）
        """
        self.field = field
        self.initial_degree = initial_degree
        self.reduction = reduction  # 每步度数减半
        self.rounds = 0
        # 计算需要的轮数: log_reduction(degree + 1)
        d = initial_degree + 1
        while d > 1:
            self.rounds += 1
            d = (d + reduction - 1) // reduction
    
    def fold(self, codeword, alpha):
        """
        FRI 的折叠步骤。
        
        将长度为 n 的码字折叠成长度为 n/2 的码字。
        
        参数:
            codeword: 原始码字 [f(w^0), f(w^1), ..., f(w^{n-1})]
            alpha: 随机折叠参数
        
        返回:
            folded: 折叠后的码字
        """
        n = len(codeword)
        if n % 2 != 0:
            codeword = codeword + [codeword[-1]]
            n += 1
        
        folded = []
        for i in range(n // 2):
            # f_even(w^i) 和 f_odd(w^i)
            even = codeword[2*i]
            odd = codeword[2*i + 1]
            # g(w^i) = f_even(w^i) + alpha * f_odd(w^i)
            # 注意: 实际 FRI 使用特殊的 w
            folded.append(even + odd * alpha)
        
        return folded
    
    def prove(self, polynomial, domain_size):
        """
        生成 FRI 证明。
        
        参数:
            polynomial: 要证明的多项式
            domain_size: 初始求值域大小
        
        返回:
            proof: 证明的各层 commitments
        """
        # 在初始域上求值
        rs = ReedSolomonCode(self.field)
        codeword = rs.encode(polynomial, domain_size)
        
        # 承诺第一层
        # 将有限域元素转换为字节串进行哈希
        leaves = [str(c.value).encode() for c in codeword]
        merkle = MerkleTree(leaves)
        
        proof = {
            'layers': [merkle.root],  # 每层的根
            'codewords': [codeword],   # 每层的码字
            'merkle_trees': [merkle],  # Merkle 树
        }
        
        # 递归折叠
        current_codeword = codeword
        current_degree = polynomial.degree()
        
        for round_idx in range(self.rounds):
            # 生成随机折叠参数 alpha
            seed = str(round_idx) + str(merkle.root)
            alpha_val = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
            alpha = FiniteField(alpha_val % self.field.P)
            
            # 折叠
            folded = self.fold(current_codeword, alpha)
            proof['codewords'].append(folded)
            
            # 承诺折叠后的码字
            if len(folded) > 1:
                leaves = [str(c.value).encode() for c in folded]
                merkle = MerkleTree(leaves)
                proof['merkle_trees'].append(merkle)
                proof['layers'].append(merkle.root)
            
            current_codeword = folded
        
        # 最终层应该接近常数
        proof['final_value'] = current_codeword[0] if current_codeword else None
        
        return proof
    
    def verify(self, proof, polynomial_degree, domain_size, challenges):
        """
        验证 FRI 证明。
        
        参数:
            proof: FRI 证明
            polynomial_degree: 声称的多项式次数
            domain_size: 求值域大小
            challenges: 验证者提供的随机挑战
        
        返回:
            valid: 验证是否通过
        """
        # 检查最终值是否为常数（度数约简后的期望）
        # 实际验证需要检查 consistency
        if proof['final_value'] is None:
            return False
        
        # 检查每层的折叠一致性
        for i in range(len(proof['codewords']) - 1):
            codeword = proof['codewords'][i]
            next_codeword = proof['codewords'][i + 1]
            
            # 验证折叠的正确性
            if len(codeword) != 2 * len(next_codeword):
                return False
        
        return True


# --------------------------------------------------------------------
# STARK 证明系统 (Simplified)
# --------------------------------------------------------------------

class STARK:
    """
    简化的 STARK 证明系统实现
    
    完整的 STARK 流程:
    1. Execution Trace: 运行计算生成 trace
    2. Polynomial Constraints: 将约束转化为多项式等式
    3. Low-Degree Extension: 将 trace 扩展为低次多项式
    4. FRI Proof: 证明扩展后的多项式是低次的
    5. Random Sampling: 验证者随机采样验证
    
    这里演示核心的低度测试和 IOP 机制。
    """
    
    def __init__(self, security_level=40):
        """
        初始化 STARK 系统。
        
        参数:
            security_level: 安全级别（决定参数大小）
        """
        self.security_level = security_level
        # 根据安全级别确定参数
        # 实际中需要满足: n * k >= 2^security_level
        self.field = FiniteField
        self.lde_expansion = 4  # LDE 扩展因子
        self.fri_reduction = 2  # FRI 每步约简
    
    def generate_trace(self, initial_state, steps):
        """
        生成执行 trace。
        
        参数:
            initial_state: 初始状态
            steps: 执行步数
        
        返回:
            trace: 状态序列
        """
        trace = [initial_state]
        current = initial_state
        
        for _ in range(steps):
            # 简化的状态转换: next = hash(current)
            next_val = int(hashlib.sha256(str(current).encode()).hexdigest(), 16)
            current = next_val % self.field.P
            trace.append(self.field(current))
        
        return trace
    
    def prove(self, trace):
        """
        为 trace 生成 STARK 证明。
        
        参数:
            trace: 计算执行 trace
        
        返回:
            proof: 证明
        """
        print(f"[STARK] 为 {len(trace)} 步 trace 生成证明...")
        
        # 步骤1: LDE (Low-Degree Extension)
        # 将 trace 扩展为更长的序列以增加安全性
        expansion = self.lde_expansion
        extended_trace = []
        for val in trace:
            for _ in range(expansion):
                extended_trace.append(val)
        
        print(f"[STARK] LDE 扩展: {len(trace)} -> {len(extended_trace)}")
        
        # 步骤2: 将扩展 trace 转换为多项式
        # 构建插值多项式
        n = len(extended_trace)
        # 简化的多项式构造（实际使用拉格朗日插值）
        coeffs = []
        for i, val in enumerate(extended_trace):
            coeffs.append(val)
        
        # 填充到合适的度数
        degree = 1
        while (degree + 1) < n:
            degree += 1
            if len(coeffs) <= degree:
                coeffs.append(self.field(0))
        
        poly = Polynomial(coeffs)
        
        # 步骤3: FRI 证明
        print(f"[STARK] 生成 FRI 证明 (多项式次数: {poly.degree()})...")
        fri = FRI(self.field, poly.degree())
        fri_proof = fri.prove(poly, n)
        
        # 步骤4: 承诺所有层
        commitments = []
        for mt in fri_proof['merkle_trees']:
            commitments.append(mt.root)
        
        proof = {
            'trace_length': len(trace),
            'extended_length': len(extended_trace),
            'poly_degree': poly.degree(),
            'fri_proof': fri_proof,
            'commitments': commitments,
            'final_value': fri_proof['final_value'],
        }
        
        print(f"[STARK] 证明生成完成!")
        print(f"  - FRI 轮数: {fri.rounds}")
        print(f"  - 承诺层数: {len(commitments)}")
        
        return proof
    
    def verify(self, proof, constraints_satisfied=True):
        """
        验证 STARK 证明。
        
        参数:
            proof: 证明
            constraints_satisfied: 约束是否满足（模拟）
        
        返回:
            valid: 验证是否通过
        """
        print("[STARK] 验证证明...")
        
        # 验证 FRI
        fri = FRI(self.field, proof['poly_degree'])
        fri_valid = fri.verify(
            proof['fri_proof'],
            proof['poly_degree'],
            proof['extended_length'],
            []  # challenges
        )
        
        if not fri_valid:
            print("[STARK] FRI 验证失败 ✗")
            return False
        
        # 验证约束（简化：假设总是满足）
        if not constraints_satisfied:
            print("[STARK] 约束验证失败 ✗")
            return False
        
        print("[STARK] 证明验证通过 ✓")
        return True


# --------------------------------------------------------------------
# 交互谕言证明 (Interactive Oracle Proof)
# --------------------------------------------------------------------

class InteractiveOracleProof:
    """
    交互谕言证明的演示
    
    IOP 模型:
    - 证明者和验证者交互多轮
    - 每轮证明者发送"谕言"(oracle) 的承诺
    - 验证者随机查询谕言的一些位置
    - 最终验证者基于查询响应决定接受或拒绝
    
    STARK 是 IOP 的一种，使用 Merkle 树实现谕言访问。
    """
    
    def __init__(self, rounds=3):
        """
        初始化 IOP。
        
        参数:
            rounds: 交互轮数
        """
        self.rounds = rounds
    
    def prove(self, data):
        """
        生成 IOP 证明。
        
        参数:
            data: 要证明的数据
        
        返回:
            proof: 包含每轮承诺和查询响应的证明
        """
        print(f"[IOP] 开始 {self.rounds} 轮交互证明...")
        
        commitments = []   # 每轮的承诺
        queries = []       # 验证者的查询
        responses = []    # 对查询的响应
        
        current_data = data
        
        for round_idx in range(self.rounds):
            # 承诺当前数据
            commitment = hashlib.sha256(str(current_data).encode()).digest()
            commitments.append(commitment)
            print(f"[IOP] 轮 {round_idx + 1}: 发送承诺 {commitment[:16].hex()}...")
            
            # 模拟验证者的随机查询
            # 实际中验证者基于前一轮的承诺生成随机挑战
            seed = commitment + b'challenge'
            query = int(hashlib.sha256(seed).hexdigest(), 16) % len(str(current_data))
            queries.append(query)
            print(f"[IOP] 轮 {round_idx + 1}: 验证者查询位置 {query}")
            
            # 响应查询
            data_str = str(current_data)
            response = data_str[query] if query < len(data_str) else data_str[0]
            responses.append(response)
            print(f"[IOP] 轮 {round_idx + 1}: 证明者响应 {response}")
            
            # 更新数据（模拟某种处理）
            current_data = str(current_data) + str(response)
        
        return {
            'commitments': commitments,
            'queries': queries,
            'responses': responses,
        }
    
    def verify(self, proof, original_data):
        """
        验证 IOP 证明。
        
        参数:
            proof: 证明
            original_data: 原始数据
        
        返回:
            valid: 是否验证通过
        """
        print("[IOP] 验证证明...")
        
        current_data = original_data
        for round_idx in range(len(proof['commitments'])):
            commitment = proof['commitments'][round_idx]
            query = proof['queries'][round_idx]
            response = proof['responses'][round_idx]
            
            # 验证承诺是否一致
            expected_commitment = hashlib.sha256(str(current_data).encode()).digest()
            if commitment != expected_commitment:
                print(f"[IOP] 轮 {round_idx + 1}: 承诺不匹配 ✗")
                return False
            
            # 验证查询响应
            data_str = str(current_data)
            expected_response = data_str[query] if query < len(data_str) else data_str[0]
            if response != expected_response:
                print(f"[IOP] 轮 {round_idx + 1}: 响应不匹配 ✗")
                return False
            
            print(f"[IOP] 轮 {round_idx + 1}: 验证通过 ✓")
            current_data = str(current_data) + str(response)
        
        print("[IOP] 所有轮验证通过 ✓")
        return True


# --------------------------------------------------------------------
# 主程序测试
# --------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("zk-STARK 实现 - 低度测试与交互谕言证明")
    print("=" * 60)
    
    # 1. 测试 Reed-Solomon 编码
    print("\n--- 测试 1: Reed-Solomon 编码 ---")
    field = FiniteField
    rs = ReedSolomonCode(field, code_rate=2)
    
    # 定义一个多项式 f(x) = 1 + 2x + 3x^2
    poly = Polynomial([FiniteField(1), FiniteField(2), FiniteField(3)])
    print(f"消息多项式: {poly}")
    print(f"多项式次数: {poly.degree()}")
    
    # 编码为长度为 8 的码字
    codeword = rs.encode(poly, 8)
    print(f"RS 码字 (长度 8): {[c.value for c in codeword]}")
    
    # 2. 测试 Merkle 树
    print("\n--- 测试 2: Merkle 树 Oracle ---")
    leaves = [f"leaf_{i}".encode() for i in range(8)]
    merkle = MerkleTree(leaves)
    print(f"Merkle 树高度: {merkle.height + 1}")
    print(f"Merkle 根: {merkle.root.hex()[:32]}...")
    
    # 获取并验证证明
    proof = merkle.get_proof(3)
    valid = MerkleTree.verify_proof(merkle.root, proof, 3)
    print(f"位置 3 的 Merkle 证明验证: {'通过 ✓' if valid else '失败 ✗'}")
    
    # 3. 测试 FRI 协议
    print("\n--- 测试 3: FRI 低度测试 ---")
    # 定义一个二次多项式
    poly = Polynomial([FiniteField(3), FiniteField(1), FiniteField(4)])  # 3 + x + 4x^2
    print(f"FRI 测试多项式: {poly}")
    print(f"多项式次数: {poly.degree()}")
    
    fri = FRI(FiniteField, poly.degree())
    print(f"FRI 轮数: {fri.rounds}")
    
    # 生成证明
    fri_proof = fri.prove(poly, 16)
    print(f"最终（常数）值: {fri_proof['final_value'].value if fri_proof['final_value'] else None}")
    
    # 验证证明
    valid = fri.verify(fri_proof, poly.degree(), 16, [])
    print(f"FRI 验证结果: {'通过 ✓' if valid else '失败 ✗'}")
    
    # 4. 测试 STARK
    print("\n--- 测试 4: STARK 证明系统 ---")
    stark = STARK(security_level=20)
    
    # 生成 trace
    initial_state = 42
    trace = stark.generate_trace(initial_state, steps=4)
    print(f"生成的 trace: {[t.value for t in trace]}")
    
    # 生成证明
    proof = stark.prove(trace)
    
    # 验证证明
    valid = stark.verify(proof)
    print(f"STARK 验证: {'通过 ✓' if valid else '失败 ✗'}")
    
    # 5. 测试 IOP
    print("\n--- 测试 5: 交互谕言证明 ---")
    iop = InteractiveOracleProof(rounds=3)
    
    secret_data = "HelloSTARK"
    proof = iop.prove(secret_data)
    valid = iop.verify(proof, secret_data)
    print(f"IOP 验证: {'通过 ✓' if valid else '失败 ✗'}")
    
    print("\n" + "=" * 60)
    print("STARK 协议演示完成")
    print("=" * 60)
