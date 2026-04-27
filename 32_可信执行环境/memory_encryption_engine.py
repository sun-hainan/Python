# -*- coding: utf-8 -*-

"""

算法实现：可信执行环境 / memory_encryption_engine



本文件实现 memory_encryption_engine 相关的算法功能。

"""



# ============================================================================

# 第一部分：MEE核心概念

# ============================================================================



# mee_definition（MEE定义）

mee_definition = {

    "MEE": "集成在CPU和内存控制器之间的硬件加密引擎",

    "location": "位于处理器和DRAM之间，对所有内存访问进行透明加密",

    "purpose": "防止冷启动攻击和物理内存读取攻击",

    "scope": "仅加密Enclave相关内存（EPC），普通内存不受影响"

}



# ============================================================================

# 第二部分：MEE在系统中的位置

# ============================================================================



# system_topology（MEE在系统拓扑中的位置）

system_topology = [

    ("CPU Core", "执行Enclave代码，产生内存访问请求"),

    ("→ L1/L2/L3 Cache", "CPU缓存层，未加密（与CPU同在芯片内）"),

    ("→ MEE", "内存加密引擎，拦截所有EPC内存访问"),

    ("→ Memory Controller", "内存控制器，管理DRAM访问"),

    ("→ DRAM", "物理内存，已加密存储")

]



# memory_access_flow（内存访问流程）

memory_access_flow = {

    "read_from_enclave": "MEE解密DRAM数据 → 传递明文到CPU（仅Enclave模式）",

    "write_to_enclare": "MEE加密明文数据 → 存储密文到DRAM",

    "untrusted_memory": "直接访问，不经过MEE"

}



# ============================================================================

# 第三部分：MEE加密机制

# ============================================================================



# mee_encryption_algorithm（加密算法）

mee_encryption_algorithm = {

    "AES-XTS": "用于块设备的分组密码模式，SGX使用",

    "AES-128-GCM": "Galois/Counter Mode，带认证，TDX使用",

    "key_derivation": "从根密钥派生每个页面的唯一密钥",

    "key_per_page": "每个4KB页面使用不同的加密密钥"

}



# encryption_metadata（加密元数据）

encryption_metadata = {

    "ciphertext": "加密后的数据存储在DRAM",

    "integrity_tree": "Merkle树用于完整性校验",

    "random_nonce": "每个块使用不同的随机数",

    "key_id": "标识使用的密钥版本"

}



# ============================================================================

# 第四部分：完整性校验机制

# ============================================================================



# integrity_verification（MEE完整性校验）

integrity_verification = {

    "MAC（Message Authentication Code）": "每个内存块附带校验码",

    "Merkle_Tree": "完整性树，根节点存储在CPU内",

    "counter_mode": "使用计数器防止重放攻击",

    "version_number": "页面版本号防止回滚"

}



# integrity_check_flow（完整性检查流程）

def integrity_check_flow():

    """

    MEE完整性检查的模拟流程

    """

    steps = []

    

    # 读取内存

    steps.append({

        "action": "读取加密内存块",

        "data": "DRAM返回密文 + MAC + Counter"

    })

    

    # 验证完整性

    steps.append({

        "action": "MEE验证MAC",

        "method": "使用存储在CPU内的密钥重新计算MAC并比对"

    })

    

    # 检查计数器

    steps.append({

        "action": "检查Counter",

        "purpose": "防止重放攻击（旧数据副本）"

    })

    

    # 解密或报错

    steps.append({

        "action": "MAC匹配则解密，否则触发异常",

        "result": "完整性验证失败时报告错误"

    })

    

    return steps



# ============================================================================

# 第五部分：TDX MEE vs SGX MME

# ============================================================================



# tee_mee_comparison（MEE实现对比）

