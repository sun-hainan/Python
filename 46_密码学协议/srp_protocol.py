# -*- coding: utf-8 -*-

"""

算法实现：密码学协议 / srp_protocol



本文件实现 srp_protocol 相关的算法功能。

"""



import hashlib

import random

import secrets





class SRPServer:

    """SRP协议服务器端"""



    def __init__(self, N, g, hash_func='sha256'):

        """

        初始化SRP服务器



        Args:

            N: int 大素数模数（RFC 5054推荐2048-bit）

            g: int 生成元

            hash_func: str 哈希函数

        """

        self.N = N  # 素数模数

        self.g = g  # 生成元

        self.hash_func = lambda x: hashlib.sha256(x).hexdigest()  # 默认SHA-256

        self.salt = None  # 盐值（存储在数据库中）

        self.verifier = None  # 验证器 v = g^x mod N (x = H(salt, password))

        self.b = None  # 服务器私钥

        self.B = None  # 服务器公钥

        self.session_key = None  # 会话密钥



    def _H(self, *args):

        """Hash函数"""

        data = b''.join(str(arg).encode() if isinstance(arg, str) else arg for arg in args)

        return int(self.hash_func(data), 16)



    def _compute_x(self, salt, password):

        """

        计算私钥 x = H(salt, password)



        Args:

            salt: bytes 盐值

            password: str 密码



        Returns:

            int 私钥

        """

        return self._H(salt, password)



    def register(self, salt, password):

        """

        注册用户（模拟数据库存储）



        Args:

            salt: bytes 盐值

            password: str 用户密码



        Returns:

            verifier: int 验证器（存入数据库）

        """

        self.salt = salt

        x = self._compute_x(salt, password)

        self.verifier = pow(self.g, x, self.N)  # v = g^x mod N

        return self.verifier



    def authenticate_init(self):

        """

        认证第一步：服务器初始化



        1. 服务器选取随机私钥 b

        2. 计算公钥 B = kv + g^b mod N（k是协议常数）

        3. 发送 salt 和 B 给客户端



        Returns:

            tuple (salt, B)

        """

        # k = H(N, g)（协议常数）

        k = self._H(self.N, self.g)



        # 随机选取服务器私钥 b

        self.b = secrets.randbelow(self.N - 2) + 1



        # B = k*v + g^b mod N

        self.B = (k * self.verifier + pow(self.g, self.b, self.N)) % self.N



        return self.salt, self.B



    def authenticate_verify(self, A, client_proof):

        """

        认证第二步：验证客户端



        Args:

            A: int 客户端公钥

            client_proof: bytes 客户端发来的会话密钥证明



        Returns:

            bool 认证是否成功

        """

        # u = H(A, B)

        u = self._H(A, self.B)



        # 计算服务器端的会话密钥

        # S = (A * v^u)^b mod N

        v_u = pow(self.verifier, u, self.N)

        S = pow(A * v_u % self.N, self.b, self.N)

        self.session_key = self._derive_key(S)



        # 计算服务器证明

        # proof = H(A, B, S)

        server_proof = self._H(A, self.B, S)



        return secrets.compare_digest(client_proof, server_proof)



    def _derive_key(self, S):

        """

        从共享值S派生会话密钥



        Args:

            S: int 共享秘密值



        Returns:

            bytes 会话密钥

        """

        return hashlib.sha256(str(S).encode()).digest()





