"""
Σ协议族模块 / Sigma Protocol Family

本模块实现Σ协议族的各种变体，包括：
- 基本Σ协议 (Basic Sigma Protocol)
- OR证明 (OR Proof / Disjunction Proof)
- 承诺方案 (Commitment Schemes)

Σ协议是一种特殊的三步交互式证明协议：
Prover -> Verifier: 承诺 (commitment)
Verifier -> Prover: 挑战 (challenge)  
Prover -> Verifier: 响应 (response)

特点：验证者使用随机挑战，证明者据此计算响应。

作者: AI Assistant
版本: 1.0
"""

import hashlib
import secrets
import random


# ============================================================
# 第一部分：基础有限域与群
# ============================================================

class SimpleField:
    """
    简化有限域类 / Simple Finite Field Class
    
    实现模素数p的有限域，用于Σ协议中的数学运算。
    """
    
    def __init__(self, prime):
        """
        初始化有限域 / Initialize finite field
        
        参数:
            prime (int): 素数模数
        """
        self.prime = prime
    
    def add(self, a, b):
        """加法 / Addition"""
        return (a + b) % self.prime
    
    def sub(self, a, b):
        """减法 / Subtraction"""
        return (a - b) % self.prime
    
    def mul(self, a, b):
        """乘法 / Multiplication"""
        return (a * b) % self.prime
    
    def pow(self, base, exp):
        """幂运算 / Exponentiation"""
        result = 1
        base = base % self.prime
        while exp > 0:
            if exp & 1:
                result = self.mul(result, base)
            base = self.mul(base, base)
            exp >>= 1
        return result
    
    def inv(self, a):
        """模逆元 / Modular inverse"""
        # 扩展欧几里得算法
        # 求解: a * x ≡ 1 (mod p)
        # 即: gcd(a, p) = 1 = a*x + p*y
        if a % self.prime == 0:
            raise ValueError("逆元不存在")
        original_a = a
        a = a % self.prime
        t, new_t = 0, 1
        r, new_r = self.prime, a
        while new_r != 0:
            quotient = r // new_r
            t, new_t = new_t, t - quotient * new_t
            r, new_r = new_r, r - quotient * new_r
        if r != 1:
            raise ValueError(f"{original_a} 和 {self.prime} 不互素")
        return t % self.prime
    
    def div(self, a, b):
        """除法 / Division"""
        return self.mul(a, self.inv(b))


# ============================================================
# 第二部分：承诺方案
# ============================================================

class CommitmentScheme:
    """
    承诺方案类 / Commitment Scheme Class
    
    实现密码学承诺方案的两个基本性质：
    - 绑定性 (Binding)：承诺后不能改变原值
    - 隐藏性 (Hiding)：承诺隐藏了原值
    
    使用Pedersen承诺的简化版本：
    commit(x, r) = g^x * h^r mod p
    """
    
    def __init__(self, prime=2**256 - 2**224 + 2**192 + 2**96 - 1):
        """
        初始化承诺方案 / Initialize commitment scheme
        
        参数:
            prime (int): 有限域的素数模数
        
        选择两个生成元g和h，它们在群中独立。
        """
        self.field = SimpleField(prime)
        # 选择两个随机生成元
        # 实际应用中需要验证它们确实是生成元
        self.g = 2
        self.h = 3
    
    def commit(self, value, randomness=None):
        """
        生成承诺 / Generate commitment
        
        计算 commit(x, r) = g^x * h^r mod p
        
        参数:
            value (int): 被承诺的值x
            randomness (int, optional): 随机性r，如果为None则自动生成
        
        返回:
            tuple: (commitment, randomness) 承诺值和使用的随机性
        """
        # 生成随机随机性（盐值）
        # 使用足够长的随机数以确保安全性
        if randomness is None:
            randomness = secrets.randbits(256)
        # 计算承诺: g^value * h^randomness mod p
        commitment = self.field.mul(
            self.field.pow(self.g, value),  # g^value
            self.field.pow(self.h, randomness)  # h^randomness
        )
        return commitment, randomness
    
    def verify_commitment(self, commitment, value, randomness):
        """
        验证承诺 / Verify commitment
        
        检查承诺是否是正确的(value, randomness)对生成的。
        
        参数:
            commitment (int): 承诺值
            value (int): 声称的值
            randomness (int): 声称的随机性
        
        返回:
            bool: 如果承诺匹配返回True
        """
        expected = self.field.mul(
            self.field.pow(self.g, value),
            self.field.pow(self.h, randomness)
        )
        return commitment == expected


