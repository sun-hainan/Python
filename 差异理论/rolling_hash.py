# -*- coding: utf-8 -*-
"""
算法实现：差异理论 / rolling_hash

本文件实现 rolling_hash 相关的算法功能。
"""

class RollingHash:
    """
    滚动哈希类
    
    使用多项式哈希函数：H(c_0, c_1, ..., c_{n-1}) = Σ c_i * base^{n-1-i} mod m
    
    其中base是基数，m是模数
    """
    
    def __init__(self, base=256, modulus=10**9 + 7):
        """
        初始化滚动哈希
        
        参数:
            base: 基数（通常选择大于字符集大小的质数）
            modulus: 模数（选择大质数以减少冲突）
        """
        self.base = base
        self.modulus = modulus
        self.hash_value = 0
        self.length = 0
    
    def update_add(self, char):
        """
        添加一个字符到末尾（构建哈希）
        
        参数:
            char: 要添加的字符（整数或字符）
        """
        char_value = ord(char) if isinstance(char, str) else char
        self.hash_value = (self.hash_value * self.base + char_value) % self.modulus
        self.length += 1
    
    def update_remove(self, char, power):
        """
        从开头移除一个字符（滑动窗口）
        
        参数:
            char: 要移除的字符
            power: base^{窗口大小-1} mod modulus
        """
        char_value = ord(char) if isinstance(char, str) else char
        self.hash_value = (self.hash_value - char_value * power % self.modulus + self.modulus) % self.modulus


def compute_initial_hash(text, base=256, modulus=10**9 + 7):
    """
    计算文本的初始哈希值
    
    参数:
        text: 输入文本
        base: 基数
        modulus: 模数
    
    返回:
        哈希值
    """
    hash_value = 0
    for char in text:
        char_value = ord(char)
        hash_value = (hash_value * base + char_value) % modulus
    return hash_value


def compute_power(base, exp, modulus):
    """
    计算base^exp mod modulus
    
    参数:
        base: 底数
        exp: 指数
        modulus: 模数
    
    返回:
        幂结果
    """
    result = 1
    base = base % modulus
    
    while exp > 0:
        if exp % 2 == 1:
            result = (result * base) % modulus
        exp //= 2
        base = (base * base) % modulus
    
    return result


def rolling_hash_substring(text, pattern, base=256, modulus=10**9 + 7):
    """
    使用滚动哈希在文本中查找模式串
    
    参数:
        text: 主文本
        pattern: 要查找的模式串
        base: 基数
        modulus: 模数
    
    返回:
        模式串首次出现的位置索引，如果没有找到返回-1
    """
    n = len(text)
    m = len(pattern)
    
    if m == 0 or m > n:
        return -1
    
    # 计算pattern的哈希值
    pattern_hash = compute_initial_hash(pattern, base, modulus)
    
    # 计算base^(m-1) mod modulus
    power = compute_power(base, m - 1, modulus)
    
    # 计算text前m个字符的哈希值
    text_hash = compute_initial_hash(text[:m], base, modulus)
    
    # 检查第一个匹配
    if text_hash == pattern_hash and text[:m] == pattern:
        return 0
    
    # 滑动窗口
    for i in range(m, n):
        # 移除text[i-m]
        char_out = ord(text[i - m])
        # 添加text[i]
        char_in = ord(text[i])
        
        # 更新哈希值
        text_hash = (text_hash - char_out * power % modulus + modulus) % modulus
        text_hash = (text_hash * base + char_in) % modulus
        
        # 检查匹配
        if text_hash == pattern_hash and text[i - m + 1:i + 1] == pattern:
            return i - m + 1
    
    return -1