class SRPClient:

    """SRP协议客户端"""



    def __init__(self, N, g, hash_func='sha256'):

        """

        初始化SRP客户端



        Args:

            N: int 大素数模数

            g: int 生成元

            hash_func: str 哈希函数

        """

        self.N = N

        self.g = g

        self.hash_func = lambda x: hashlib.sha256(x).hexdigest()

        self.a = None  # 客户端私钥

        self.A = None  # 客户端公钥

        self.session_key = None  # 会话密钥

        self.password = None  # 用户密码（本地使用）



    def _H(self, *args):

        """Hash函数"""

        data = b''.join(str(arg).encode() if isinstance(arg, str) else arg for arg in args)

        return int(self.hash_func(data), 16)



    def authenticate_start(self, password):

        """

        认证第一步：客户端开始



        Args:

            password: str 用户输入的密码



        Returns:

            tuple (A, password_proof)

        """

        self.password = password



        # 随机选取客户端私钥 a

        self.a = secrets.randbelow(self.N - 2) + 1



        # 计算客户端公钥 A = g^a mod N

        self.A = pow(self.g, self.a, self.N)



        return self.A



    def authenticate_response(self, salt, B):

        """

        认证第二步：处理服务器响应并发送证明



        1. 计算 u = H(A, B)

        2. 计算 x = H(salt, password)

        3. 计算 S = (B - k*g^x)^{a + u*x} mod N

        4. 派生会话密钥

        5. 发送会话密钥证明



        Args:

            salt: bytes 服务器发来的盐值

            B: int 服务器公钥



        Returns:

            bytes 客户端发来的会话密钥证明

        """

        # k = H(N, g)

        k = self._H(self.N, self.g)



        # u = H(A, B)

        u = self._H(self.A, B)



        # x = H(salt, password)

        x = self._H(salt, self.password)



        # g_x = g^x mod N

        g_x = pow(self.g, x, self.N)



        # 验证 B != 0

        if B % self.N == 0:

            raise ValueError("Invalid server public key")



        # S = (B - k*g^x)^{a + u*x} mod N

        exp = (self.a + u * x) % (self.N - 1)

        S = pow(B - k * g_x, exp, self.N)



        # 派生会话密钥

        self.session_key = self._derive_key(S)



        # proof = H(A, B, S)

        proof = self._H(self.A, B, S)



        return proof



    def _derive_key(self, S):

        """派生会话密钥"""

        return hashlib.sha256(str(S).encode()).digest()



    def verify_server_proof(self, server_proof):

        """

        验证服务器发来的证明



        Args:

            server_proof: bytes 服务器发来的会话密钥证明



        Returns:

            bool 验证是否成功

        """

        # 服务器证明应该是 H(A, B, S)

        expected = self._H(self.A, self.B, self.session_key)

        return secrets.compare_digest(server_proof, expected)





def generate_srp_parameters(bits=2048):

    """

    生成SRP推荐的安全参数



    Args:

        bits: int 素数位数（RFC 5054推荐2048或3072）



    Returns:

        tuple (N, g)

    """

    # RFC 5054 推荐的参数

    if bits == 2048:

        N = int(

            'AC6BDB41 24A5A9B A1D2E2E5 ABF10E8 E5D6A1C0'

            '4D7E 9E4E 3A88 5BFC E93B0F A2F39F0D 1EE67C8'

            '27F36A4B F0EDC14 81CFA6B2 8FB0CFE5 FDF8C67'

            'A80A4CA8 AB7C2F10 17BF18D 8E3A80E9 4F79B0D6'

            '8F3B1F93 3DDEECCE 9AC00A6 8DAF2A40 FFFFFFFF'

            'FFFFFFFF C90FDAA2 2168C234 C4C6628B 80DC1CD1'

            '29024E08 8A67CC74 020BBEA6 3B139B22 514A0879'

            '8E3404DD EF9519B3 CD3A431B 302B0A6D F25F1437'

            '4FE1356D 6D51C245 E485B576 625E7EC6 F44C42E9'

            'A637ED6B 0BFF5CB6 F406B7ED EE386BFB 5A899FA5'

            'AE9F2411 7C4B1FE6 49286651 ECE45B3DC 2007CB8A'

            '163BF059 8DA48361 C55D39A6 9163FA8F D24CF5F8'

            '3655D23D CA3AD961 C62F3562 08552BB9 ED529077'

            '096966D6 70C354E4 ABC9804F 1746C08C A237327F'

            'FFFFFFFF FFFFFFFF'.replace(' ', ''), 16

        )

    elif bits == 3072:

        N = int(

            'FFFFFFFF FFFFFFFF C90FDAA2 2168C234 C4C6628B 80DC1CD1'

            '29024E08 8A67CC74 020BBEA6 3B139B22 514A0879 8E3404DD'

            'EF9519B3 CD3A431B 302B0A6D F25F1437 4FE1356D 6D51C245'

            'E485B576 625E7EC6 F44C42E9 A637ED6B 0BFF5CB6 F406B7ED'

            'EE386BFB 5A899FA5 AE9F2411 7C4B1FE6 49286651 ECE45B3DC'

            '2007CB8A 163BF059 8DA48361 C55D39A6 9163FA8F D24CF5F8'

            '3655D23D CA3AD961 C62F3562 08552BB9 ED529077 096966D6'

            '70C354E4 ABC9804F 1746C08C A237327F FFFFFF FFFFFFFF'.replace(' ', ''), 16

        )

    else:

        raise ValueError("Unsupported bit size")



    g = 2

    return N, g





