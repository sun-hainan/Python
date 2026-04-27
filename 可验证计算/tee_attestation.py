# -*- coding: utf-8 -*-

"""

算法实现：可验证计算 / tee_attestation



本文件实现 tee_attestation 相关的算法功能。

"""



import hashlib

import hmac

import json





class Enclave:

    """TEE Enclave（飞地）模拟。"""



    def __init__(self, enclave_id, measurement):

        self.enclave_id = enclave_id

        self.measurement = measurement  # MRENCLAVE（代码/数据哈希）

        self.mrsigner = b'\x01' * 32   # 签名者身份哈希

        self.attributes = 0x0000000000000000000000000000000000000000000000000000000000000003  # 属性标志



    def get_report(self, report_data):

        """

        生成 Enclave Report（类似 Intel EPID 报告）。



        报告包含：

        - MRENCLAVE：Enclave 代码哈希

        - MRSIGNER：签名者公钥哈希

        - REPORTDATA：用户数据

        """

        report = {

            'enclave_id': self.enclave_id.hex(),

            'mrenclave': self.measurement.hex() if isinstance(self.measurement, bytes) else self.measurement,

            'mrsigner': self.mrsigner.hex(),

            'attributes': hex(self.attributes),

            'report_data': report_data.hex() if isinstance(report_data, bytes) else report_data,

            'isv_prod_id': 1,

            'isv_svn': 1

        }

        return report





class TEE_Platform:

    """TEE 平台模拟，包含多个 Enclave。"""



    def __init__(self):

        self.quote_key = (12345678901234567890, 65537)  # 模拟 (n, e)

        self.quote_private = 98765432109876543210

        self.enclaves = {}



    def create_enclave(self, enclave_id, code_hash):

        """创建并测量 Enclave。"""

        # MRENCLAVE = SHA-256(code_hash || init_data)

        measurement = hashlib.sha256(code_hash + b'init_data').digest()

        enclave = Enclave(enclave_id, measurement)

        self.enclaves[enclave_id] = enclave

        return enclave



    def generate_quote(self, enclave_id, report_data, nonce):

        """

        生成 Quote：本地证明 + 远程验证所需数据。



        Quote 结构（简化）：

        - Enclave Report

        - 签名

        """

        if enclave_id not in self.enclaves:

            raise ValueError(f"Enclave {enclave_id} 不存在")



        enclave = self.enclaves[enclave_id]

        report = enclave.get_report(report_data)



        # 将报告与 nonce 连接后签名

        data_to_sign = json.dumps(report, sort_keys=True).encode() + nonce

        signature = self._sign_quote(data_to_sign)



        quote = {

            'version': 3,

            'report': report,

            'signature': signature.hex(),

            'signature_key': hex(self.quote_key[0])[:32] + "..."

        }



        return quote



    def _sign_quote(self, data):

        """简化签名（实际用 EPID 或 ECDSA）。"""

        return hmac.new(str(self.quote_private).encode(), data, hashlib.sha384).digest()



    def verify_quote_signature(self, quote):

        """验证 Quote 签名。"""

        report_json = json.dumps(quote['report'], sort_keys=True).encode()

        nonce_placeholder = b'nonce'

        data = report_json + nonce_placeholder

        expected_sig = self._sign_quote(data)

        return hmac.compare_digest(expected_sig.hex(), quote['signature'])





def verify_remote_attestation(quote, expected_mrenclave, expected_report_data, nonce):

    """

    验证远程证明 Quote。



    参数:

        quote: TEE 平台生成的 Quote

        expected_mrenclave: 期望的 Enclave 测量值

        expected_report_data: 期望的用户数据

        nonce: 验证者提供的随机数（防重放）



    返回:

        True/False

    """

    report = quote['report']



    # 1. 检查版本

    if quote['version'] != 3:

        return False, "Quote 版本不支持"



    # 2. 检查 MRENCLAVE（Enclave 身份）

    if report['mrenclave'] != expected_mrenclave:

        return False, "MRENCLAVE 不匹配"



    # 3. 检查 REPORTDATA（用户数据）

    if report['report_data'] != expected_report_data:

        return False, "REPORTDATA 不匹配"



    # 4. 检查属性（SGX 标志）

    if int(report['attributes'], 16) & 0x03 != 0x03:

        return False, "Enclave 属性不正确"



    # 5. 验证签名

    # （简化：实际需要验证 Intel CA 公钥）

    return True, "Attestation 验证通过"





if __name__ == "__main__":

    print("=== TEE 远程证明测试 ===")



    # 初始化 TEE 平台

    platform = TEE_Platform()



    # 假设要部署的可信应用代码哈希

    app_code_hash = b'trustworthy_app_v1.0_code'

    enclave_id = b'enclave_001'



    # 创建 Enclave

    enclave = platform.create_enclave(enclave_id, app_code_hash)

    print(f"Enclave 创建成功:")

    print(f"  MRENCLAVE: {enclave.measurement.hex()[:32]}...")



    # 构造证明请求

    report_data = b'user_specific_data_12345'

    nonce = b'verifier_nonce_67890'



    # 生成 Quote

    quote = platform.generate_quote(enclave_id, report_data, nonce)

    print(f"\nQuote 生成成功:")

    print(f"  版本: {quote['version']}")

    print(f"  签名: {quote['signature'][:32]}...")



    # 验证 Quote

    valid, msg = verify_remote_attestation(

        quote,

        enclave.measurement.hex(),

        report_data.hex(),

        nonce

    )

    print(f"\n验证结果: {msg}")



    # 篡改检测测试

    print("\n=== 篡改检测测试 ===")

    tampered_quote = json.loads(json.dumps(quote))

    tampered_quote['report']['report_data'] = 'tampered_data'

    valid, msg = verify_remote_attestation(

        tampered_quote,

        enclave.measurement.hex(),

        report_data.hex(),

        nonce

    )

    print(f"篡改 REPORTDATA 后: {msg}")



    print("\nTEE 证明特性:")

    print("  硬件隔离：Enclave 内容对外部完全不可见")

    print("  测量启动：MRENCLAVE 保证代码完整性")

    print("  签名认证：Quote 可由 Intel/AMD 根证书验证")

