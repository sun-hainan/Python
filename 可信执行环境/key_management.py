# -*- coding: utf-8 -*-

"""

算法实现：可信执行环境 / key_management



本文件实现 key_management 相关的算法功能。

"""



# ============================================================================

# 第一部分：密封密钥核心概念

# ============================================================================



# sealed_key_definition（密封密钥定义）

sealed_key_definition = {

    "sealed_key": "使用TEE硬件密钥加密（密封）的密钥，可安全存储在非信任存储",

    "unsealing": "解封过程只能在Enclave内完成，使用TEE硬件密钥解密",

    "purpose": "实现持久化存储：密钥离开Enclave后仍受TEE保护",

    "hardware_root": "密钥源自CPU内部，无法通过物理访问提取"

}



# ============================================================================

# 第二部分：密封策略

# ============================================================================



# sealing_policy（密封策略）：决定密钥与哪种身份绑定

sealing_policy = {

    "MRENCLAVE": {

        "name": "Enclave内容绑定",

        "description": "密钥只能被相同代码度量值的Enclave解封",

        "use_case": "同一应用、同一版本的密钥管理",

        "pros": "精确控制，只有完全相同的代码能访问",

        "cons": "代码升级后密钥无法使用（需要迁移）"

    },

    "MRSIGNER": {

        "name": "签名者绑定",

        "description": "密钥可被同一签名者签名的任何Enclave解封",

        "use_case": "应用升级后仍需访问原有密钥",

        "pros": "支持应用升级，版本兼容性更好",

        "cons": "签名者下的所有Enclave都能解封，粒度较粗"

    }

}



# ============================================================================

# 第三部分：密封数据结构

# ============================================================================



# sealed_data_structure（密封数据结构）

sealed_data_structure = {

    "key_id": "密钥标识符（用于密钥派生）",

    "key_policy": "密封策略（MRENCLAVE或MRSIGNER）",

    "seal_key": "密封密钥（使用Seal Key加密）",

    "metadata": "版本号、创建时间、算法标识等",

    "mac": "完整性校验码"

}



# ============================================================================

# 第四部分：密钥密封流程

# ============================================================================



# seal_key_flow（密封密钥的完整流程）

def seal_key_flow(enclave_identity, secret_key, policy="MRENCLAVE"):

    """

    模拟密钥密封流程

    

    Args:

        enclave_identity: Enclave身份度量值

        secret_key: 要密封的密钥（原始密钥）

        policy: 密封策略

    

    Returns:

        dict: 密封后的数据结构

    """

    import secrets

    import hashlib

    import base64

    

    # 生成密钥标识符

    key_id = secrets.token_hex(16)

    

    # 生成密封密钥（模拟使用EGETKEY获取Seal Key）

    seal_key_material = f"{enclave_identity}{policy}{secret_key}"

    seal_key = hashlib.sha256(seal_key_material.encode()).digest()

    

    # 模拟加密：使用Seal Key加密原始密钥

    encrypted_key = base64.b64encode(

        bytes([b ^ k for b, k in zip(secret_key.encode(), seal_key * 10)])

    ).decode()

    

    # 生成元数据

    metadata = {

        "key_id": key_id,

        "policy": policy,

        "enclave_identity": enclave_identity[:32],

        "algorithm": "AES-256-GCM",

        "version": 1

    }

    

    # 生成MAC（完整性校验）

    mac_data = f"{key_id}{policy}{encrypted_key}"

    mac = hashlib.sha256(mac_data.encode()).hexdigest()

    

    return {

        "sealed_blob": {

            "key_id": key_id,

            "encrypted_key": encrypted_key,

            "metadata": metadata,

            "mac": mac

        },

        "description": "Enclave使用EGETKEY获取Seal Key，加密后存储到外部"

    }



# ============================================================================

# 第五部分：密钥解封流程

# ============================================================================



# unseal_key_flow（解封密钥的完整流程）

def unseal_key_flow(sealed_blob, current_enclave_identity, current_signer):

    """

    模拟密钥解封流程

    

    Args:

        sealed_blob: 密封后的数据结构

        current_enclave_identity: 当前Enclave的MRENCLAVE

        current_signer: 当前Enclave的MRSIGNER

    

    Returns:

        dict: 解封结果

    """

    import hashlib

    import base64

    

    result = {

        "success": False,

        "error": None,

        "unsealed_key": None

    }

    

    # 步骤1：验证MAC完整性

    mac_data = f"{sealed_blob['key_id']}{sealed_blob['metadata']['policy']}{sealed_blob['encrypted_key']}"

    expected_mac = hashlib.sha256(mac_data.encode()).hexdigest()

    

    if expected_mac != sealed_blob["mac"]:

        result["error"] = "MAC校验失败，数据可能被篡改"

        return result

    

    # 步骤2：验证策略兼容性

    policy = sealed_blob["metadata"]["policy"]

    sealed_identity = sealed_blob["metadata"]["enclave_identity"]

    

    if policy == "MRENCLAVE":

        if current_enclave_identity[:32] != sealed_identity:

            result["error"] = f"MRENCLAVE不匹配: 期望{sealed_identity[:16]}..., 当前{current_enclave_identity[:16]}..."

            return result

    elif policy == "MRSIGNER":

        if current_signer != sealed_identity:

            result["error"] = f"MRSIGNER不匹配"

            return result

    

    # 步骤3：获取Seal Key并解密

    seal_key_material = f"{current_enclave_identity}{policy}"

    seal_key = hashlib.sha256(seal_key_material.encode()).digest()

    

    try:

        encrypted_bytes = base64.b64decode(sealed_blob["encrypted_key"])

        decrypted = bytes([b ^ k for b, k in zip(encrypted_bytes, seal_key * 10)])

        # 去除padding

        result["unsealed_key"] = decrypted.decode().rstrip('\x00')

        result["success"] = True

    except Exception as e:

        result["error"] = f"解密失败: {str(e)}"

    

    return result



