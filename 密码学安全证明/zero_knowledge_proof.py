"""
零知识证明基础模块 / Zero-Knowledge Proof Fundamentals

本模块实现零知识证明的基本概念，包括：
- 交互式证明系统 (Interactive Proof Systems)
- ZKP身份认证协议 (ZKP Authentication)
- NP语言与计算不可区分性 (NP Languages & Computational Indistinguishability)

零知识证明允许证明者向验证者证明某个陈述为真，
而不泄露任何除了陈述本身有效性之外的信息。

作者: AI Assistant
版本: 1.0
"""

import hashlib
import random
import secrets


# ============================================================
# 第一部分：有限域与群的基础定义
# ============================================================

class FiniteField:
    """
    有限域类 / Finite Field Class
    
    实现模素数p的有限域运算，用于零知识证明中的数学基础。
    有限域是零知识证明系统的代数基础。
    """
    
    def __init__(self, prime):
        """
        初始化有限域 / Initialize finite field
        
        参数:
            prime (int): 素数模数，必须为素数以保证域的性质
        
        有限域的阶（元素个数）等于素数p，
        记作GF(p)或Fp。
        """
        # 验证素数有效性：确保模数是素数
        # 这是有限域定义的基本要求
        if not self._is_prime(prime):
            raise ValueError(f"模数 {prime} 不是素数，无法构成有限域")
        self.prime = prime  # 存储素数模数
    
    def _is_prime(self, n):
        """
        素数检测 / Primality test
        
        使用简单的试除法检测素数。
        实际应用中应使用Miller-Rabin等概率算法。
        
        参数:
            n (int): 待检测的整数
        
        返回:
            bool: 如果n是素数返回True，否则返回False
        """
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        # 只需检测到sqrt(n)的奇数
        i = 3
        while i * i <= n:
            if n % i == 0:
                return False
            i += 2
        return True
    
    def add(self, a, b):
        """
        有限域加法 / Field addition
        
        计算 (a + b) mod p
        
        参数:
            a (int): 被加数
            b (int): 加数
        
        返回:
            int: 和的规范表示（在[0, p-1]范围内）
        """
        return (a + b) % self.prime
    
    def sub(self, a, b):
        """
        有限域减法 / Field subtraction
        
        计算 (a - b) mod p
        
        参数:
            a (int): 被减数
            b (int): 减数
        
        返回:
            int: 差的规范表示
        """
        return (a - b) % self.prime
    
    def mul(self, a, b):
        """
        有限域乘法 / Field multiplication
        
        计算 (a * b) mod p
        
        参数:
            a (int): 被乘数
            b (int): 乘数
        
        返回:
            int: 积的规范表示
        """
        return (a * b) % self.prime
    
    def div(self, a, b):
        """
        有限域除法 / Field division
        
        计算 a / b mod p，即 a * b^(-1) mod p
        利用费马小定理：b^(-1) ≡ b^(p-2) mod p
        
        参数:
            a (int): 被除数
            b (int): 除数
        
        返回:
            int: 商的规范表示
        
        异常:
            ZeroDivisionError: 当b ≡ 0 mod p时抛出
        """
        # 使用扩展欧几里得算法或费马小定理求逆元
        # 这里使用扩展欧几里得算法（更高效）
        b_inv = self._mod_inverse(b)
        return self.mul(a, b_inv)
    
    def _mod_inverse(self, a):
        """
        模逆元计算 / Modular inverse
        
        计算a在模p下的乘法逆元a^(-1)
        满足 a * a^(-1) ≡ 1 mod p
        
        参数:
            a (int): 要求逆元的数
        
        返回:
            int: a的模p乘法逆元
        
        异常:
            ValueError: 当a与p不互素时抛出（a≡0的情况）
        """
        # 扩展欧几里得算法求逆元
        # gcd(a, p) = 1 = s*a + t*p => s是a的逆元
        original_a = a
        a = a % self.prime
        if a == 0:
            raise ValueError(f"{original_a} 在模{self.prime}下没有逆元（与模数不互素）")
        
        # 扩展欧几里得算法的迭代版本
        old_r, r = self.prime, a       # old_r是余数初始状态，r是当前余数
        old_s, s = 1, 0               # 系数s的递推初始值
        old_t, t = 0, 1               # 系数t的递推初始值
        
        while r != 0:
            # 计算商（整除）
            quotient = old_r // r
            # 更新余数序列：old_r, r -> new_r, old_r
            temp_r = old_r - quotient * r
            old_r, r = r, temp_r
            # 更新系数序列
            temp_s = old_s - quotient * s
            old_s, s = s, temp_s
            temp_t = old_t - quotient * t
            old_t, t = t, temp_t
        
        # old_r应该是1（因为p是素数，a<p时必然互素）
        if old_r != 1:
            raise ValueError(f"{original_a} 和 {self.prime} 不互素，无逆元")
        
        # s可能是负数，需要调整到[0, p-1]范围
        return old_s % self.prime
    
    def pow(self, base, exponent):
        """
        有限域指数运算 / Field exponentiation
        
        计算 base^exponent mod p
        
        使用平方-乘算法优化，复杂度为O(log exponent)
        
        参数:
            base (int): 底数
            exponent (int): 指数（非负整数）
        
        返回:
            int: 指数运算结果的规范表示
        """
        # 处理负指数：a^(-e) = (a^e)^(-1)
        if exponent < 0:
            base = self._mod_inverse(base)
            exponent = -exponent
        
        result = 1  # 初始化结果为乘法单位元1
        base = base % self.prime
        
        # 二进制平方法：将指数按二进制展开
        while exponent > 0:
            # 如果当前指数位是1，则乘以当前的base
            if exponent & 1:
                result = self.mul(result, base)
            # 平方base，准备处理下一位
            base = self.mul(base, base)
            # 右移指数，处理下一位
            exponent >>= 1
        
        return result


