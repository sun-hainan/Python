# -*- coding: utf-8 -*-
"""
算法实现：可信执行环境 / sgx_application_development

本文件实现 sgx_application_development 相关的算法功能。
"""

# ============================================================================
# 第一部分：开发环境要求
# ============================================================================

# development_environment（开发环境要求）
development_environment = {
    "硬件要求": {
        "cpu": "第六代Intel Core或更新（支持SGX）",
        "BIOS": "启用SGX支持（部分CPU需要"Enabled"而非"Software Controlled"）",
        "RAM": "至少8GB（Enclave需要额外内存）"
    },
    "操作系统": {
        "linux": "Ubuntu 20.04/22.04, Fedora 34+",
        "windows": "Windows 10/11 Pro",
        "参考": "Intel SGX官方支持列表"
    },
    "必需软件": {
        "Intel_SGX_SDK": "sgx_linux_x64_sdk_2.x.x.bin",
        "Intel_SGX_Driver": "内核驱动（Linux需要）",
        "DCAP": "Data Center Attestation Primitives",
        "GCC": "支持C++11或更新"
    }
}

# ============================================================================
# 第二部分：项目创建流程
# ============================================================================

# project_creation_steps（项目创建步骤）
project_creation_steps = [
    ("下载SDK", "从Intel官网下载SGX SDK安装包"),
    ("安装SDK", "执行 .bin 安装脚本到指定目录"),
    ("创建项目", "使用 $SGX_SDK/sgxsdk/unsafe_sgx_module.sh 或手动创建"),
    ("编写EDL", "定义ECALL和OCALL接口"),
    ("运行Edger8r", "生成桥接代码"),
    ("实现Enclave", "编写可信函数"),
    ("实现App", "编写非可信主程序"),
    ("编译运行", "编译并测试")
]

# ============================================================================
# 第三部分：完整EDL示例
# ============================================================================

# complete_edl_example（完整EDL文件示例）
complete_edl_example = """
/*
 * SecretManager.edl - 密钥管理Enclave接口
 */

enclave {
    // 导入可信库
    from "sgx_tkey_exchange.edl" import *;
    from "sgx_std.edl" import *;
    
    trusted {
        // 公开ECALL - 任何应用可调用
        public void ecall_init_enclave();
        
        // 生成加密密钥
        public int ecall_generate_key(
            [out, size=32] uint8_t* public_key,
            [out, size=32] uint8_t* private_key_sealed,
            size_t sealed_size
        );
        
        // 加密数据
        public int ecall_encrypt_data(
            [in, size=data_len] const uint8_t* plaintext,
            size_t data_len,
            [in, size=32] const uint8_t* key,
            [out, size=out_len] uint8_t* ciphertext,
            size_t out_len
        );
        
        // 解密数据
        public int ecall_decrypt_data(
            [in, size=data_len] const uint8_t* ciphertext,
            size_t data_len,
            [in, size=32] const uint8_t* key,
            [out, size=out_len] uint8_t* plaintext,
            size_t out_len
        );
    };
    
    untrusted {
        // 不可信函数 - Enclave调用外部服务
        void ocall_print([in, string] const char* str);
        void ocall_save_to_file(
            [in, size=size] const uint8_t* data,
            size_t size,
            [in, string] const char* filename
        );
        int ocall_load_from_file(
            [in, string] const char* filename,
            [out, size=size] uint8_t* data,
            size_t size
        );
    };
};
"""

# ============================================================================
# 第四部分：Enclave代码实现
# ============================================================================

# enclave_implementation_example（Enclave实现示例）
enclave_implementation_example = """
#include "sgx_error.h"
#include "sgx_tkey_exchange.h"
#include "SecretManager_t.h"  // Edger8r生成的头文件

// 全局Enclave状态
sgx_ec256_private_t* g_private_key = NULL;
sgx_aes_gcm_128bit_key_t g_master_key;

// Enclave初始化
sgx_status_t ecall_init_enclave() {
    // 初始化Enclave内部状态
    return SGX_SUCCESS;
}

// 生成密钥
sgx_status_t ecall_generate_key(
    uint8_t* public_key,
    uint8_t* private_key_sealed,
    size_t sealed_size
) {
    sgx_ecc_state_handle_t ecc_state = NULL;
    sgx_ec256_private_t private_key;
    sgx_ec256_public_t public_key_temp;
    
    // 创建ECDH密钥对
    sgx_ecc256_create_key_pair(&private_key, &public_key_temp, ecc_state);
    
    // 密封私钥
    sgx_seal_data(...);
    
    return SGX_SUCCESS;
}
"""

# ============================================================================
# 第五部分：应用代码实现
# ============================================================================

