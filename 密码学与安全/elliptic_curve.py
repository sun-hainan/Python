# -*- coding: utf-8 -*-

"""

算法实现：密码学与安全 / elliptic_curve



本文件实现 elliptic_curve 相关的算法功能。

"""



import random

import hashlib

from typing import Tuple, Optional





class FiniteField:

    """有限域算术"""



    def __init__(self, p: int):

        """

        初始化有限域 GF(p)



        参数：

            p: 素数模数

        """

        self.p = p



    def add(self, a: int, b: int) -> int:

        """

        有限域加法



        参数：

            a, b: 操作数



        返回：(a + b) mod p

        """

        return (a + b) % self.p



    def sub(self, a: int, b: int) -> int:

        """

        有限域减法



        参数：

            a, b: 操作数



        返回：(a - b) mod p

        """

        return (a - b) % self.p



    def mul(self, a: int, b: int) -> int:

        """

        有限域乘法



        参数：

            a, b: 操作数



        返回：(a * b) mod p

        """

        return (a * b) % self.p



    def inv(self, a: int) -> int:

        """

        有限域乘法逆元



        参数：

            a: 操作数



        返回：a^(-1) mod p（使用扩展欧几里得算法）

        """

        if a == 0:

            raise ValueError("零没有逆元")



        # 扩展欧几里得算法

        old_r, r = self.p, a

        old_s, s = 0, 1



        while r != 0:

            quotient = old_r // r

            old_r, r = r, old_r - quotient * r

            old_s, s = s, old_s - quotient * s



        # s是a的逆元

        if old_s < 0:

            old_s += self.p



        return old_s



    def div(self, a: int, b: int) -> int:

        """

        有限域除法



        参数：

            a, b: 操作数



        返回：(a * b^(-1)) mod p

        """

        return self.mul(a, self.inv(b))