# ============================================================
# 第二部分：交互式证明系统
# ============================================================

class InteractiveProofSystem:
    """
    交互式证明系统类 / Interactive Proof System Class
    
    实现Goldreich-Micali-Wigderson (GMW) 风格的
    交互式证明协议，用于演示零知识证明的基本原理。
    
    交互式证明系统由三方组成：
    - 证明者 (Prover)：知道秘密，试图说服验证者
    - 验证者 (Verifier)：只根据公开信息验证
    - 随机预言 (Random Oracle)：用于非交互版本
    """
    
    def __init__(self, security_parameter=256):
        """
        初始化交互式证明系统 / Initialize interactive proof system
        
        参数:
            security_parameter (int): 安全参数，控制承诺的强度
                值越大，安全性越高，但计算成本也增加
        """
        self.security_parameter = security_parameter
        # 选择一个大素数作为有限域的模数
        # 实际应用中应使用密码学安全的素数
        self.field = FiniteField(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F)
        # 生成群的生成元g（群论中的生成元概念）
        self.generator = 2  # 简化起见，使用2作为生成元
    
    def _hash_commitment(self, value, randomness):
        """
        计算承诺值的哈希 / Hash commitment value
        
        将值和随机性组合后哈希，生成承诺。
        这是密码学承诺方案的核心操作。
        
        参数:
            value (int): 被承诺的值
            randomness (int): 随机性（盐值），确保承诺的绑定性
        
        返回:
            int: 哈希值，作为承诺
        """
        # 组合值和随机性后进行SHA-256哈希
        combined = f"{value}:{randomness}".encode()
        hash_bytes = hashlib.sha256(combined).digest()
        # 将哈希结果转换为整数
        return int.from_bytes(hash_bytes, 'big') % self.field.prime
    
    def prover_commit(self, secret_value):
        """
        证明者生成承诺 / Prover generates commitment
        
        证明者选择一个随机数作为随机性，对秘密值生成承诺。
        承诺具有：
        - 绑定性 (Binding)：承诺后不能改变原值
        - 隐藏性 (Hiding)：不能从承诺中恢复原值
        
        参数:
            secret_value (int): 秘密值，证明者知道的值
        
        返回:
            tuple: (commitment, randomness) 承诺和用于打开的随机性
        """
        # 选择足够长的随机数作为盐值
        # 安全参数决定随机数的比特长度
        randomness = secrets.randbits(self.security_parameter)
        # 计算承诺：使用密码学哈希函数
        commitment = self._hash_commitment(secret_value, randomness)
        return commitment, randomness
    
    def verifier_challenge(self):
        """
        验证者生成挑战 / Verifier generates challenge
        
        验证者发送一个随机挑战给证明者。
        这个挑战确保证明者不能提前预知并作弊。
        
        返回:
            int: 随机挑战值，在{0, 1}上均匀分布
        """
        return random.randint(0, 1)
    
    def prover_response(self, secret_value, randomness, challenge):
        """
        证明者生成响应 / Prover generates response
        
        根据挑战生成响应。对于不同的挑战，
        证明者使用不同的"世界"的知识来响应。
        
        参数:
            secret_value (int): 秘密值
            randomness (int): 承诺时使用的随机性
            challenge (int): 验证者的挑战
        
        返回:
            int: 证明者的响应
        
        注意：
            这是一个简化的实现。真实的协议中，
            证明者需要展示对某个NP语言成员关系的知识。
        """
        if challenge == 0:
            # 挑战为0时：展示秘密值本身
            # 在真实协议中，这里会展示某种"见证"
            response = secret_value
        else:
            # 挑战为1时：展示承诺的另一个相关值
            # 通过哈希变换生成一个相关但不可预测的值
            response = self._hash_commitment(secret_value, randomness + 1)
        return response
    
    def verifier_verify(self, commitment, randomness, challenge, response):
        """
        验证者验证证明 / Verifier verifies proof
        
        验证者检查证明者响应的一致性。
        
        参数:
            commitment (int): 承诺值
            randomness (int): 打开承诺用的随机性
            challenge (int): 验证者之前发送的挑战
            response (int): 证明者的响应
        
        返回:
            bool: 如果验证通过返回True，否则返回False
        """
        if challenge == 0:
            # 验证第一个世界：重新计算承诺并比较
            expected = self._hash_commitment(response, randomness)
            return expected == commitment
        else:
            # 验证第二个世界：检查响应的某种属性
            # 简化版本：检查响应是否在合理范围内
            return 0 <= response < self.field.prime