# application_code_example（应用代码示例）
application_code_example = """
#include "sgx_urts.h"
#include "SecretManager_u.h"  // Edger8r生成的非可信桥接

#define ENCLAVE_PATH "./libsecretmanager.signed.so"

sgx_enclave_id_t global_eid = 0;

// 初始化Enclave
int initialize_enclave() {
    sgx_launch_token_t token = {0};
    int updated = 0;
    
    sgx_status_t status = sgx_create_enclave(
        ENCLAVE_PATH,
        SGX_DEBUG_FLAG,
        &token,
        &updated,
        &global_eid
    );
    
    if (status != SGX_SUCCESS) {
        printf("Failed to create enclave: %x\\n", status);
        return -1;
    }
    
    return 0;
}

int main() {
    // 创建Enclave
    if (initialize_enclave() < 0) return -1;
    
    // 调用Enclave函数
    uint8_t public_key[32];
    uint8_t sealed_key[256];
    
    sgx_status_t status = ecall_generate_key(
        global_eid,
        public_key,
        sealed_key,
        sizeof(sealed_key)
    );
    
    // 清理
    sgx_destroy_enclave(global_eid);
    return 0;
}
"""

# ============================================================================
# 第六部分：编译脚本
# ============================================================================

# compilation_instructions（编译说明）
compilation_instructions = {
    "预处理Edger8r": "cd Enclave && make",
    "编译Enclave": "sgx_encryptor -f Enclave/Enclave.cpp -o Enclave.so",
    "签名Enclave": "sgx_sign -key Enclave_private.pem -enclave Enclave.so -out Enclave.signed.so",
    "编译应用": "gcc -o App App.cpp -L$SGX_SDK/lib -lsgx_urts -lsecretmanager_u",
    "设置环境变量": "export LD_LIBRARY_PATH=$SGX_SDK/lib:$LD_LIBRARY_PATH"
}

# ============================================================================
# 第七部分：常见错误与解决
# ============================================================================

# common_errors（常见错误）
common_errors = {
    "SGX_ERROR_NO_DEVICE": "SGX未在BIOS中启用，或驱动未安装",
    "SGX_ERROR_INVALID_ENCLAVE": "Enclave签名无效，检查签名密钥",
    "SGX_ERROR_OUT_OF_MEMORY": "EPC内存不足，减小Enclave大小或增加EPC",
    "SGX_ERROR_INVALID_ATTRIBUTE": "Enclave属性不匹配，检查是否支持调试",
    "page_fault_error": "内存访问越界，检查指针和边界",
    "linker_error_undefined": "未链接正确的库，检查Makefile"
}

# troubleshooting_steps（故障排除步骤）
troubleshooting_steps = [
    "检查 'ls /dev/isgx' 或 '/dev/sgx/enclave' 是否存在",
    "运行 'sgx_device' 检查驱动状态",
    "使用 'openssl enc -aes-256-cbc -pass pass:xxx -in file -out file.enc' 验证基础加密",
    "启用Enclave日志输出：setenv('SGX_DEBUG', '1')",
    "检查 dmesg | grep sgx 获取内核日志"
]

# ============================================================================
# 第八部分：调试技巧
# ============================================================================

# debugging_techniques（调试技巧）
debugging_techniques = {
    "debug_enclave": "编译时设置SGX_DEBUG_FLAG=1，运行时可调试",
    "printf_debugging": "通过OCALL将日志输出到App",
    "gdb_support": "使用sgx-gdb进行Enclave调试",
    "crash_dump": "检查 /var/log/kern.log 中的SGX错误日志"
}

# ============================================================================
# 第九部分：部署检查清单
# ============================================================================

# deployment_checklist（部署检查清单）
deployment_checklist = [
    "使用正式签名密钥（不是调试密钥）",
    "Enclave属性设置debuggable=false（生产环境）",
    "启用防回滚（Anti-Replay）机制",
    "密封密钥存储在安全位置",
    "配置远程认证（IAS/DCAP服务）",
    "启用TLS加密通信",
    "定期更新Intel微码和SGX PSW"
]

# ============================================================================
# 主程序：展示开发流程
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SGX应用开发指南：从入门到实战")
    print("=" * 70)
    
    # 开发环境
    print("\n【开发环境要求】")
    print("  硬件要求：")
    for req, desc in development_environment["硬件要求"].items():
        print(f"    · {req}: {desc}")
    print("  操作系统：")
    for os, desc in development_environment["操作系统"].items():
        print(f"    · {os}: {desc}")
    print("  必需软件：")
    for sw, desc in development_environment["必需软件"].items():
        print(f"    · {sw}: {desc}")
    
    # 项目创建流程
    print("\n【项目创建流程】")
    for i, (step, desc) in enumerate(project_creation_steps, 1):
        print(f"  {i}. {step}: {desc}")
    
    # EDL示例
    print("\n【EDL文件示例（部分）】")
    for line in complete_edl_example.strip().split('\n')[:20]:
        print(f"  {line}")
    print("  ...")
    
    # 编译说明
    print("\n【编译说明】")
    for step, desc in compilation_instructions.items():
        print(f"  · {step}: {desc}")
    
    # 常见错误
    print("\n【常见错误与解决】")
    for error, solution in common_errors.items():
        print(f"  ✗ {error}")
        print(f"    → {solution}")
    
    # 故障排除
    print("\n【故障排除步骤】")
    for i, step in enumerate(troubleshooting_steps, 1):
        print(f"  {i}. {step}")
    
    # 部署检查清单
    print("\n【部署检查清单】")
    for i, item in enumerate(deployment_checklist, 1):
        print(f"  {i}. {item}")
    
    print("\n" + "=" * 70)
    print("SGX开发需要细心：EDL定义 -> Edger8r -> 实现 -> 编译 -> 签名 -> 部署")
    print("=" * 70)
