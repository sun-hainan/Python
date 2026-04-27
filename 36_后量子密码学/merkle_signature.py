# -*- coding: utf-8 -*-

"""

算法实现：后量子密码学 / merkle_signature



本文件实现 merkle_signature 相关的算法功能。

"""



# ============================================================================

# 第一部分：基于哈希签名概述

# ============================================================================



# hash_based_signatures（基于哈希签名的特点）

hash_based_signatures = {

    "security_basis": "仅依赖哈希函数的抗碰撞性",

    "no_structure": "不依赖任何数学问题（如因子分解）",

    "quantum_resistance": "哈希函数对量子攻击保持安全",

    "large_signatures": "主要缺点是签名较大"

}



# one_time_signature（一次性签名OTS）

one_time_signature = {

    "definition": "每个密钥只能签名一条消息",

    "lamport": "最早的OTS方案之一",

    "winternitz": "改进的OTS，使用更短密钥"

}



# ============================================================================

# 第二部分：Lamport一次性签名

# ============================================================================



# lamport_ots（Lamport OTS）

lamport_ots = {

    "inventor": "Leslie Lamport（1979）",

    "key_size": "每个消息位需要2个哈希值",

    "signature_size": "密钥大小的1/2"

}



# lamport_key_generation（Lamport密钥生成）

def lamport_keygen(message_length=256):

    """

    生成Lamport OTS密钥对

    

    Args:

        message_length: 消息哈希长度（位数）

    

    Returns:

        dict: 公钥和私钥

    """

    import secrets

    import hashlib

    

    # 私钥：每个位两个随机数

    private_key = {

        "sk0": [],  # 当消息位为0时使用

        "sk1": []   # 当消息位为1时使用

    }

    

    for i in range(message_length):

        private_key["sk0"].append(secrets.token_bytes(32))

        private_key["sk1"].append(secrets.token_bytes(32))

    

    # 公钥：私钥的哈希

    public_key = {

        "pk0": [hashlib.sha256(x).digest() for x in private_key["sk0"]],

        "pk1": [hashlib.sha256(x).digest() for x in private_key["sk1"]]

    }

    

    return {

        "public_key": public_key,

        "private_key": private_key

    }



# lamport_sign（Lamport签名）

def lamport_sign(message, private_key):

    """

    Lamport OTS签名

    

    Args:

        message: 消息（将进行哈希）

        private_key: 私钥

    

    Returns:

        list: 签名

    """

    import hashlib

    

    # 哈希消息

    message_hash = hashlib.sha256(message).digest()

    

    # 将哈希转换为位

    message_bits = []

    for byte in message_hash:

        for i in range(8):

            message_bits.append((byte >> (7 - i)) & 1)

    

    # 签名：对于每个位，选择对应的私钥片段

    signature = []

    for i, bit in enumerate(message_bits):

        if bit == 0:

            signature.append(private_key["sk0"][i])

        else:

            signature.append(private_key["sk1"][i])

    

    return signature



# lamport_verify（Lamport验证）

def lamport_verify(message, signature, public_key):

    """

    验证Lamport签名

    

    Args:

        message: 消息

        signature: 签名

        public_key: 公钥

    

    Returns:

        bool: 验证结果

    """

    import hashlib

    

    # 哈希消息

    message_hash = hashlib.sha256(message).digest()

    

    # 转换消息为位

    message_bits = []

    for byte in message_hash:

        for i in range(8):

            message_bits.append((byte >> (7 - i)) & 1)

    

    # 验证每个签名片段

    for i, bit in enumerate(message_bits):

        sig_part = signature[i]

        expected_hash = hashlib.sha256(sig_part).digest()

        

        if bit == 0:

            if expected_hash != public_key["pk0"][i]:

                return False

        else:

            if expected_hash != public_key["pk1"][i]:

                return False

    

    return True



# ============================================================================

# 第三部分：Merkle树签名

# ============================================================================



# merkle_tree_signature（Merkle树签名概念）

merkle_tree_signature = {

    "purpose": "使用Merkle树扩展OTS实现多次签名",

    "combining": "将多个OTS公钥哈希成一棵Merkle树",

    "root": "Merkle根作为主公钥",

    "authentication_path": "签名时提供Merkle路径证明"

}



# merkle_tree_construction（Merkle树构造）

