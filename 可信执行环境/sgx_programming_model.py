# -*- coding: utf-8 -*-
"""
算法实现：可信执行环境 / sgx_programming_model

本文件实现 sgx_programming_model 相关的算法功能。
"""

# ============================================================================
# 第一部分：SGX SDK架构
# ============================================================================

# sgx_sdk_components（SGX SDK核心组件）
sgx_sdk_components = {
    "Edger8r": "EDL边缘编译器，生成Enclave桥接代码",
    "Launcher": "加载Enclave的主程序（非Enclave部分）",
    "Enclave": "受保护的代码和数据区域",
    "Trusted Runtime（TRTS）": "可信运行时，支持Enclave执行",
    "Trusted Libraries": "可信库（libc、libcxx、libsgx_tstdc等）",
    "Untrusted Runtime（URTS）": "非可信运行时，管理Enclave生命周期"
}

# ============================================================================
# 第二部分：EDL接口定义语言
# ============================================================================

# edl_file_structure（EDL文件结构示例）
edl_file_content = """
// TrustedEnclave.edl - EDL接口定义示例

// 声明可信函数（从外部调用进入Enclave）
trusted {
    // 公共可信函数（任何应用可调用）
    public int ecall_encrypt([in, size=len] const uint8_t* plaintext, size_t len, [out] uint8_t* ciphertext);
    
    // 私有可信函数（仅同一Enclave内的ECALL可调用）
    private int internal_key_derivation();
};

// 声明不可信函数（从Enclave调用外部服务）
untrusted {
    // 不可信库函数
    void ocall_print_string([in, string] const char* str);
};
"""

# ============================================================================
# 第三部分：关键API函数
# ============================================================================

# sgx_creation_api（Enclave创建相关API）
sgx_creation_api = {
    "sgx_create_enclave()": "创建并初始化Enclave",
    "sgx_destroy_enclave()": "销毁Enclave并释放资源",
    "sgx_create_enclave_ex()": "扩展版创建（支持更多参数）"
}

# sgx_attestation_api（认证相关API）
sgx_attestation_api = {
    "sgx_ra_init()": "初始化远程认证上下文",
    "sgx_ra_get_msg1()": "生成认证消息1（用于RA初始化）",
    "sgx_ra_proc_msg2()": "处理认证消息2（验证远程证明）",
    "sgx_ra_get_msg3()": "获取认证消息3（Quote）"
}

# sgx_key_api（密钥相关API）
sgx_key_api = {
    "sgx_get_key()": "获取Enclave密钥（Seal Key/Report Key等）",
    "sgx_seal_data()": "密封数据",
    "sgx_unseal_data()": "解封数据",
    "sgx_init_ra()": "初始化远程认证密钥派生"
}

# sgx_enclave_call_api（Enclave调用API）
sgx_enclave_call_api = {
    "sgx_call_enclave()": "同步调用Enclave函数",
    "sgx_ecall()": "底层ECALL接口",
    "EENTER": "直接进入Enclave（不通过SDK）"
}

# ============================================================================
# 第四部分：Enclave内存管理
# ============================================================================

# sgx_memory_model（SGX内存模型）
sgx_memory_model = {
    "EPC（Enclave Page Cache）": "物理内存中用于Enclave页面的区域",
    "EPCM（EPC Map）": "每个EPC页面的元数据（权限、类型、所有者）",
    "regular_DRAM": "非Enclave内存，OS可自由访问",
    "prefetch_buffer": "CPU缓存，不受Enclave保护"
}

# memory_attributes（内存属性）
memory_attributes = {
    "R": "Readable，可读",
    "W": "Writable，可写",
    "X": "Executable，可执行",
    "P": "Privileged， 特权模式访问",
    "A": "Address_mode，地址模式"
}

# ============================================================================
# 第五部分：异常处理
# ============================================================================