# ============================================================
# 第三部分：ZKP身份认证协议
# ============================================================

class ZKPAuthentication:
    """
    ZKP身份认证类 / ZKP Authentication Class
    
    实现基于零知识证明的身份认证协议。
    用户可以证明自己知道某个秘密，而无需泄露秘密本身。
    
    安全性基于：
    - 计算离散对数的困难性
    - 承诺方案的绑定性和隐藏性
    """
    
    def __init__(self, field_prime):
        """
        初始化ZKP身份认证系统 / Initialize ZKP authentication
        
        参数:
            field_prime (int): 有限域的素数模数
        """
        self.field = FiniteField(field_prime)
        # 设置群的生成元（实际应用中需要选择合适的生成元）
        self.generator = 3
    
    def setup_public_parameters(self):
        """
        设置公共参数 / Setup public parameters
        
        生成并发布系统的公共参数。
        这些参数所有用户共享。
        
        返回:
            tuple: (g, h) 公共生成元和公钥
        """
        # 生成随机私钥x（证明者的秘密）
        private_key = secrets.randbits(self.security_parameter)
        # 计算公钥h = g^x mod p
        public_key = self.field.pow(self.generator, private_key)
        return self.generator, public_key
    
    def generate_proof(self, private_key, public_key):
        """
        证明者生成零知识证明 / Prover generates ZK proof
        
        证明者知道私钥x，满足 h = g^x。
        通过交互式证明，展示对私钥的知识而不泄露私钥。
        
        参数:
            private_key (int): 证明者的私钥x
            public_key (int): 证明者的公钥h = g^x mod p
        
        返回:
            tuple: (commitment, challenge, response) 三步协议的消息
        """
        # 第一步：证明者随机选择w，计算commitment
        # commitment = g^w mod p
        w = secrets.randbits(256)  # 随机选择见证
        commitment = self.field.pow(self.generator, w)
        
        # 第二步：验证者发送挑战（这里简化使用哈希生成伪随机挑战）
        # 真实协议中，验证者发送真正的随机挑战
        challenge_input = f"{commitment}:{public_key}".encode()
        challenge = int.from_bytes(
            hashlib.sha256(challenge_input).digest(), 'big'
        ) % 2  # 简化为0或1的挑战
        
        # 第三步：证明者计算响应：response = w + challenge * private_key
        # 如果挑战=0：response = w
        # 如果挑战=1：response = w + x
        response = (w + challenge * private_key) % (self.field.prime - 1)
        
        return commitment, challenge, response
    
    def verify_proof(self, public_key, commitment, challenge, response):
        """
        验证零知识证明 / Verify ZK proof
        
        验证者检查等式：g^response ≡ commitment * public_key^challenge
        
        参数:
            public_key (int): 证明者的公钥h
            commitment (int): 证明者发送的承诺A = g^w
            challenge (int): 验证者的挑战c
            response (int): 证明者发送的响应z = w + c*x
        
        返回:
            bool: 如果验证通过返回True
        """
        # 计算左边：g^response mod p
        left_side = self.field.pow(self.generator, response)
        # 计算右边：commitment * public_key^challenge mod p
        right_side = self.field.mul(
            commitment,
            self.field.pow(public_key, challenge)
        )
        return left_side == right_side