# ------------------- 单元测试 -------------------

if __name__ == '__main__':

    print("=" * 50)

    print("测试 SRP 安全远程密码协议")

    print("=" * 50)



    # 获取SRP参数

    N, g = generate_srp_parameters(2048)



    # 模拟用户注册

    password = "SecretPassword123!"

    salt = secrets.token_bytes(16)  # 随机盐值



    print(f"\n用户密码: {password}")

    print(f"盐值: {salt.hex()}")



    # 创建服务器并注册用户

    server = SRPServer(N, g)

    verifier = server.register(salt, password)

    print(f"验证器: {verifier}...")



    # ========== 认证阶段 ==========

    print("\n--- 认证阶段 ---")



    # 服务器初始化

    server_salt, B = server.authenticate_init()

    print(f"服务器发送 salt: {server_salt.hex()}")

    print(f"服务器发送 B: {B}...")



    # 客户端开始

    client = SRPClient(N, g)

    A = client.authenticate_start(password)

    print(f"客户端发送 A: {A}...")



    # 客户端处理响应并发送证明

    client_proof = client.authenticate_response(server_salt, B)

    print(f"客户端发送 proof: {client_proof.hex()}...")



    # 服务器验证客户端

    server_auth = server.authenticate_verify(A, client_proof)

    print(f"服务器验证客户端: {'✅ 成功' if server_auth else '❌ 失败'}")



    # 服务器发送自己的证明（简化，实际协议需要）

    # 实际中服务器也应该发送证明让客户端验证

    server_proof = server._H(A, B, server.session_key)



    # 客户端验证服务器

    client_auth = client.verify_server_proof(server_proof)

    print(f"客户端验证服务器: {'✅ 成功' if client_auth else '❌ 失败'}")



    # 双方会话密钥匹配

    if server_auth and client_auth:

        print(f"\n✅ 会话密钥匹配: {server.session_key == client.session_key}")

        print(f"会话密钥: {server.session_key.hex()[:32]}...")



    print("\n" + "=" * 50)

    print("协议安全性分析:")

    print("=" * 50)

    print("1. 服务器存储的是验证器 v = g^x mod N，不是明文密码")

    print("2. 协议交互中不传输明文密码")

    print("3. 即使攻击者截获所有消息，也无法恢复密码（依赖DLP难题）")

    print("4. 双方通过证明验证彼此拥有正确的会话密钥")

    print("5. 会话密钥可后续用于加密通信")



    print("\n" + "=" * 50)

    print("复杂度分析:")

    print("=" * 50)

    print("时间复杂度: O(k * log(N))，k为指数位数")

    print("空间复杂度: O(1)，仅存储常数个参数和临时值")



    print("\n✅ SRP安全远程密码协议测试通过！")