tee_mee_comparison = {

    "Intel_SGX": {

        "full_name": "Memory Encryption Engine（MME）",

        "encryption": "AES-XTS-128",

        "integrity": "基于Merkle树的部分完整性保护",

        "scope": "仅EPC区域",

        "counter_per_page": "是（16字节计数器）"

    },

    "Intel_TDX": {

        "full_name": "TDX MEE（Memory Encryption Engine）",

        "encryption": "AES-256-XTS（更强）",

        "integrity": "强完整性保护（完整Merkle树）",

        "scope": "TD私有内存（所有TD访问）",

        "key_management": "MKTME（Multi-Key TME）支持多租户密钥"

    },

    "AMD_SEV": {

        "full_name": "AMD Secure Memory Encryption",

        "encryption": "AES-128",

        "integrity": "使用安全嵌套页表（Secure Encrypted Vyrtulization）",

        "scope": "整个VM内存"

    }

}



# ============================================================================

# 第六部分：性能与优化

# ============================================================================



# performance_considerations（MEE性能考虑）

performance_considerations = {

    "latency_overhead": "内存加密增加约5-10ns访问延迟",

    "bandwidth_impact": "加密操作占内存带宽的5-15%",

    "cache_hit": "缓存命中时无MEE开销",

    "decryption_needed": "每次缓存未命中都需要解密"

}



# optimization_techniques（优化技术）

optimization_techniques = {

    "large_page_support": "使用2MB页面减少元数据开销",

    "streaming_mode": "对顺序访问优化，减少随机访问",

    "key_caching": "在CPU内缓存页面密钥",

    "integrity_tree_skip": "可信内存区域跳过完整性检查"

}



# ============================================================================

# 第七部分：安全边界

# ============================================================================



# mee_security_boundary（MEE安全边界）

mee_security_boundary = {

    "protected_by_MEE": [

        "EPC/TD私有内存中的数据",

        "Enclave寄存器状态（在内存中时）",

        "MEE元数据（Counter、MAC等）"

    ],

    "NOT_protected_by_MEE": [

        "CPU缓存中的数据（L1/L2/L3）",

        "CPU寄存器",

        "非Enclave内存",

        "传输中的数据（CPU间互联）"

    ]

}



# ============================================================================

# 主程序：展示MEE机制

# ============================================================================



if __name__ == "__main__":

    print("=" * 70)

    print("内存加密引擎（Memory Encryption Engine, MEE）概念")

    print("=" * 70)

    

    # 定义

    print("\n【MEE定义】")

    for key, val in mee_definition.items():

        print(f"  {key}: {val}")

    

    # 系统拓扑

    print("\n【MEE在系统中的位置】")

    for component, desc in system_topology:

        print(f"  {component} → {desc}")

    

    # 访问流程

    print("\n【内存访问流程】")

    for access_type, desc in memory_access_flow.items():

        print(f"  {access_type}: {desc}")

    

    # 加密算法

    print("\n【加密机制】")

    for algo, desc in mee_encryption_algorithm.items():

        print(f"  · {algo}: {desc}")

    

    # 完整性检查流程

    print("\n【完整性检查流程】")

    for step in integrity_check_flow():

        print(f"  → {step['action']}")

        for k, v in step.items():

            if k != 'action':

                print(f"    {k}: {v}")

    

    # TEE对比

    print("\n【各TEE的MEE实现对比】")

    for tee, details in tee_mee_comparison.items():

        print(f"\n  [{tee}]")

        for key, val in details.items():

            print(f"    {key}: {val}")

    

    # 安全边界

    print("\n【MEE安全边界】")

    print("  ✓ 受MEE保护：")

    for item in mee_security_boundary["protected_by_MEE"]:

        print(f"    · {item}")

    print("  ✗ 不受MEE保护：")

    for item in mee_security_boundary["NOT_protected_by_MEE"]:

        print(f"    · {item}")

    

    # 性能

    print("\n【性能考虑】")

    for concern, desc in performance_considerations.items():

        print(f"  · {concern}: {desc}")

    

    print("\n" + "=" * 70)

    print("MEE通过硬件透明加密确保即使物理内存被窃取也无法读取数据")

    print("=" * 70)