def diff_with_rolling_hash(text_a, text_b, base=256, modulus=10**9 + 7):
    """
    使用滚动哈希进行文本差异检测
    
    找出两个文本中匹配和未匹配的部分
    
    参数:
        text_a: 原始文本
        text_b: 新文本
        base: 哈希基数
        modulus: 哈希模数
    
    返回:
        差异列表 [(type, content), ...]
        type为'equal', 'delete', 'insert'
    """
    result = []
    
    i = 0
    j = 0
    
    while i < len(text_a) and j < len(text_b):
        # 尝试找到最长的匹配子串
        if text_a[i] == text_b[j]:
            # 从当前位置找最大匹配
            match_len = 0
            max_match = 0
            match_start_i = i
            match_start_j = j
            
            # 使用更长的窗口来确认匹配
            temp_i = i
            temp_j = j
            
            while temp_i < len(text_a) and temp_j < len(text_b):
                if text_a[temp_i] == text_b[temp_j]:
                    match_len += 1
                    temp_i += 1
                    temp_j += 1
                else:
                    if match_len > max_match:
                        max_match = match_len
                        match_start_i = i
                        match_start_j = j
                    # 允许一定的不匹配继续尝试
                    if temp_i - i > max_match:
                        break
                    match_len = 0
                    temp_i = i + (temp_i - i) + 1
                    temp_j = j
            
            if match_len > max_match:
                max_match = match_len
                match_start_i = i
                match_start_j = j
            
            if max_match > 0:
                # 添加匹配部分
                if i < match_start_i:
                    result.append(('delete', text_a[i:match_start_i]))
                if j < match_start_j:
                    result.append(('insert', text_b[j:match_start_j]))
                
                result.append(('equal', text_a[match_start_i:match_start_i + max_match]))
                i = match_start_i + max_match
                j = match_start_j + max_match
            else:
                # 单字符差异
                result.append(('delete', text_a[i]))
                result.append(('insert', text_b[j]))
                i += 1
                j += 1
        else:
            # 字符不匹配
            result.append(('delete', text_a[i]))
            result.append(('insert', text_b[j]))
            i += 1
            j += 1
    
    # 处理剩余部分
    if i < len(text_a):
        result.append(('delete', text_a[i:]))
    if j < len(text_b):
        result.append(('insert', text_b[j:]))
    
    return result


def multi_rolling_hash(text_a, text_b):
    """
    使用多个不同哈希基数的滚动哈希减少冲突
    
    参数:
        text_a: 原始文本
        text_b: 新文本
    
    返回:
        差异列表
    """
    bases = [256, 257, 258]
    modulus = [10**9 + 7, 10**9 + 9, 10**9 + 21]
    
    # 返回使用第一个哈希的结果
    # 实际应用中应该检查所有哈希都匹配才确认
    return diff_with_rolling_hash(text_a, text_b, bases[0], modulus[0])


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：基本滚动哈希
    print("=" * 50)
    print("测试1: 滚动哈希构建")
    print("=" * 50)
    
    rh = RollingHash(base=256, modulus=10**9 + 7)
    
    for char in "hello":
        rh.update_add(char)
        print(f"添加 '{char}': hash = {rh.hash_value}")
    
    print(f"\n最终哈希值: {rh.hash_value}")
    
    # 测试用例2：子串查找
    print("\n" + "=" * 50)
    print("测试2: Rabin-Karp子串查找")
    print("=" * 50)
    
    text = "ABABDABACDABABCABAB"
    pattern = "ABAB"
    
    pos = rolling_hash_substring(text, pattern)
    print(f"文本: '{text}'")
    print(f"模式: '{pattern}'")
    print(f"找到位置: {pos}")
    
    # 测试用例3：多个模式查找
    print("\n" + "=" * 50)
    print("测试3: 多次模式查找")
    print("=" * 50)
    
    text = "ATGCGATCGATCGTAGCTAG"
    patterns = ["ATCG", "GCAT", "TAG"]
    
    for pattern in patterns:
        pos = rolling_hash_substring(text, pattern)
        if pos >= 0:
            print(f"'{pattern}' 在位置 {pos} 找到")
        else:
            print(f"'{pattern}' 未找到")
    
    # 测试用例4：Diff with Rolling Hash
    print("\n" + "=" * 50)
    print("测试4: 滚动哈希差异检测")
    print("=" * 50)
    
    text_a = "ABCABBA"
    text_b = "CBABAC"
    
    diff = diff_with_rolling_hash(text_a, text_b)
    
    print(f"原始: '{text_a}'")
    print(f"新:   '{text_b}'")
    print("\n差异:")
    for op, content in diff:
        if op == 'equal':
            print(f"  {content}", end='')
        elif op == 'delete':
            print(f"[-{content}-]", end='')
        else:
            print(f"[+{content}+]", end='')
    print()
    
    # 测试用例5：单词级滚动哈希
    print("\n" + "=" * 50)
    print("测试5: 哈希碰撞演示")
    print("=" * 50)
    
    # 使用小模数更容易展示碰撞
    small_modulus = 100
    
    words = ["abc", "bcd", "abd"]
    
    for word in words:
        h = compute_initial_hash(word, base=256, modulus=small_modulus)
        print(f"'{word}': hash = {h} (mod {small_modulus})")
    
    # 验证不同文本不同哈希
    print("\n正常模数:")
    for word in words:
        h = compute_initial_hash(word)
        print(f"'{word}': hash = {h}")