# ============================================================================

# 第六部分：密钥派生

# ============================================================================



# key_derivation（密钥派生函数）

def derive_keys(master_key, purpose, length=32):

    """

    使用HKDF从主密钥派生出多个子密钥

    

    Args:

        master_key: 主密钥

        purpose: 密钥用途标识

        length: 派生密钥长度

    

    Returns:

        bytes: 派生的密钥

    """

    import hashlib

    import hmac

    

    # HKDF模拟：基于HMAC的密钥派生

    info = f"{purpose}".encode()

    salt = b"TEE_Salt_V1"

    

    # Extract

    prk = hmac.new(salt, master_key.encode(), hashlib.sha256).digest()

    

    # Expand

    t = b""

    key = b""

    counter = 1

    while len(key) < length:

        t = hmac.new(prk, t + info + bytes([counter]), hashlib.sha256).digest()

        key += t

        counter += 1

    

    return key[:length]



# ============================================================================

# 第七部分：密钥存储位置

# ============================================================================



# key_storage_locations（常见密钥存储位置）

key_storage_locations = {

    "file_system": "加密后存储在普通文件系统",

    "UFS（Untrusted Flash Storage）": "NVMe/Arm Flash中的加密区域",

    "eUFS": "用于存储密封密钥的安全闪存分区",

    "persistent_key": "部分TEE支持安全持久化密钥存储"

}



# ============================================================================

# 主程序：演示密封/解封流程

# ============================================================================



if __name__ == "__main__":

    print("=" * 70)

    print("密钥安全管理：密封密钥与解封")

    print("=" * 70)

    

    # 核心概念

    print("\n【密封密钥定义】")

    for key, val in sealed_key_definition.items():

        print(f"  {key}: {val}")

    

    # 密封策略

    print("\n【密封策略】")

    for policy, info in sealing_policy.items():

        print(f"\n  [{policy}] {info['name']}")

        print(f"    描述: {info['description']}")

        print(f"    优点: {info['pros']}")

        print(f"    缺点: {info['cons']}")

    

    # 演示密封流程

    print("\n【密封流程演示】")

    sample_enclave_id = "abcd1234efgh5678" * 4

    sample_secret = "MySecretAESKey123456789"

    

    sealed = seal_key_flow(sample_enclave_id, sample_secret, "MRENCLAVE")

    print(f"  密钥ID: {sealed['sealed_blob']['key_id']}")

    print(f"  策略: {sealed['sealed_blob']['metadata']['policy']}")

    print(f"  加密后: {sealed['sealed_blob']['encrypted_key'][:40]}...")

    print(f"  MAC: {sealed['sealed_blob']['mac'][:32]}...")

    

    # 演示解封流程

    print("\n【解封流程演示】")

    # 正确的Enclave身份

    unseal_result = unseal_key_flow(

        sealed['sealed_blob'],

        sample_enclave_id,  # 相同身份，可以解封

        "signer_key"

    )

    if unseal_result["success"]:

        print(f"  ✓ 解封成功")

        print(f"  密钥: {unseal_result['unsealed_key']}")

    else:

        print(f"  ✗ 解封失败: {unseal_result['error']}")

    

    # 错误的Enclave身份演示

    print("\n【错误身份解封演示】")

    wrong_enclave_id = "wrong_enclave_identity_12345678" * 4

    unseal_fail = unseal_key_flow(

        sealed['sealed_blob'],

        wrong_enclave_id,  # 错误身份

        "signer_key"

    )

    if not unseal_fail["success"]:

        print(f"  ✗ 解封失败（预期）: {unseal_fail['error']}")

    

    # 密钥派生

    print("\n【密钥派生演示】")

    master = "MasterKeyForApp"

    enc_key = derive_keys(master, "encryption")

    mac_key = derive_keys(master, "authentication")

    print(f"  主密钥: {master}")

    print(f"  加密密钥: {enc_key.hex()[:32]}...")

    print(f"  认证密钥: {mac_key.hex()[:32]}...")

    

    print("\n" + "=" * 70)

    print("密封密钥机制让密钥即使存储在不安全的外部存储中也能保持安全")

    print("=" * 70)