# ============================================================
# 第三部分：基本Σ协议
# ============================================================

class SigmaProtocol:
    """
    基本Σ协议类 / Basic Sigma Protocol Class
    
    实现针对离散对数关系的基本Σ协议。
    
    关系R的定义：
    R = {((G, g, h), (x, r)) | h = g^x 且 r = commit(x) }
    
    协议流程：
    1. P -> V: a = g^k（承诺）
    2. V -> P: c（随机挑战，c ∈ {0, 1}^t）
    3. P -> V: s = k + c*x（响应）
    4. V验证: g^s = a * h^c
    """
    
    def __init__(self, security_bits=256):
        """
        初始化Σ协议 / Initialize Sigma protocol
        
        参数:
            security_bits (int): 安全参数，控制挑战空间大小
        """
        self.security_bits = security_bits
        # 使用一个足够大的素数
        self.prime = 2**256 - 2**224 + 2**192 + 2**96 - 1
        self.field = SimpleField(self.prime)
        # 生成元
        self.g = 2
        # 私钥x和对应的公钥h = g^x
        self.secret_x = None
        self.public_h = None
    
    def setup(self, secret_x=None):
        """
        设置协议参数 / Setup protocol parameters
        
        参数:
            secret_x (int, optional): 私钥，如果为None则随机生成
        """
        if secret_x is None:
            secret_x = secrets.randbits(256)
        self.secret_x = secret_x
        self.public_h = self.field.pow(self.g, secret_x)
        return self.public_h
    
    def prover_commit(self):
        """
        证明者步骤1：生成承诺 / Prover step 1: Generate commitment
        
        证明者随机选择k，计算a = g^k
        
        返回:
            int: 承诺值a
        """
        # 随机选择见证k
        self.k = secrets.randbits(self.security_bits)
        # 计算承诺: a = g^k mod p
        self.a = self.field.pow(self.g, self.k)
        return self.a
    
    def verifier_challenge(self):
        """
        验证者步骤2：生成挑战 / Verifier step 2: Generate challenge
        
        验证者发送一个随机挑战。
        
        返回:
            int: 随机挑战值c
        """
        # 挑战空间大小为2^security_bits
        # 实际应用中可能使用更小的挑战空间
        self.challenge = secrets.randbits(self.security_bits)
        return self.challenge
    
    def prover_response(self):
        """
        证明者步骤3：生成响应 / Prover step 3: Generate response
        
        证明者计算响应: s = k + c*x
        
        返回:
            int: 响应值s
        
        异常:
            ValueError: 如果还没有执行承诺步骤
        """
        if not hasattr(self, 'k') or not hasattr(self, 'challenge'):
            raise ValueError("必须先执行承诺和接收挑战")
        # s = k + c * x (mod p-1)
        # 注意：离散对数的指数运算模p-1（群的阶）
        order = self.prime - 1
        s = (self.k + self.challenge * self.secret_x) % order
        return s
    
    def verifier_verify(self, a, c, s):
        """
        验证者步骤4：验证证明 / Verifier step 4: Verify proof
        
        验证等式: g^s = a * h^c
        
        参数:
            a (int): 承诺值
            c (int): 挑战值
            s (int): 响应值
        
        返回:
            bool: 如果验证通过返回True
        """
        # 计算左边: g^s mod p
        left = self.field.pow(self.g, s)
        # 计算右边: a * h^c mod p
        right = self.field.mul(a, self.field.pow(self.public_h, c))
        return left == right