def build_merkle_tree(public_keys):

    """

    构建Merkle树

    

    Args:

        public_keys: OTS公钥列表

    

    Returns:

        tuple: (根哈希, 树结构)

    """

    import hashlib

    

    current_level = [hashlib.sha256(pk).digest() for pk in public_keys]

    

    tree_structure = [current_level]

    

    # 构建直到根

    while len(current_level) > 1:

        next_level = []

        for i in range(0, len(current_level), 2):

            left = current_level[i]

            right = current_level[i+1] if i+1 < len(current_level) else left

            combined = hashlib.sha256(left + right).digest()

            next_level.append(combined)

        current_level = next_level

        tree_structure.append(current_level)

    

    root = current_level[0] if current_level else None

    

    return root, tree_structure



# ============================================================================

# 第四部分：Merkle签名方案

# ============================================================================



# mss_key_generation（MSS密钥生成）

def mss_keygen(num_signatures=256):

    """

    Merkle签名方案密钥生成

    

    Args:

        num_signatures: 可签名的消息数量（2的幂）

    

    Returns:

        dict: 完整密钥结构

    """

    import hashlib

    import secrets

    

    # 计算树深度

    import math

    depth = math.ceil(math.log2(num_signatures))

    

    # 生成所有OTS密钥对

    ots_keys = []

    for i in range(num_signatures):

        keys = lamport_keygen(message_length=256)

        ots_keys.append(keys)

    

    # 提取所有公钥

    ots_public_keys = [keys["public_key"] for keys in ots_keys]

    

    # 构建Merkle树

    # 将每个OTS公钥转换为其哈希

    pk_hashes = []

    for pk in ots_public_keys:

        pk_bytes = b"".join(pk["pk0"] + pk["pk1"])

        pk_hashes.append(hashlib.sha256(pk_bytes).digest())

    

    root, tree = build_merkle_tree(pk_hashes)

    

    return {

        "root": root,

        "tree": tree,

        "ots_keys": ots_keys,

        "current_index": 0,

        "depth": depth,

        "num_signatures": num_signatures

    }



# mss_sign（MSS签名）

def mss_sign(message, mss_keys):

    """

    Merkle签名

    

    Args:

        message: 消息

        mss_keys: MSS密钥结构

    

    Returns:

        tuple: (MSS签名, 更新后的密钥状态)

    """

    import hashlib

    

    index = mss_keys["current_index"]

    ots_keys = mss_keys["ots_keys"][index]

    tree = mss_keys["tree"]

    depth = mss_keys["depth"]

    

    # 对消息进行OTS签名

    ots_signature = lamport_sign(message, ots_keys["private_key"])

    

    # 计算当前公钥的哈希

    ots_public_key = ots_keys["public_key"]

    pk_bytes = b"".join(ots_public_key["pk0"] + ots_public_key["pk1"])

    pk_hash = hashlib.sha256(pk_bytes).digest()

    

    # 获取认证路径

    auth_path = []

    current_level_idx = index

    

    for level in range(depth):

        level_size = len(tree[level])

        sibling_idx = current_level_idx ^ 1  # 兄弟节点

        

        if sibling_idx < level_size:

            auth_path.append(tree[level][sibling_idx])

        else:

            auth_path.append(tree[level][current_level_idx])  # 自己

        

        current_level_idx = current_level_idx // 2

    

    # 完整的MSS签名

    mss_signature = {

        "ots_signature": ots_signature,

        "ots_public_key": ots_public_key,

        "auth_path": auth_path,

        "index": index

    }

    

    # 更新密钥状态

    updated_keys = mss_keys.copy()

    updated_keys["current_index"] = index + 1

    

    return mss_signature, updated_keys



# ============================================================================

# 第五部分：MSS验证

# ============================================================================



# mss_verify（MSS验证）

def mss_verify(message, signature, root):

    """

    验证MSS签名

    

    Args:

        message: 消息

        signature: MSS签名

        root: 主公钥（Merkle根）

    

    Returns:

        bool: 验证结果

    """

    import hashlib

    

    ots_sig = signature["ots_signature"]

    ots_pk = signature["ots_public_key"]

    auth_path = signature["auth_path"]

    index = signature["index"]

    

    # 验证OTS签名

    if not lamport_verify(message, ots_sig, ots_pk):

        return False

    

    # 重新计算到根的路径

    pk_bytes = b"".join(ots_pk["pk0"] + ots_pk["pk1"])

    current_hash = hashlib.sha256(pk_bytes).digest()

    

    # 从叶节点到根

    for i, sibling in enumerate(auth_path):

        if (index >> i) & 1 == 0:

            # 当前节点是左子节点

            current_hash = hashlib.sha256(current_hash + sibling).digest()

        else:

            # 当前节点是右子节点

            current_hash = hashlib.sha256(sibling + current_hash).digest()

    

    # 比较根

    return current_hash == root



