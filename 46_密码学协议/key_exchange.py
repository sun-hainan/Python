# -*- coding: utf-8 -*-

"""

算法实现：密码学协议 / key_exchange



本文件实现 key_exchange 相关的算法功能。

"""



import random

import hashlib





def is_prime(n):

    if n < 2:

        return False

    if n == 2:

        return True

    if n % 2 == 0:

        return False

    for i in range(3, int(n**0.5) + 1, 2):

        if n % i == 0:

            return False

    return True





def generate_prime(bits=16):

    while True:

        p = random.randrange(2**(bits-1), 2**bits, 2)

        if is_prime(p):

            return p





def find_generator(p):

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

    for g in range(2, p):

        valid = True

        for q in factors:

            if pow(g, phi // q, p) == 1:

                valid = False

                break

        if valid:

            return g

    return None





class DHKeyExchange:

    """标准 Diffie-Hellman 密钥交换。"""



    def __init__(self, p=None, g=None):

        self.p = p or generate_prime(16)

        self.g = g or find_generator(self.p)



    def generate_keypair(self):

        """生成 DH 密钥对。"""

        private = random.randint(2, self.p - 2)

        public = pow(self.g, private, self.p)

        return private, public



    def compute_shared(self, my_private, their_public):

        """计算共享密钥。"""

        return pow(their_public, my_private, self.p)





class ECDHKeyExchange:

    """椭圆曲线 Diffie-Hellman。"""



    def __init__(self):

        # secp256k1 曲线参数

        self.p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F

        self.a = 0

        self.b = 7

        self.G = (55066263022277343669578718895168534326250603453777594175500187360389116729240,

                  32670510020758816978083085130307012865264778384143022051892924946363995685289)

        self.n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141



    def point_add(self, P, Q):

        if P is None:

            return Q

        if Q is None:

            return P

        x1, y1 = P

        x2, y2 = Q

        if x1 == x2:

            if y1 == y2:

                return self.point_double(P)

            return None

        dx = (x2 - x1) % self.p

        dy = (y2 - y1) % self.p

        inv_dx = pow(dx, -1, self.p)

        s = (dy * inv_dx) % self.p

        x3 = (s * s - x1 - x2) % self.p

        y3 = (s * (x1 - x3) - y1) % self.p

        return (x3, y3)



    def point_double(self, P):

        if P is None:

            return None

        x, y = P

        numerator = (3 * x * x + self.a) % self.p

        denominator = (2 * y) % self.p

        inv_den = pow(denominator, -1, self.p)

        s = (numerator * inv_den) % self.p

        x3 = (s * s - 2 * x) % self.p

        y3 = (s * (x - x3) - y) % self.p

        return (x3, y3)



    def point_mul(self, k, P):

        result = None

        addend = P

        while k:

            if k & 1:

                result = self.point_add(result, addend)

            addend = self.point_double(addend)

            k >>= 1

        return result



    def generate_keypair(self):

        """生成 ECDH 密钥对。"""

        private = random.randint(1, self.n - 1)

        public = self.point_mul(private, self.G)

        return private, public



    def compute_shared(self, my_private, their_public):

        """计算共享密钥。"""

        shared_point = self.point_mul(my_private, their_public)

        if shared_point is None:

            return None

        x, y = shared_point

        return int(hashlib.sha256(str(x).encode()).hexdigest(), 16)





class MQVKeyExchange:

    """MQV 协议（简化版）。"""



    def __init__(self, dh):

        self.dh = dh



    def generate_keypair(self):

        """生成 MQV 密钥对。"""

        private = random.randint(2, self.dh.p - 2)

        public = pow(self.dh.g, private, self.dh.p)

        return private, public



    def compute_shared(self, my_private, my_public, their_private, their_public):

        """

        计算 MQV 共享密钥。



        简化版：包含双方公私钥的混合。

        """

        # 计算 bar(x) = (x mod 2^{n/2}) + 2^{n/2}

        n = 160  # 安全参数

        p = self.dh.p



        def bar(x):

            return ((x % (1 << (n // 2))) + (1 << (n // 2))) % p



        # 计算共享值

        s = (my_private + bar(my_public) * their_private) % (p - 1)

        t = (their_private + bar(their_public) * my_private) % (p - 1)



        # 双方计算 g^{st}

        shared = pow(self.dh.g, s * t, p)

        return shared





def compare_key_exchanges():

    """对比三种密钥交换协议。"""

    print("=== 密钥交换协议对比 ===")



    # DH

    dh = DHKeyExchange()

    alice_priv_dh, alice_pub_dh = dh.generate_keypair()

    bob_priv_dh, bob_pub_dh = dh.generate_keypair()

    shared_dh_alice = dh.compute_shared(alice_priv_dh, bob_pub_dh)

    shared_dh_bob = dh.compute_shared(bob_priv_dh, alice_pub_dh)

    print(f"\n1. Diffie-Hellman:")

    print(f"   素数 p 位数: {dh.p.bit_length()}")

    print(f"   共享密钥: {shared_dh_alice}")

    print(f"   匹配: {shared_dh_alice == shared_dh_bob}")



    # ECDH

    ecdh = ECDHKeyExchange()

    alice_priv_ec, alice_pub_ec = ecdh.generate_keypair()

    bob_priv_ec, bob_pub_ec = ecdh.generate_keypair()

    shared_ec_alice = ecdh.compute_shared(alice_priv_ec, bob_pub_ec)

    shared_ec_bob = ecdh.compute_shared(bob_priv_ec, alice_pub_ec)

    print(f"\n2. ECDH:")

    print(f"   曲线位宽: {ecdh.p.bit_length()}")

    print(f"   共享密钥: {shared_ec_alice % (10**20):.0f}...")

    print(f"   匹配: {shared_ec_alice == shared_ec_bob}")



    # MQV

    mqv = MQVKeyExchange(dh)

    alice_priv_mqv, alice_pub_mqv = mqv.generate_keypair()

    bob_priv_mqv, bob_pub_mqv = mqv.generate_keypair()

    shared_mqv_alice = mqv.compute_shared(alice_priv_mqv, alice_pub_mqv, bob_priv_mqv, bob_pub_mqv)

    shared_mqv_bob = mqv.compute_shared(bob_priv_mqv, bob_pub_mqv, alice_priv_mqv, alice_pub_mqv)

    print(f"\n3. MQV:")

    print(f"   共享密钥: {shared_mqv_alice}")

    print(f"   匹配: {shared_mqv_alice == shared_mqv_bob}")



    print("\n密钥交换协议安全性对比:")

    print("  DH: 依赖离散对数问题，2048-bit RSA 等价安全")

    print("  ECDH: 256-bit ECDH ≈ 2048-bit DH")

    print("  MQV: 抗中间人攻击，双方认证")

    print("  实际选择：根据性能和安全需求选择")





if __name__ == "__main__":

    compare_key_exchanges()