# ============================================================
# 第四部分：OR证明
# ============================================================

class SigmaORProof:
    """
    Σ-OR证明类 / Sigma OR Proof Class
    
    实现Σ协议的OR证明（零知识证明的或结构）。
    
    目标：证明者知道x1或x2之一（即h1=g^x1或h2=g^x2之一为真），
    但不泄露具体是哪一个。
    
    协议设计：
    - 对于已知的那个x，选择真实的挑战c1和响应s1
    - 对于未知的那个x，伪造挑战c2和响应s2（通过调整a2实现）
    - 利用"求和约束"确保c = c1 + c2
    """
    
    def __init__(self):
        """
        初始化OR证明协议 / Initialize OR proof protocol
        """
        self.prime = 2**256 - 2**224 + 2**192 + 2**96 - 1
        self.field = SimpleField(self.prime)
        self.g = 2
    
    def prove_or(self, x_know, h1, h2, h1_known=True):
        """
        执行OR证明 / Execute OR proof
        
        证明者知道x_know，满足：
        - 如果h1_known=True: h1 = g^x_know
        - 如果h1_known=False: h2 = g^x_know
        
        参数:
            x_know (int): 证明者知道的秘密值
            h1 (int): 第一个公钥
            h2 (int): 第二个公钥
            h1_known (bool): 是否知道h1对应的私钥
        
        返回:
            dict: 包含证明的所有元素
        """
        # 标记哪个公钥是已知的
        known_is_h1 = h1_known
        known_x = x_know
        known_h = h1 if known_is_h1 else h2
        unknown_h = h2 if known_is_h1 else h1
        
        # Step 1: 对已知的情况进行正常的Σ协议
        k1 = secrets.randbits(256)  # 随机选择k1
        a1 = self.field.pow(self.g, k1)  # a1 = g^k1
        
        # Step 2: 对未知的情况，我们需要"模拟"
        # 选择伪造的挑战c2和响应s2，然后反推a2
        c2 = secrets.randbits(256)  # 伪造挑战c2
        s2 = secrets.randbits(256)  # 伪造响应s2
        # a2 = g^s2 / (h2^c2) = g^(s2 - c2 * x_unknown)
        # 但我们不知道x_unknown，所以我们直接设定a2
        # 实际上：a2 = g^s2 * (h2^c2)^(-1) = g^(s2 - c2 * x2)
        # 由于我们不知道x2，我们用a2 = g^s2 / h2^c2，但需要知道x2...
        # 正确的模拟方法是：a2可以是任意值！
        # 验证等式 g^s2 = a2 * h2^c2，所以 a2 = g^s2 * h2^(-c2)
        a2 = self.field.mul(
            self.field.pow(self.g, s2),
            self.field.pow(unknown_h, self.field.prime - 1 - c2)  # h^(-c) = h^(p-1-c)
        )
        
        # Step 3: 计算真实挑战c = Hash(a1, a2, statement)
        # 这里简化：直接使用c1 + c2，但需要分配
        combined = f"{a1}:{a2}:{h1}:{h2}".encode()
        c_total = int.from_bytes(hashlib.sha256(combined).digest(), 'big')
        c_total = c_total % (2**256)
        
        # 对于已知的情况：c1 = c - c2
        c_known = (c_total - c2) % (self.prime - 1)
        s_known = (k1 + c_known * known_x) % (self.prime - 1)
        
        return {
            'a1': a1,
            'a2': a2,
            'c1': c_known,
            'c2': c2,
            's1': s_known,
            's2': s2,
            'h1': h1,
            'h2': h2
        }
    
    def verify_or(self, proof):
        """
        验证OR证明 / Verify OR proof
        
        检查是否满足 g^s1 = a1 * h1^c1 和 g^s2 = a2 * h2^c2
        并且 c1 + c2 = Hash(a1, a2, h1, h2)
        
        参数:
            proof (dict): 包含证明的字典
        
        返回:
            bool: 如果验证通过返回True
        """
        a1 = proof['a1']
        a2 = proof['a2']
        c1 = proof['c1']
        c2 = proof['c2']
        s1 = proof['s1']
        s2 = proof['s2']
        h1 = proof['h1']
        h2 = proof['h2']
        
        # 验证第一个等式: g^s1 = a1 * h1^c1
        left1 = self.field.pow(self.g, s1)
        right1 = self.field.mul(a1, self.field.pow(h1, c1))
        if left1 != right1:
            return False
        
        # 验证第二个等式: g^s2 = a2 * h2^c2
        left2 = self.field.pow(self.g, s2)
        right2 = self.field.mul(a2, self.field.pow(h2, c2))
        if left2 != right2:
            return False
        
        # 验证挑战和约束: c1 + c2 = Hash(a1, a2, h1, h2)
        combined = f"{a1}:{a2}:{h1}:{h2}".encode()
        c_total = int.from_bytes(hashlib.sha256(combined).digest(), 'big')
        c_total = c_total % (2**256)
        if (c1 + c2) % (2**256) != c_total:
            return False
        
        return True


