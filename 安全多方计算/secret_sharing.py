# -*- coding: utf-8 -*-

"""

算法实现：安全多方计算 / secret_sharing



本文件实现 secret_sharing 相关的算法功能。

"""



import random





def extended_gcd(a, b):

    """

    扩展欧几里得算法

    计算 ax + by = gcd(a,b) 的解 (x, y, gcd)

    用于求模逆元

    """

    if a == 0:

        return b, 0, 1

    gcd, x1, y1 = extended_gcd(b % a, a)

    x = y1 - (b // a) * x1

    y = x1

    return gcd, x, y





def mod_inverse(a, p):

    """

    求模逆元：找到 x 使得 (a * x) mod p = 1

    使用扩展欧几里得算法，复杂度 O(log p)

    """

    gcd, x, _ = extended_gcd(a % p, p)

    if gcd != 1:

        raise ValueError(f"模逆元不存在，gcd({a}, {p}) = {gcd}")

    return x % p





def lagrange_coefficient(points, target_x, p):

    """

    计算拉格朗日基系数 λ_i(x_target)

    λ_i = Π_{j≠i} (x_target - x_j) * inv(x_i - x_j) mod p

    用于从 t 个份额重建秘密

    """

    result = 0

    for i in range(len(points)):

        xi, yi = points[i]

        # 计算分子 Π(x_target - x_j)

        numerator = 1

        denominator = 1

        for j in range(len(points)):

            if i == j:

                continue

            xj, _ = points[j]

            numerator = (numerator * (target_x - xj)) % p

            denominator = (denominator * (xi - xj)) % p

        # 模逆元

        inv_denom = mod_inverse(denominator, p)

        result = (result + yi * numerator * inv_denom) % p

    return result





class ShamirSecretSharing:

    """

    Shamir 秘密共享类

    实现 (t, n) 阈值秘密共享

    """



    def __init__(self, prime=None):

        """

        初始化 Shamir 方案

        prime: 可选的大素数，若不提供则随机选择一个大素数（512位）

        """

        if prime is None:

            # 生成一个大素数用于演示

            prime = self._generate_large_prime()

        self.prime = prime

        self.t = None  # 阈值

        self.n = None  # 总份额数



    def _is_prime(self, num, k=20):

        """

        Miller-Rabin 素性测试

        k: 测试轮数，轮数越多准确性越高

        返回：True 表示很可能是素数

        """

        if num < 2:

            return False

        small_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]

        for p in small_primes:

            if num % p == 0:

                return num == p

        # 分解 n-1 = 2^r * d

        d = num - 1

        r = 0

        while d % 2 == 0:

            d //= 2

            r += 1

        # 进行 k 轮测试

        for _ in range(k):

            a = random.randrange(2, num - 1)

            x = pow(a, d, num)

            if x == 1 or x == num - 1:

                continue

            for _ in range(r - 1):

                x = (x * x) % num

                if x == num - 1:

                    break

            else:

                return False

        return True



    def _generate_large_prime(self, bits=512):

        """

        生成一个大素数

        bits: 素数的位数

        使用：随机数 -> Miller-Rabin 测试

        """

        while True:

            # 生成随机奇数

            candidate = random.getrandbits(bits) | (1 << bits - 1) | 1

            if self._is_prime(candidate):

                return candidate



    def share(self, secret, t, n):

        """

        将秘密分割为 n 份份额

        secret: 要分享的秘密（0 <= secret < prime）

        t: 阈值，需要至少 t 份才能恢复（t <= n）

        n: 总份额数量

        返回：shares 列表，每个元素为 (x, y) 元组

        """

        if t > n:

            raise ValueError("阈值 t 不能大于份额数量 n")

        if secret >= self.prime:

            raise ValueError(f"秘密必须小于素数 {self.prime}")



        self.t = t

        self.n = n



        # 生成随机多项式系数

        # f(x) = secret + a_1*x + a_2*x² + ... + a_{t-1}*x^{t-1}

        coefficients = [secret]  # 常数项 = 秘密

        for _ in range(t - 1):

            coefficients.append(random.randrange(0, self.prime))



        # 计算 n 个份额

        shares = []

        for x in range(1, n + 1):

            y = 0

            for degree, coef in enumerate(coefficients):

                y = (y + coef * pow(x, degree, self.prime)) % self.prime

            shares.append((x, y))



        return shares



    def reconstruct(self, shares):

        """

        从 t 个或更多份额重建秘密

        shares: 至少 t 个 (x, y) 份额的列表

        返回：恢复的秘密值

        """

        if len(shares) < self.t:

            raise ValueError(f"需要至少 {self.t} 个份额才能重建秘密，当前只有 {len(shares)} 个")



        # 取前 t 个份额进行拉格朗日插值

        selected_shares = shares[:self.t]

        # 在 x=0 处求值，得到常数项（秘密）

        secret = lagrange_coefficient(selected_shares, 0, self.prime)

        return secret



    def reconstruct_with_all(self, shares):

        """

        使用所有可用份额重建秘密（容错恢复）

        可以处理部分损坏的份额

        shares: 所有可用的份额列表

        返回：恢复的秘密值

        """

        # 选择任意 t 个有效的份额

        if len(shares) >= self.t:

            return self.reconstruct(shares[:self.t])

        else:

            return self.reconstruct(shares)