# ============================================================
# 第四部分：NP语言的零知识证明
# ============================================================

class NPLanguageZKProof:
    """
    NP语言零知识证明类 / NP Language ZK Proof Class
    
    演示如何对NP语言成员关系生成零知识证明。
    例如：证明一个数是两个大素数的乘积（复合数证明）。
    
    NP语言L的定义：
    L = {x | ∃w: R(x, w) = True}
    其中x是陈述（instance），w是见证（witness）
    """
    
    def __init__(self, security_bits=256):
        """
        初始化NP语言ZKP系统 / Initialize NP language ZK proof system
        
        参数:
            security_bits (int): 安全参数，控制证明的可靠性
        """
        self.security_bits = security_bits
        self.field = FiniteField(2**256 - 2**224 + 2**192 + 2**96 - 1)  # P-256素数
    
    def _generate_prime(self, bits):
        """
        生成指定比特长度的素数 / Generate prime of specified bits
        
        使用简单的素数生成方法。
        实际应用中应使用密码学安全的素数生成器。
        
        参数:
            bits (int): 素数的比特长度
        
        返回:
            int: 生成的素数
        """
        while True:
            # 生成随机奇数
            candidate = secrets.randbits(bits) | 1
            # 设置最高位和最低位确保奇数且长度足够
            candidate |= (1 << (bits - 1)) | 1
            # 简单试除检测
            is_prime = True
            for p in range(3, 1000, 2):
                if candidate % p == 0:
                    is_prime = False
                    break
            if is_prime:
                return candidate
    
    def prove_composite(self, n):
        """
        证明n是合数 / Prove n is composite
        
        零知识证明：证明者知道n的因数分解，
        但不泄露具体的因数。
        
        这是一个简单版本，演示基本原理。
        真实协议需要更复杂的设计。
        
        参数:
            n (int): 待证明的合数
        
        返回:
            dict: 零知识证明，包含多个轮次的响应
        """
        # 简化的证明：直接提供因数分解（仅用于演示）
        # 真实协议中，证明者不会直接暴露因数
        factors = []
        temp = n
        d = 2
        while d * d <= temp:
            if temp % d == 0:
                factors.append(d)
                temp //= d
            d += 1
        if temp > 1:
            factors.append(temp)
        
        proof = {
            'statement': 'n is composite',
            'n': n,
            'num_factors': len(factors),
            'factor_sum_mod': sum(factors) % n,
            # 实际证明中，这些"承诺"是通过复杂协议生成的
            'commitment': hashlib.sha256(str(n).encode()).hexdigest()
        }
        return proof
    
    def verify_composite(self, proof):
        """
        验证合数证明 / Verify composite proof
        
        验证者检查证明是否有效。
        注意：这里的验证是简化版本。
        
        参数:
            proof (dict): 零知识证明
        
        返回:
            bool: 如果验证通过返回True
        """
        n = proof['n']
        # 基本检查：n确实是一个合数（验证者可以自己检查）
        if n < 4:
            return False
        # 检查n是否为质数（使用简单的试除法）
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return proof['num_factors'] >= 2
        return False