# ============================================================
# 第五部分： Schnorr身份认证协议
# ============================================================

class SchnorrProtocol:
    """
    Schnorr身份认证协议类 / Schnorr Identification Protocol Class
    
    Schnorr协议是经典的Σ协议实例，用于身份认证。
    
    安全性基于离散对数问题的困难性。
    
    协议流程（3步）：
    1. 证明者选择随机r，计算a = g^r，发送a给验证者
    2. 验证者发送随机挑战e
    3. 证明者计算s = r + e*x，发送s给验证者
    4. 验证者检查 g^s = a * h^e
    """
    
    def __init__(self, prime_bits=256):
        """
        初始化Schnorr协议 / Initialize Schnorr protocol
        
        参数:
            prime_bits (int): 素数的比特长度
        """
        # 使用预定义的素数（128位，便于测试）
        # 实际应用中应使用密码学安全的素数
        self.prime = 2**127 - 1  # Mersenne素数
        self.field = SimpleField(self.prime)
        self.generator = 2
        self.private_key = None
        self.public_key = None
    
    def keygen(self, private_key=None):
        """
        密钥生成 / Key generation
        
        参数:
            private_key (int, optional): 私钥，如果为None则随机生成
        
        返回:
            int: 公钥
        """
        if private_key is None:
            private_key = secrets.randbits(128)
        self.private_key = private_key
        self.public_key = self.field.pow(self.generator, private_key)
        return self.public_key
    
    def prove(self, public_key, private_key=None, random_r=None):
        """
        证明者执行Schnorr协议 / Prover executes Schnorr protocol
        
        参数:
            public_key (int): 公钥h = g^x
            private_key (int, optional): 私钥x
            random_r (int, optional): 随机值r
        
        返回:
            tuple: (a, e, s) 承诺、挑战、响应
        """
        if private_key is None:
            private_key = self.private_key
        
        # Step 1: 选择随机r，计算承诺a
        if random_r is None:
            random_r = secrets.randbits(128)
        a = self.field.pow(self.generator, random_r)
        
        # Step 2: 生成挑战e（这里简化，使用哈希生成伪随机挑战）
        # 真实协议中，挑战来自验证者
        challenge_input = f"{a}:{public_key}".encode()
        e = int.from_bytes(hashlib.sha256(challenge_input).digest(), 'big') % self.prime
        
        # Step 3: 计算响应s = r + e * x
        s = (random_r + e * private_key) % (self.prime - 1)
        
        return a, e, s
    
    def verify(self, public_key, a, e, s):
        """
        验证Schnorr证明 / Verify Schnorr proof
        
        检查 g^s = a * h^e
        
        参数:
            public_key (int): 公钥h
            a (int): 承诺值
            e (int): 挑战值
            s (int): 响应值
        
        返回:
            bool: 如果验证通过返回True
        """
        left = self.field.pow(self.generator, s)
        right = self.field.mul(a, self.field.pow(public_key, e))
        return left == right