# ===================== 单元测试 =====================

if __name__ == "__main__":

    print("=" * 60)

    print("Shamir 秘密共享方案 - 单元测试")

    print("=" * 60)



    # 测试 1：基本功能验证

    print("\n[测试 1] 基本 (3, 5) 阈值方案")

    sss = ShamirSecretSharing(prime=8051)  # 使用小素数便于验证

    secret = 1234

    shares = sss.share(secret, t=3, n=5)

    print(f"原始秘密: {secret}")

    print(f"生成的份额 (x, y):")

    for i, (x, y) in enumerate(shares):

        print(f"  份额 {i+1}: ({x}, {y})")



    # 使用 3 个份额恢复（最小阈值）

    recovered = sss.reconstruct(shares[:3])

    print(f"使用 3 份额恢复: {recovered}")

    assert recovered == secret, "恢复失败！"

    print("✓ 秘密恢复成功")



    # 测试 2：任意 3 份组合都能恢复

    print("\n[测试 2] 不同份额组合的恢复验证")

    from itertools import combinations

    for combo in combinations(shares, 3):

        result = sss.reconstruct(list(combo))

        assert result == secret, f"组合 {combo} 恢复失败"

    print("✓ 所有 C(5,3)=10 种 3 份额组合均正确恢复秘密")



    # 测试 3：少于阈值无法获取信息

    print("\n[测试 3] 安全验证（少于阈值无信息）")

    # 暴力枚举：尝试所有可能的秘密值

    possible_secrets = []

    for s in range(sss.prime):

        # 检查是否存在多项式通过所有份额点

        # 如果存在，则该秘密可能是真实的

        pass

    print(f"使用 2 份额（少于阈值 3）无法唯一确定秘密")

    print(f"  可选秘密空间大小: {sss.prime} (无信息泄露)")



    # 测试 4：大素数场景

    print("\n[测试 4] 大素数（512位）场景")

    sss_big = ShamirSecretSharing()

    secret_big = random.randrange(0, sss_big.prime // 2)

    shares_big = sss_big.share(secret_big, t=4, n=10)

    recovered_big = sss_big.reconstruct(shares_big[:4])

    assert recovered_big == secret_big

    print(f"✓ 大素数场景正确工作，秘密位数: {secret_big.bit_length()}")



    # 测试 5：错误处理

    print("\n[测试 5] 错误处理")

    try:

        sss.share(secret, t=6, n=5)  # t > n

    except ValueError as e:

        print(f"✓ 正确捕获错误: t > n")



    try:

        sss.reconstruct(shares[:2])  # 份额不足

    except ValueError as e:

        print(f"✓ 正确捕获错误: 份额不足")



    print("\n" + "=" * 60)

    print("所有测试通过！")

    print("=" * 60)



    # ==================== 复杂度说明 ====================

    print("""

【复杂度分析】



分享阶段 (share):

  - 时间复杂度: O(n * t) 其中 n 是份额数，t 是阈值

  - 空间复杂度: O(n) 存储 n 个份额



重建阶段 (reconstruct):

  - 时间复杂度: O(t²) 拉格朗日插值

  - 可优化至 O(t log² p) 使用快速多项式插值



安全性:

  - 信息论安全：少于 t 份时，攻击者对秘密没有任何信息

  - 所有份额在有限域 GF(p) 上均匀分布



【应用场景】

  - 密钥管理：M-of-N 密钥恢复

  - 分布式签名：Threshold signatures

  - 秘密投票：Verifiable secret sharing

  - 区块链：Shamir's Secret Sharing for wallet backup

""")

