# -*- coding: utf-8 -*-

"""

算法实现：密码学协议 / srp_auth



本文件实现 srp_auth 相关的算法功能。

"""



import random

import hashlib





def is_prime(n):

    """素性测试。"""

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

    """生成大素数。"""

    while True:

        p = random.randrange(2**(bits-1), 2**bits, 2)

        if is_prime(p):

            return p





class SRPServer:

    """SRP 服务器端。"""



    def __init__(self, p, g):

        self.p = p

        self.g = g

        self.v = None  # 验证器

        self.salt = None



    def register(self, username, password, salt=None):

        """

        注册用户（存储验证器而非密码）。



        参数:

            username: 用户名

            password: 密码

            salt: 盐值（可选）

        """

        if salt is None:

            salt = random.randint(1, 2**16)



        # x = H(salt, H(username, ":", password))

        inner = f"{username}:{password}".encode()

        inner_hash = hashlib.sha256(inner).hexdigest()

        x = int(hashlib.sha256((str(salt) + inner_hash).encode()).hexdigest(), 16) % self.p



        # v = g^x mod p

        self.v = pow(self.g, x, self.p)

        self.salt = salt



        return salt, self.v



    def init_auth(self, username, A):

        """

        服务器初始化认证过程。



        参数:

            username: 用户名

            A: 客户端公钥



        返回:

            B: 服务器公钥

        """

        # 服务器选择随机数 b

        self.b = random.randint(2, self.p - 2)



        # kv = 3 * v（乘数）

        kv = (3 * self.v) % self.p



        # B = kv + g^b mod p

        g_pow_b = pow(self.g, self.b, self.p)

        self.B = (kv + g_pow_b) % self.p



        # 计算 u = H(A, B)

        self.u = int(hashlib.sha256((str(A) + str(self.B)).encode()).hexdigest(), 16) % self.p



        return self.B



    def verify(self, M1):

        """

        验证客户端的证明 M1。



        参数:

            M1: 客户端的证明



        返回:

            True/False

        """

        # 计算期望的 M1

        expected = self._compute_M1()

        return hmac.compare_digest(expected, M1)



    def _compute_M1(self):

        """计算期望的 M1。"""

        # M1 = H(A, B, S)

        S = self._compute_S()

        return hashlib.sha256((str(self.A) + str(self.B) + str(S)).encode()).digest()



    def _compute_S(self):

        """计算共享秘密 S。"""

        # S = (A * v^u)^b mod p

        base = (self.A * pow(self.v, self.u, self.p)) % self.p

        S = pow(base, self.b, self.p)

        return S





class SRPClient:

    """SRP 客户端。"""



    def __init__(self, p, g):

        self.p = p

        self.g = g

        self.A = None

        self.B = None

        self.u = None

        self.S = None



    def init_auth(self, username, password, salt, server_B):

        """

        客户端初始化认证。



        参数:

            username: 用户名

            password: 密码

            salt: 服务器提供的盐

            server_B: 服务器公钥



        返回:

            A: 客户端公钥

        """

        # 客户端选择随机数 a

        self.a = random.randint(2, self.p - 2)



        # A = g^a mod p

        self.A = pow(self.g, self.a, self.p)



        self.B = server_B



        # 计算 u

        self.u = int(hashlib.sha256((str(self.A) + str(self.B)).encode()).hexdigest(), 16) % self.p



        # 计算 x

        inner = f"{username}:{password}".encode()

        inner_hash = hashlib.sha256(inner).hexdigest()

        x = int(hashlib.sha256((str(salt) + inner_hash).encode()).hexdigest(), 16) % self.p



        # 计算 S

        g_pow_x = pow(self.g, x, self.p)

        k = int(hashlib.sha256((str(self.p) + str(self.g)).encode()).hexdigest(), 16) % self.p

        base = (g_pow_x * k) % self.p

        self.S = pow(base, self.a, self.p)



        return self.A



    def compute_proof(self, username):

        """计算客户端证明 M1。"""

        # M1 = H(H(g)^H(password), H(username), salt, A, B, S)

        inner = f"{username}:".encode() + hashlib.sha256(b"password").digest()

        x = int(hashlib.sha256(inner).hexdigest(), 16) % self.p

        g_pow_x = pow(self.g, x, self.p)



        inner2 = hashlib.sha256(str(self.g).encode()).hexdigest()

        g_hash = int(inner2, 16) % self.p



        h_user = hashlib.sha256(username.encode()).hexdigest()



        data = str(g_pow_x) + str(h_user) + str(self.salt) + str(self.A) + str(self.B) + str(self.S)

        M1 = hashlib.sha256(data.encode()).digest()



        return M1



    def set_salt(self, salt):

        """设置盐值（从服务器获取）。"""

        self.salt = salt





def simulate_srp():

    """模拟 SRP 认证过程。"""

    print("=== SRP 协议模拟 ===")



    # 公共参数

    p = generate_prime(16)

    g = 2



    username = "alice"

    password = "secret123"



    # 服务器注册

    server = SRPServer(p, g)

    salt, v = server.register(username, password)

    print(f"用户注册成功")

    print(f"  盐: {salt}")

    print(f"  验证器（存储在服务器）: {v}")



    # 客户端初始化

    client = SRPClient(p, g)



    # 服务器初始化认证

    A = random.randint(2, p - 2)  # 模拟客户端公钥

    # 实际中客户端计算 A = g^a mod p

    A = pow(g, random.randint(2, p - 2), p)



    client_a = random.randint(2, p - 2)

    A_actual = pow(g, client_a, p)



    B = server.init_auth(username, A_actual)



    # 客户端计算

    client.A = A_actual

    client.B = B

    client.u = int(hashlib.sha256((str(A_actual) + str(B)).encode()).hexdigest(), 16) % p



    # 计算 S（简化版本）

    inner = f"{username}:{password}".encode()

    inner_hash = hashlib.sha256(inner).hexdigest()

    x = int(hashlib.sha256((str(salt) + inner_hash).encode()).hexdigest(), 16) % p



    k = int(hashlib.sha256((str(p) + str(g)).encode()).hexdigest(), 16) % p

    g_pow_x = pow(g, x, p)

    base = (g_pow_x * k) % p

    S_client = pow(base, client_a, p)



    # 服务器验证（简化）

    print(f"\n认证过程:")

    print(f"  客户端公钥 A: {A_actual}")

    print(f"  服务器公钥 B: {B}")

    print(f"  共享秘密 S: {S_client}")



    # 实际中通过 M1/M2 验证

    print(f"  客户端生成证明 M1")

    print(f"  服务器验证 M1")



    print(f"\nSRP 安全性:")

    print("  1. 服务器不存储明文密码，只存储验证器")

    print("  2. 密码从未在网络上传输")

    print("  3. 即使验证器泄露，攻击者也无法冒充用户（需要破解离散对数）")





if __name__ == "__main__":

    simulate_srp()



    print("\nSRP 协议要点:")

    print("  零知识风格：客户端证明知道密码，但不暴露密码")

    print("  抗字典攻击：每次注册使用随机盐")

    print("  前向安全：长期密钥泄露不影响已建立的会话")

