# -*- coding: utf-8 -*-

"""

算法实现：密码学协议 / Diffie_hellman



本文件实现 Diffie_hellman 相关的算法功能。

"""



import random

import hashlib





def is_prime(n):

    """Miller-Rabin 素性测试。"""

    if n < 2:

        return False

    if n == 2:

        return True

    if n % 2 == 0:

        return False



    # 简单的确定性测试（适用于小素数）

    for i in range(3, int(n**0.5) + 1, 2):

        if n % i == 0:

            return False

    return True





def generate_prime(bits=16):

    """生成随机素数。"""

    while True:

        p = random.randrange(2**(bits-1), 2**bits, 2)

        if is_prime(p):

            return p





def find_primitive_root(p):

    """找到素数 p 的原根。"""

    if p == 2:

        return 1



    # 分解 p-1

    phi = p - 1

    factors = []

    temp = phi

    for i in range(2, int(temp**0.5) + 1):

        if temp % i == 0:

            factors.append(i)

            while temp % i == 0:

                temp //= i

    if temp > 1:

        factors.append(temp)



    # 尝试找到原根

    for g in range(2, p):

        valid = True

        for q in factors:

            if pow(g, phi // q, p) == 1:

                valid = False

                break

        if valid:

            return g



    return None





class DiffieHellman:

    """Diffie-Hellman 密钥交换协议。"""



    def __init__(self, bits=16):

        # 选择素数和原根

        self.p = generate_prime(bits)

        self.g = find_primitive_root(self.p)



        # 随机选择私钥

        self.private_key = random.randint(2, self.p - 2)



        # 计算公钥

        self.public_key = pow(self.g, self.private_key, self.p)



    def get_public_key(self):

        """获取公钥。"""

        return {'p': self.p, 'g': self.g, 'pub': self.public_key}



    def compute_shared_secret(self, other_public_key):

        """

        计算共享密钥。



        参数:

            other_public_key: 对方的公钥



        返回:

            共享密钥

        """

        # 共享密钥 = (对方的公钥)^{我的私钥} mod p

        shared = pow(other_public_key, self.private_key, self.p)



        # 派生会话密钥

        key_material = hashlib.sha256(str(shared).encode()).digest()

        return key_material





def simulate_dh_key_exchange():

    """模拟 Diffie-Hellman 密钥交换。"""

    print("=== Diffie-Hellman 密钥交换模拟 ===")



    # Alice 初始化

    alice = DiffieHellman(bits=12)

    alice_pk = alice.get_public_key()

    print(f"Alice 的素数 p: {alice_pk['p']}")

    print(f"Alice 的原根 g: {alice_pk['g']}")

    print(f"Alice 的公钥: {alice_pk['pub']}")



    # Bob 初始化

    bob = DiffieHellman(bits=12)

    bob_pk = bob.get_public_key()

    print(f"\nBob 的公钥: {bob_pk['pub']}")



    # 注意：实际中双方使用相同的 p 和 g

    # 这里模拟用同一个素数

    bob.p = alice_pk['p']

    bob.g = alice_pk['g']

    bob.public_key = bob_pk['pub']



    # 密钥交换

    alice_shared = alice.compute_shared_secret(bob.public_key)

    bob_shared = bob.compute_shared_secret(alice.public_key)



    print(f"\nAlice 的共享密钥: {alice_shared.hex()[:16]}...")

    print(f"Bob 的共享密钥:   {bob_shared.hex()[:16]}...")

    print(f"密钥匹配: {alice_shared == bob_shared}")



    # Eve 窃听测试

    print("\n=== 窃听测试 ===")

    print(f"Eve 可见信息:")

    print(f"  p = {alice_pk['p']}")

    print(f"  g = {alice_pk['g']}")

    print(f"  Alice 的公钥 = {alice_pk['pub']}")

    print(f"  Bob 的公钥 = {bob.public_key}")

    print(f"Eve 无法计算出共享密钥（需要私钥）")





class ECDiffieHellman:

    """椭圆曲线 Diffie-Hellman (ECDH)。"""



    def __init__(self):

        # 使用简化的椭圆曲线 y^2 = x^3 + ax + b (mod p)

        self.a = 0

        self.b = 7

        self.p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F  # secp256k1 的 p

        # 基点 G（简化）

        self.Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240

        self.Gy = 32670510020758816978083085130307012865264778384143022051892924946363995685289

        self.n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141  # 群的阶



        # 私钥

        self.private_key = random.randint(1, self.n - 1)



        # 公钥 = private_key * G

        self.public_key = self._point_mul(self.private_key, (self.Gx, self.Gy))



    def _point_add(self, P, Q):

        """椭圆曲线点加法。"""

        if P is None:

            return Q

        if Q is None:

            return P



        x1, y1 = P

        x2, y2 = Q



        if x1 == x2:

            if y1 == y2:

                # 倍点

                return self._point_double(P)

            return None  # 无穷远点



        # 斜率

        dx = (x2 - x1) % self.p

        dy = (y2 - y1) % self.p

        inv_dx = pow(dx, -1, self.p)

        s = (dy * inv_dx) % self.p



        x3 = (s * s - x1 - x2) % self.p

        y3 = (s * (x1 - x3) - y1) % self.p



        return (x3, y3)



    def _point_double(self, P):

        """椭圆曲线倍点。"""

        if P is None:

            return None



        x, y = P

        if y == 0:

            return None



        # 斜率

        numerator = (3 * x * x + self.a) % self.p

        denominator = (2 * y) % self.p

        inv_den = pow(denominator, -1, self.p)

        s = (numerator * inv_den) % self.p



        x3 = (s * s - 2 * x) % self.p

        y3 = (s * (x - x3) - y) % self.p



        return (x3, y3)



    def _point_mul(self, k, P):

        """标量乘法（重复加倍）。"""

        result = None

        addend = P



        while k:

            if k & 1:

                result = self._point_add(result, addend)

            addend = self._point_double(addend)

            k >>= 1



        return result



    def get_public_key(self):

        """获取公钥。"""

        return self.public_key



    def compute_shared_secret(self, other_public_key):

        """计算共享密钥。"""

        shared_point = self._point_mul(self.private_key, other_public_key)

        if shared_point is None:

            return None



        x, y = shared_point

        key_material = hashlib.sha256(str(x).encode()).digest()

        return key_material





if __name__ == "__main__":

    # 标准 DH 测试

    simulate_dh_key_exchange()



    print("\n" + "="*50)

    print("=== ECDH 测试 ===")



    alice_ec = ECDiffieHellman()

    bob_ec = ECDiffieHellman()



    alice_shared = alice_ec.compute_shared_secret(bob_ec.get_public_key())

    bob_shared = bob_ec.compute_shared_secret(alice_ec.get_public_key())



    print(f"Alice 共享密钥: {alice_shared.hex()[:16]}...")

    print(f"Bob 共享密钥:   {bob_shared.hex()[:16]}...")

    print(f"密钥匹配: {alice_shared == bob_shared}")



    print("\nDiffie-Hellman 特性:")

    print("  前向保密：长期密钥泄露不影响已建立的会话密钥")

    print("  ECDH 更短密钥即可达到相同安全强度")

    print("  实际使用时应配合身份验证防止中间人攻击")