# sgx_exception_types（SGX相关异常类型）
sgx_exception_types = {
    "page_fault": "Enclave页面错误，可能是正常页面调度或攻击",
    "divide_error": "除零错误",
    "invalid_opcode": "无效操作码（可能在Enclave中被注入）",
    "protection_fault": "Enclave内存保护违规"
}

# exception_handler_pattern（异常处理模式）
exception_handler_pattern = """
// 设置异步退出通知
sgx_status = sgx_register_exception_handler(
    EXCEPTION_HAPPENED_CALLBACK,
    &handler_context
);

// 启用异步退出
sgx_enable_exception_handler();

// 在Enclave内执行敏感操作
// 如果发生异常，会触发AEX并调用handler

// 恢复执行或终止
"""

# ============================================================================
# 第六部分：项目结构示例
# ============================================================================

# enclave_project_structure（Enclave项目目录结构）
enclave_project_structure = {
    "App/": "主应用程序（非Enclave）",
    "  App.cpp": "主程序入口，加载Enclave",
    "  App.h": "应用头文件",
    "Enclave/": "Enclave代码",
    "  Enclave.cpp": "可信函数实现",
    "  Enclave.h": "可信函数声明",
    "  Enclave.lds": "链接器脚本",
    "Enclave.edl": "接口定义文件",
    "Makefile": "编译脚本"
}

# ============================================================================
# 第七部分：编程工作流
# ============================================================================

# programming_workflow（SGX应用开发流程）
programming_workflow = [
    ("编写EDL", "定义ECALL和OCALL接口"),
    ("运行Edger8r", "生成桥接代码（Enclave_t.c / Enclave_u.c）"),
    ("编写Enclave代码", "实现可信函数逻辑"),
    ("编写应用代码", "调用Enclave函数"),
    ("编译Enclave", "生成Enclave.signed.so（签名后的Enclave）"),
    ("运行应用", "加载签名后的Enclave，调用ECALL")
]

# ============================================================================
# 第八部分：函数参数传递规则
# ============================================================================

# parameter_passing_rules（EDL参数方向修饰符）
parameter_passing_rules = {
    "in": "数据从外部传入Enclave",
    "out": "数据从Enclave传出到外部",
    "in,out": "双向传递",
    "size": "指定数据大小",
    "string": "以null结尾的字符串",
    "count": "数组元素数量"
}

# ============================================================================
# 主程序：展示SGX编程模型
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Intel SGX编程模型详解")
    print("=" * 70)
    
    # SDK组件
    print("\n【SGX SDK核心组件】")
    for component, desc in sgx_sdk_components.items():
        print(f"  · {component}: {desc}")
    
    # EDL示例
    print("\n【EDL接口定义示例】")
    for line in edl_file_content.strip().split('\n')[:15]:
        print(f"  {line}")
    print("  ...")
    
    # 关键API分类
    print("\n【创建API】")
    for api in sgx_creation_api.values():
        print(f"  · {api}")
    
    print("\n【认证API】")
    for api in sgx_attestation_api.values():
        print(f"  · {api}")
    
    print("\n【密钥API】")
    for api in sgx_key_api.values():
        print(f"  · {api}")
    
    # 内存模型
    print("\n【内存模型】")
    for region, desc in sgx_memory_model.items():
        print(f"  · {region}: {desc}")
    
    # 项目结构
    print("\n【项目目录结构】")
    for path, desc in enclave_project_structure.items():
        print(f"  {path}  {desc}")
    
    # 开发流程
    print("\n【开发流程】")
    for i, step in enumerate(programming_workflow, 1):
        print(f"  {i}. {step[0]}: {step[1]}")
    
    # 参数传递规则
    print("\n【EDL参数修饰符】")
    for modifier, desc in parameter_passing_rules.items():
        print(f"  · {modifier}: {desc}")
    
    print("\n" + "=" * 70)
    print("SGX编程模型通过EDL + SDK提供安全且易用的Enclave开发框架")
    print("=" * 70)