# ============================================================================

# 第六部分：安全性与效率

# ============================================================================



# security_properties（安全性属性）

security_properties = {

    "unforgeability": "基于哈希函数抗碰撞性",

    "no_quantum_breaks": "对量子攻击保持安全（不同于RSA/ECC）",

    "stateful": "主要限制：是有状态的，需要跟踪已用密钥"

}



# performance_characteristics（性能特点）

performance_characteristics = {

    "signing": "快速（仅需哈希运算）",

    "verification": "中等（需要Merkle路径验证）",

    "signature_size": "大（OTS签名 + Merkle路径）",

    "key_generation": "较慢（需要生成所有OTS密钥）"

}



# ============================================================================

# 第七部分：与SPHINCS+的关系

# ============================================================================



# sphincs_plus_intro（SPHINCS+简介）

sphincs_plus_intro = {

    "full_name": "Stateless Hash-based Signature with Bounded Tree",

    "improvement": "无状态版本，避免MSS的有状态问题",

    "hypertree": "使用多层Merkle树（ hypertree）",

    "nist_selection": "NIST PQC标准化第3轮"

}



# comparison_with_others（与其他基于哈希签名比较）

comparison_with_others = {

    "vs_lamport": {

        "signatures": "Lamport只能签1条，MSS可签多条",

        "size": "Lamport签名更小"

    },

    "vs_sphincs": {

        "state": "MSS有状态，SPHINCS无状态",

        "size": "SPHINCS签名更大",

        "practicality": "SPHINCS更实用"

    }

}



# ============================================================================

# 主程序：演示Merkle签名

# ============================================================================



if __name__ == "__main__":

    print("=" * 70)

    print("Merkle树签名方案")

    print("=" * 70)

    

    # 基于哈希签名概述

    print("\n【基于哈希签名】")

    for key, val in hash_based_signatures.items():

        print(f"  {key}: {val}")

    

    # Lamport OTS

    print("\n【Lamport OTS】")

    for key, val in lamport_ots.items():

        print(f"  {key}: {val}")

    

    # Lamport密钥生成演示

    print("\n【Lamport密钥生成演示】")

    lamport_keys = lamport_keygen(message_length=256)

    print(f"  私钥sk0长度: {len(lamport_keys['private_key']['sk0'])}")

    print(f"  公钥pk0哈希数: {len(lamport_keys['public_key']['pk0'])}")

    

    # Lamport签名演示

    print("\n【Lamport签名演示】")

    message = b"Test message for Lamport OTS"

    signature = lamport_sign(message, lamport_keys["private_key"])

    print(f"  消息: {message}")

    print(f"  签名片段数: {len(signature)}")

    

    # 验证

    verified = lamport_verify(message, signature, lamport_keys["public_key"])

    print(f"  验证结果: {verified}")

    

    # Merkle树签名

    print("\n【MSS密钥生成】")

    mss_keys = mss_keygen(num_signatures=8)  # 小数量演示

    print(f"  Merkle根: {mss_keys['root'].hex()[:32]}...")

    print(f"  可签名数量: {mss_keys['num_signatures']}")

    print(f"  树深度: {mss_keys['depth']}")

    

    # MSS签名

    print("\n【MSS签名演示】")

    mss_message = b"MSS test message"

    mss_sig, updated_keys = mss_sign(mss_message, mss_keys)

    print(f"  消息: {mss_message}")

    print(f"  OTS签名片段数: {len(mss_sig['ots_signature'])}")

    print(f"  认证路径长度: {len(mss_sig['auth_path'])}")

    print(f"  使用密钥索引: {mss_sig['index']}")

    

    # MSS验证

    mss_verified = mss_verify(mss_message, mss_sig, mss_keys["root"])

    print(f"  验证结果: {mss_verified}")

    

    # 安全性

    print("\n【安全性属性】")

    for key, val in security_properties.items():

        print(f"  {key}: {val}")

    

    print("\n【性能特点】")

    for key, val in performance_characteristics.items():

        print(f"  · {key}: {val}")

    

    # SPHINCS+

    print("\n【SPHINCS+】")

    for key, val in sphincs_plus_intro.items():

        print(f"  {key}: {val}")

    

    print("\n" + "=" * 70)

    print("Merkle签名是基于哈希签名的基础，SPHINCS+是其无状态改进")

    print("=" * 70)

