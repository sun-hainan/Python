# -*- coding: utf-8 -*-

"""

算法实现：后量子密码学 / pqc_overview



本文件实现 pqc_overview 相关的算法功能。

"""



# ============================================================================

# 第一部分：量子威胁

# ============================================================================



# quantum_threat（量子计算威胁）

quantum_threat = {

    "shor_algorithm": "Shor算法可在多项式时间分解大整数，破解RSA",

    "grover_algorithm": "Grover算法提供平方加速，影响对称加密",

    "timeline": "大规模量子计算机预计10-20年内出现",

    "harvest_now_decrypt_later": "现在收集数据，以后解密"

}



# crypto_impact（密码学影响）

crypto_impact = {

    "rsa_ecc_broken": "RSA、ECC不再安全",

    "symmetric_affected": "AES-128需升级到AES-256",

    "hash_safe": "哈希函数相对安全（需更长输出）"

}



# ============================================================================

# 第二部分：NIST标准化

# ============================================================================



# nist_process（标准化进程）

nist_process = {

    "call_for_proposals": "2016年征集后量子算法",

    "round_1": "2017年69个提案",

    "round_2": "2019年26个进入第二轮",

    "round_3": "2020年7个进入决赛",

    "round_4": "2022年4个标准化 + 4个额外评估"

}



# standardized_algorithms（已标准化算法）

standardized_algorithms = {

    "kyber": {

        "type": "KEM",

        "basis": "Module-LWE",

        "security": "128-256位",

        "key_size": "公钥约1KB"

    },

    "dilithium": {

        "type": "数字签名",

        "basis": "Module-LWE",

        "security": "128-256位",

        "signature_size": "约2.6KB"

    },

    "falcon": {

        "type": "数字签名",

        "basis": "NTRU",

        "security": "128-256位",

        "signature_size": "约660字节（最紧凑）"

    },

    "sphincs_plus": {

        "type": "数字签名",

        "basis": "哈希函数",

        "security": "128-256位",

        "signature_size": "约30KB（最大）"

    }

}



# ============================================================================

# 第三部分：算法分类

# ============================================================================



# algorithm_categories（算法分类）

algorithm_categories = {

    "lattice_based": {

        "examples": ["Kyber", "Dilithium", "Falcon", "NTRU"],

        "hardness": "格问题（如LWE、SVP）",

        "maturity": "最高（多个标准）"

    },

    "code_based": {

        "examples": ["McEliece", "BIKE", "HQC"],

        "hardness": "译码问题",

        "maturity": "成熟（McEliece 1978）"

    },

    "hash_based": {

        "examples": ["SPHINCS+", "XMSS"],

        "hardness": "哈希函数抗碰撞",

        "maturity": "成熟，但签名大"

    },

    "isogeny_based": {

        "examples": ["SIKE"],

        "hardness": "超奇异同源问题",

        "maturity": "较新，密钥最小"

    },

    "multivariate": {

        "examples": ["Rainbow（已攻破）", "GeMSS"],

        "hardness": "多变量二次方程组",

        "maturity": "中等"

    }

}



# ============================================================================

# 第四部分：算法比较

# ============================================================================



# algorithm_comparison（详细比较）

def compare_algorithms():

    """

    比较主要PQC算法

    """

    comparison = []

    

    # Kyber

    comparison.append({

        "name": "Kyber-768",

        "type": "KEM",

        "public_key": "1184 bytes",

        "ciphertext": "1088 bytes",

        "shared_secret": "32 bytes",

        "security": "约128位",

        "speed": "非常快"

    })

    

    # McEliece

    comparison.append({

        "name": "McEliece-460896",

        "type": "KEM",

        "public_key": "524KB",

        "ciphertext": "188 bytes",

        "shared_secret": "32 bytes",

        "security": "约256位",

        "speed": "较慢"

    })

    

    # SIKE

    comparison.append({

        "name": "SIKE-p434",

        "type": "KEM",

        "public_key": "378 bytes",

        "ciphertext": "346 bytes",

        "shared_secret": "32 bytes",

        "security": "约128位",

        "speed": "中等"

    })

    

    # Dilithium

    comparison.append({

        "name": "Dilithium-3",

        "type": "签名",

        "public_key": "1952 bytes",

        "signature": "3293 bytes",

        "security": "约128位",

        "speed": "快"

    })

    

    # SPHINCS+

    comparison.append({

        "name": "SPHINCS+-128s",

        "type": "签名",

        "public_key": "32 bytes",

        "signature": "29764 bytes",

        "security": "约128位",

        "speed": "较慢"

    })

    

    return comparison



# ============================================================================

# 第五部分：迁移考虑

# ============================================================================



# migration_considerations（迁移考虑）

migration_considerations = {

    "hybrid_crypto": "将PQC与经典算法结合",

    "key_management": "PQC密钥通常更大",

    "performance": "不同方案性能差异大",

    "compatibility": "确保与现有系统兼容",

    "standards": "关注IETF、ISO等标准进展"

}



# hybrid_recommendation（混合建议）

hybrid_recommendation = {

    "tls_1_3": "使用PQC cipher suite",

    "pkix": "X.509证书中包含PQC公钥",

    "key_exchange": "先用X25519+PQC KEM",

    "signatures": "使用ECDSA+PQC双签名"

}



# ============================================================================

# 第六部分：实现状态

# ============================================================================



# implementation_status（实现状态）

implementation_status = {

    "openssl_3_0": "已支持Kyber",

    "libsodium": "计划支持",

    "boringssl": "已支持X25519+Kyber混合",

    "web_browsers": "Chrome、Firefox正在实验性支持"

}



# ============================================================================

# 主程序

# ============================================================================



if __name__ == "__main__":

    print("=" * 70)

    print("后量子密码学全景：标准化与比较")

    print("=" * 70)

    

    # 量子威胁

    print("\n【量子威胁】")

    for key, val in quantum_threat.items():

        print(f"  {key}: {val}")

    

    print("\n【密码学影响】")

    for key, val in crypto_impact.items():

        print(f"  · {key}: {val}")

    

    # NIST进程

    print("\n【NIST标准化进程】")

    for stage, desc in nist_process.items():

        print(f"  {stage}: {desc}")

    

    # 标准化算法

    print("\n【已标准化算法】")

    for name, details in standardized_algorithms.items():

        print(f"\n  [{name}]")

        for key, val in details.items():

            print(f"    {key}: {val}")

    

    # 算法分类

    print("\n【算法分类】")

    for category, info in algorithm_categories.items():

        print(f"\n  [{category}]")

        print(f"    示例: {', '.join(info['examples'])}")

        print(f"    难度: {info['hardness']}")

        print(f"    成熟度: {info['maturity']}")

    

    # 比较

    print("\n【算法比较】")

    comps = compare_algorithms()

    for c in comps:

        print(f"\n  [{c['name']}]")

        for key, val in c.items():

            if key != 'name':

                print(f"    {key}: {val}")

    

    # 迁移

    print("\n【迁移考虑】")

    for key, val in migration_considerations.items():

        print(f"  · {key}: {val}")

    

    print("\n【混合建议】")

    for key, val in hybrid_recommendation.items():

        print(f"  · {key}: {val}")

    

    print("\n【实现状态】")

    for lib, status in implementation_status.items():

        print(f"  · {lib}: {status}")

    

    print("\n" + "=" * 70)

    print("PQC迁移是长期过程，混合模式是目前推荐方案")

    print("=" * 70)