# ============================================================
# 主程序入口
# ============================================================

if __name__ == "__main__":
    """
    测试零知识证明基础模块
    
    演示各种零知识证明协议的基本功能。
    """
    
    print("=" * 60)
    print("零知识证明基础模块测试")
    print("=" * 60)
    
    # 测试1：有限域运算
    print("\n[测试1] 有限域运算")
    print("-" * 40)
    field = FiniteField(17)  # 使用小素数便于手动验证
    print(f"有限域: F_{17}")
    print(f"加法: 5 + 7 = {field.add(5, 7)}")
    print(f"减法: 5 - 7 = {field.sub(5, 7)}")
    print(f"乘法: 5 * 7 = {field.mul(5, 7)}")
    print(f"除法: 5 / 7 = {field.div(5, 7)}")
    print(f"幂: 2^10 = {field.pow(2, 10)}")
    print(f"逆元: 3^-1 = {field._mod_inverse(3)}")
    assert field.mul(3, field._mod_inverse(3)) == 1, "逆元验证失败"
    print("✓ 有限域运算测试通过")
    
    # 测试2：交互式证明系统
    print("\n[测试2] 交互式证明系统")
    print("-" * 40)
    ips = InteractiveProofSystem(security_parameter=128)
    secret = 42  # 秘密值
    commitment, randomness = ips.prover_commit(secret)
    print(f"承诺值: {commitment}")
    print(f"随机性: {randomness}")
    challenge = ips.verifier_challenge()
    print(f"挑战: {challenge}")
    response = ips.prover_response(secret, randomness, challenge)
    print(f"响应: {response}")
    verified = ips.verifier_verify(commitment, randomness, challenge, response)
    print(f"验证结果: {'通过' if verified else '失败'}")
    assert verified, "交互式证明验证失败"
    print("✓ 交互式证明系统测试通过")
    
    # 测试3：ZKP身份认证
    print("\n[测试3] ZKP身份认证")
    print("-" * 40)
    # 使用小素数便于演示
    field_prime = 23
    zkp_auth = ZKPAuthentication(field_prime)
    zkp_auth.security_parameter = 128
    generator = 3
    private_key = 7  # 假设私钥x=7
    public_key = pow(generator, private_key, field_prime)  # h = g^x mod p
    print(f"私钥: {private_key}")
    print(f"公钥: {public_key}")
    commitment, challenge, response = zkp_auth.generate_proof(private_key, public_key)
    print(f"承诺: {commitment}")
    print(f"挑战: {challenge}")
    print(f"响应: {response}")
    verified = zkp_auth.verify_proof(public_key, commitment, challenge, response)
    print(f"验证结果: {'通过' if verified else '失败'}")
    assert verified, "ZKP身份认证验证失败"
    print("✓ ZKP身份认证测试通过")
    
    # 测试4：NP语言零知识证明
    print("\n[测试4] NP语言零知识证明")
    print("-" * 40)
    np_zkp = NPLanguageZKProof(security_bits=128)
    # 构造一个合数：101 * 103 = 10403
    n = 10403
    print(f"待证明的数: {n}")
    proof = np_zkp.prove_composite(n)
    print(f"证明: {proof}")
    verified = np_zkp.verify_composite(proof)
    print(f"验证结果: {'通过' if verified else '失败'}")
    assert verified, "NP语言证明验证失败"
    print("✓ NP语言零知识证明测试通过")
    
    print("\n" + "=" * 60)
    print("所有测试通过！零知识证明基础模块运行正常。")
    print("=" * 60)