class EllipticCurve:

    """椭圆曲线"""



    # secp256k1曲线参数（比特币使用）

    CURVE_PARAMS = {

        'p': 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F,  # 素数模数

        'a': 0x0000000000000000000000000000000000000000000000000000000000000000,  # 曲线参数a

        'b': 0x0000000000000000000000000000000000000000000000000000000000000007,  # 曲线参数b

        'n': 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141,  # 基点的阶

        'gx': 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,  # 基点x坐标

        'gy': 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8,  # 基点y坐标

    }



    def __init__(self, name: str = 'secp256k1'):

        """

        初始化椭圆曲线



        参数：

            name: 曲线名称

        """

        params = self.CURVE_PARAMS

        self.field = FiniteField(params['p'])

        self.a = params['a']

        self.b = params['b']

        self.n = params['n']

        self.gx = params['gx']

        self.gy = params['gy']

        self.name = name



    def is_on_curve(self, x: int, y: int) -> bool:

        """

        检查点是否在曲线上



        参数：

            x, y: 点坐标



        返回：是否在曲线上

        """

        if x == 0 and y == 0:

            return True  # 无穷远点



        left = self.field.mul(y, y)  # y^2

        right = self.field.add(

            self.field.add(

                self.field.mul(x, self.field.mul(x, x)),  # x^3

                self.field.mul(self.a, x)  # a*x

            ),

            self.b  # + b

        )



        return left == right



    def point_add(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> Tuple[int, int]:

        """

        椭圆曲线点加法



        参数：

            p1, p2: 两个点的坐标 (x, y)



        返回：p1 + p2 的结果

        """

        x1, y1 = p1

        x2, y2 = p2



        # 无穷远点处理

        if x1 == 0 and y1 == 0:

            return p2

        if x2 == 0 and y2 == 0:

            return p1



        # 如果p1 = -p2（x相同，y相反），返回无穷远点

        if x1 == x2 and self.field.add(y1, y2) == 0:

            return (0, 0)



        # 计算斜率

        if p1 == p2:

            # 点倍增：lam = (3*x1^2 + a) / (2*y1)

            numerator = self.field.add(

                self.field.mul(3, self.field.mul(x1, x1)),

                self.a

            )

            denominator = self.field.mul(2, y1)

        else:

            # 点加法：lam = (y2 - y1) / (x2 - x1)

            numerator = self.field.sub(y2, y1)

            denominator = self.field.sub(x2, x1)



        lam = self.field.div(numerator, denominator)



        # 计算结果点

        x3 = self.field.sub(

            self.field.sub(

                self.field.mul(lam, lam),

                x1

            ),

            x2

        )

        y3 = self.field.sub(

            self.field.mul(lam, self.field.sub(x1, x3)),

            y1

        )



        return (x3, y3)



    def scalar_mul(self, k: int, point: Tuple[int, int]) -> Tuple[int, int]:

        """

        标量乘法：k * P（使用二进制算法）



        参数：

            k: 标量（私钥）

            point: 基点P



        返回：k * P

        """

        result = (0, 0)  # 无穷远点

        addend = point



        while k:

            if k & 1:

                result = self.point_add(result, addend)

            addend = self.point_add(addend, addend)  # 2P

            k >>= 1



        return result



    def generate_keypair(self) -> Tuple[int, Tuple[int, int]]:

        """

        生成密钥对



        返回：(私钥, 公钥)

        """

        # 私钥：随机数

        private_key = random.randint(1, self.n - 1)



        # 公钥：私钥 * 基点

        public_key = self.scalar_mul(private_key, (self.gx, self.gy))



        return private_key, public_key



    def sign(self, message: bytes, private_key: int) -> Tuple[int, int]:

        """

        ECDSA签名



        参数：

            message: 待签名消息

            private_key: 私钥



        返回：(r, s) 签名

        """

        # 计算消息哈希

        e = int(hashlib.sha256(message).hexdigest(), 16)



        # 随机nonce

        k = random.randint(1, self.n - 1)



        # R = k * G

        r_point = self.scalar_mul(k, (self.gx, self.gy))

        r = r_point[0] % self.n



        if r == 0:

            raise ValueError("签名失败：r=0")



        # s = k^(-1) * (e + r * private_key) mod n

        s = self.field.mul(

            self.field.inv(k),

            self.field.add(e, self.field.mul(r, private_key))

        ) % self.n



        if s == 0:

            raise ValueError("签名失败：s=0")



        return (r, s)



    def verify(self, message: bytes, signature: Tuple[int, int], public_key: Tuple[int, int]) -> bool:

        """

        ECDSA验证



        参数：

            message: 消息

            signature: (r, s)

            public_key: 公钥



        返回：验证结果

        """

        r, s = signature



        if not (1 <= r < self.n and 1 <= s < self.n):

            return False



        e = int(hashlib.sha256(message).hexdigest(), 16)



        w = self.field.inv(s) % self.n

        u1 = self.field.mul(e, w) % self.n

        u2 = self.field.mul(r, w) % self.n



        point = self.point_add(

            self.scalar_mul(u1, (self.gx, self.gy)),

            self.scalar_mul(u2, public_key)

        )



        v = point[0] % self.n



        return v == r





def ecc_applications():

    """ECC应用场景"""

    print("=== ECC应用场景 ===")

    print()

    print("1. 区块链")

    print("   - 比特币：secp256k1曲线")

    print("   - 以太坊：相同曲线")

    print()

    print("2. TLS/SSL")

    print("   - ECDHE密钥交换")

    print("   - TLS 1.3默认使用")

    print()

    print("3. 数字签名")

    print("   - ECDSA（美国政府标准）")

    print("   - EdDSA（Ed25519）")

    print()

    print("4. 轻量级设备")

    print("   - 智能卡、物联网")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 椭圆曲线密码学测试 ===\n")



    # 创建曲线

    curve = EllipticCurve('secp256k1')



    print(f"曲线: {curve.name}")

    print(f"素数模数: {hex(curve.p)}")

    print(f"基点: ({hex(curve.gx)[:32]}..., {hex(curve.gy)[:32]}...)")

    print()



    # 检查基点是否在曲线上

    on_curve = curve.is_on_curve(curve.gx, curve.gy)

    print(f"基点在曲线上: {'是' if on_curve else '否'}")

    print()



    # 生成密钥对

    private_key, public_key = curve.generate_keypair()



    print("密钥生成：")

    print(f"  私钥: {hex(private_key)[:32]}...")

    print(f"  公钥: ({hex(public_key[0])[:32]}..., {hex(public_key[1])[:32]}...)")

    print()



    # 公钥验证

    computed_pub = curve.scalar_mul(private_key, (curve.gx, curve.gy))

    pub_valid = (computed_pub[0] == public_key[0] and computed_pub[1] == public_key[1])

    print(f"公钥正确性验证: {'通过' if pub_valid else '失败'}")

    print()



    # 签名测试

    message = b"Hello, ECC!"



    signature = curve.sign(message, private_key)



    print("签名测试：")

    print(f"  消息: {message.decode()}")

    print(f"  签名: (r={hex(signature[0])[:16]}..., s={hex(signature[1])[:16]}...)")

    print()



    # 验证签名

    valid = curve.verify(message, signature, public_key)

    print(f"签名验证: {'通过' if valid else '失败'}")

    print()



    # 篡改检测

    tampered_message = b"Hello, ECC?X"

    tampered_valid = curve.verify(tampered_message, signature, public_key)

    print(f"篡改消息验证: {'通过' if tampered_valid else '失败（预期）'}")

    print()



    # 应用场景

    ecc_applications()



    print()

    print("说明：")

    print("  - ECC用更短的密钥提供同等安全")

    print("  - 160位ECC ≈ 1024位RSA")

    print("  - 广泛用于现代加密系统")