# ============================================================
# 主程序入口
# ============================================================

if __name__ == "__main__":
    """
    Σ协议族模块测试
    
    演示各种Σ协议的基本功能。
    """
    
    print("=" * 60)
    print("Σ协议族模块测试")
    print("=" * 60)
    
    # 测试1：承诺方案
    print("\n[测试1] Pedersen承诺方案")
    print("-" * 40)
    commit_scheme = CommitmentScheme()
    value = 42
    randomness = 12345
    commitment, returned_randomness = commit_scheme.commit(value, randomness)
    print(f"值: {value}")
    print(f"随机性: {randomness}")
    print(f"承诺值: {commitment}")
    verified = commit_scheme.verify_commitment(commitment, value, randomness)
    print(f"验证结果: {'通过' if verified else '失败'}")
    assert verified, "承诺验证失败"
    print("✓ 承诺方案测试通过")
    
    # 测试2：基本Σ协议
    print("\n[测试2] 基本Σ协议（离散对数）")
    print("-" * 40)
    sigma = SigmaProtocol(security_bits=128)
    secret_x = 12345
    public_h = sigma.setup(secret_x)
    print(f"私钥x: {secret_x}")
    print(f"公钥h = g^x: {public_h}")
    
    # 完整的证明-验证流程
    a = sigma.prover_commit()
    print(f"承诺a = g^k: {a}")
    c = sigma.verifier_challenge()
    print(f"挑战c: {c}")
    s = sigma.prover_response()
    print(f"响应s = k + c*x: {s}")
    verified = sigma.verifier_verify(a, c, s)
    print(f"验证结果: {'通过' if verified else '失败'}")
    assert verified, "Σ协议验证失败"
    print("✓ 基本Σ协议测试通过")
    
    # 测试3：OR证明
    print("\n[测试3] Σ-OR证明")
    print("-" * 40)
    or_proof = SigmaORProof()
    g = 2
    x_known = 111  # 我们知道的私钥
    x_unknown = 222  # 我们不知道的私钥
    h1 = pow(g, x_known, or_proof.prime)  # g^111
    h2 = pow(g, x_unknown, or_proof.prime)  # g^222
    print(f"h1 = g^{x_known}: {h1}")
    print(f"h2 = g^{x_unknown}: {h2}")
    print("证明者知道h1对应的私钥，但不泄露h2的信息")
    
    proof = or_proof.prove_or(x_known, h1, h2, h1_known=True)
    print(f"生成的证明: c1={proof['c1']}, s1={proof['s1']}")
    print(f"            c2={proof['c2']}, s2={proof['s2']}")
    
    verified = or_proof.verify_or(proof)
    print(f"验证结果: {'通过' if verified else '失败'}")
    assert verified, "OR证明验证失败"
    print("✓ Σ-OR证明测试通过")
    
    # 测试4：Schnorr身份认证
    print("\n[测试4] Schnorr身份认证协议")
    print("-" * 40)
    schnorr = SchnorrProtocol(prime_bits=128)
    private_key = 12345
    public_key = schnorr.keygen(private_key)
    print(f"私钥: {private_key}")
    print(f"公钥: {public_key}")
    
    a, e, s = schnorr.prove(public_key, private_key)
    print(f"承诺a: {a}")
    print(f"挑战e: {e}")
    print(f"响应s: {s}")
    
    verified = schnorr.verify(public_key, a, e, s)
    print(f"验证结果: {'通过' if verified else '失败'}")
    assert verified, "Schnorr验证失败"
    print("✓ Schnorr身份认证测试通过")
    
    print("\n" + "=" * 60)
    print("所有测试通过！Σ协议族模块运行正常。")
    print("=" * 60)
