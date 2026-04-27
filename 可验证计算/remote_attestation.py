# -*- coding: utf-8 -*-

"""

算法实现：可验证计算 / remote_attestation



本文件实现 remote_attestation 相关的算法功能。

"""



import hashlib

import hmac

import json





class TPMSimulator:

    """

    TPM 模拟器：管理平台配置寄存器（PCR）和身份密钥（AIK）。

    """



    def __init__(self):

        # 平台配置寄存器（测量值）

        self.pcr = [b'\x00' * 32 for _ in range(16)]



        # 身份密钥对（简化）

        self.aik_private = 12345

        self.aik_public = 67890



        # AIK 证书（简化，由 CA 签发）

        self.aik_certificate = self._sign_aik_cert()



    def extend_pcr(self, index, data):

        """

        扩展 PCR：将新测量值与当前 PCR 值连接后哈希。



        这是 TPM 的核心特性：只能追加，无法篡改历史测量。

        """

        current = self.pcr[index]

        new_value = hashlib.sha256(current + data).digest()

        self.pcr[index] = new_value

        return new_value



    def quote(self, challenge):

        """

        生成 Quote：签名当前 PCR 值，证明平台状态。



        参数:

            challenge: 验证者提供的随机挑战



        返回:

            quote: 包含 PCR 值和签名的数据结构

        """

        # 选择要签名的 PCR（通常选择 PCR[0-16]）

        pcr_select = self.pcr[:]



        # 将 PCR 值和挑战连接后签名

        data_to_sign = b''.join(pcr_select) + challenge

        signature = self._sign(data_to_sign, self.aik_private)



        quote = {

            'pcr_values': [pcr.hex() for pcr in pcr_select],

            'challenge': challenge.hex(),

            'signature': signature,

            'aik_public': self.aik_public,

            'aik_certificate': self.aik_certificate

        }



        return quote



    def _sign(self, data, key):

        """简化签名：使用 HMAC 代替 RSA。"""

        return hmac.new(str(key).encode(), data, hashlib.sha256).hexdigest()



    def _sign_aik_cert(self):

        """生成 AIK 证书（简化）。"""

        cert_data = f"AIK:{self.aik_public}".encode()

        return self._sign(cert_data, 'ca_private_key')





def verify_quote(quote, expected_pcrs, expected_challenge):

    """

    验证远程证明 Quote。



    参数:

        quote: TPM 返回的 Quote 数据结构

        expected_pcrs: 期望的 PCR 值列表

        expected_challenge: 期望的挑战值



    返回:

        True/False

    """

    # 1. 验证 AIK 证书（简化）

    expected_cert = hmac.new(

        'ca_private_key'.encode(),

        f"AIK:{quote['aik_public']}".encode(),

        hashlib.sha256

    ).hexdigest()

    if quote['aik_certificate'] != expected_cert:

        return False, "AIK 证书无效"



    # 2. 验证挑战值

    if quote['challenge'] != expected_challenge.hex():

        return False, "挑战值不匹配"



    # 3. 验证 PCR 值

    for i, (expected, actual) in enumerate(zip(expected_pcrs, quote['pcr_values'])):

        if expected.hex() != actual:

            return False, f"PCR[{i}] 不匹配"



    # 4. 验证签名

    pcr_data = b''.join(pcr.encode() for pcr in quote['pcr_values'])

    data_to_verify = pcr_data + expected_challenge

    expected_sig = hmac.new(

        str(quote['aik_public']).encode(),

        data_to_verify,

        hashlib.sha256

    ).hexdigest()

    if expected_sig != quote['signature']:

        return False, "签名验证失败"



    return True, "验证通过"





if __name__ == "__main__":

    print("=== 远程证明测试 ===")



    # 模拟 TPM

    tpm = TPM_Simulator()



    # 模拟平台启动：测量引导加载程序、内核等

    boot_measurements = [

        b'bootloader_v1.0',

        b'kernel_v5.10',

        b'initramfs',

        b'secure_os'

    ]



    print("平台启动测量:")

    for i, measurement in enumerate(boot_measurements):

        new_val = tpm.extend_pcr(0, measurement)

        print(f"  PCR[0] <- {measurement.decode()}: {new_val.hex()[:16]}...")



    # 验证者发起挑战

    challenge = b'verifier_nonce_12345'

    print(f"\n验证者挑战: {challenge.hex()[:20]}...")



    # TPM 生成 Quote

    quote = tpm.quote(challenge)

    print(f"\nQuote 生成成功:")

    print(f"  PCR[0] 值: {quote['pcr_values'][0][:16]}...")

    print(f"  签名: {quote['signature'][:16]}...")



    # 验证者验证 Quote

    expected_pcrs = tpm.pcr[:]

    valid, msg = verify_quote(quote, expected_pcrs, challenge)

    print(f"\n验证结果: {msg}")



    # 模拟篡改：修改 PCR 值

    print("\n=== 篡改检测测试 ===")

    tampered_quote = quote.copy()

    tampered_quote['pcr_values'][0] = 'tampered'.ljust(64, '0')

    valid, msg = verify_quote(tampered_quote, expected_pcrs, challenge)

    print(f"篡改后验证结果: {msg}")



    print("\n远程证明特性:")

    print("  可信启动：每步引导都测量并扩展 PCR")

    print("  不可伪造：只有 TPM 硬件能生成有效签名")

    print("  抗篡改：PCR 只可扩展，无法重置")

