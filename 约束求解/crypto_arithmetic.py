# -*- coding: utf-8 -*-
"""
算法实现：约束求解 / crypto_arithmetic

本文件实现 crypto_arithmetic 相关的算法功能。
"""

from typing import List, Dict, Set, Optional, Tuple
import itertools


class AlphameticSolver:
    """
    密码算术问题求解器
    将字母算术问题转换为CSP并求解
    """
    
    def __init__(self):
        self.letters: Set[str] = set()
        self.words: List[str] = []
        self.result_word: str = ""
    
    def parse_equation(self, equation: str):
        """
        解析字母算术方程
        
        Args:
            equation: 形如 "SEND + MORE = MONEY" 的方程
        """
        # 分割方程
        parts = equation.replace('+', '=').split('=')
        self.words = [w.strip() for w in parts[:-1]]
        self.result_word = parts[-1].strip()
        
        # 收集所有字母
        self.letters = set()
        for word in self.words + [self.result_word]:
            self.letters.update(word.upper())
    
    def solve(self, base: int = 10) -> Optional[Dict[str, int]]:
        """
        求解密码算术问题
        
        Args:
            base: 进制(默认为10)
        
        Returns:
            字母到数字的映射或None
        """
        if not self.letters:
            return None
        
        letters = sorted(list(self.letters))
        n_letters = len(letters)
        
        # 获取每个字母的位置权重
        def get_weight(word: str) -> Dict[str, int]:
            """计算每个字母的权重(在某个位置出现的次数)"""
            weight = {c: 0 for c in letters}
            for pos, char in enumerate(reversed(word.upper())):
                weight[char] += pow(base, pos)
            return weight
        
        # 计算所有单词的权重
        word_weights = []
        for word in self.words:
            word_weights.append(get_weight(word))
        result_weights = get_weight(self.result_word)
        
        # 求解线性方程
        # sum(words) * weight = result_word * weight
        # 即 sum(words) - result_word = 0
        
        # 生成系数矩阵
        coefficients = {c: 0 for c in letters}
        for word_weight in word_weights:
            for c in letters:
                coefficients[c] += word_weight[c]
        for c in letters:
            coefficients[c] -= result_weights[c]
        
        # 找出首字母(不能为0)
        leading_letters = set()
        for word in self.words:
            leading_letters.add(word.upper()[0])
        leading_letters.add(self.result_word.upper()[0])
        
        # 暴力搜索(因为变量少)
        for digits in itertools.permutations(range(base), n_letters):
            assignment = {letters[i]: digits[i] for i in range(n_letters)}
            
            # 首字母不能为0
            for lead in leading_letters:
                if lead in assignment and assignment[lead] == 0:
                    break
            else:
                # 计算等式
                left_sum = 0
                for i, word in enumerate(self.words):
                    val = 0
                    for char in word.upper():
                        val = val * base + assignment[char]
                    left_sum += val
                
                right_val = 0
                for char in self.result_word.upper():
                    right_val = right_val * base + assignment[char]
                
                if left_sum == right_val:
                    return assignment
        
        return None
    
    def get_coefficient(self, letter: str, position: int, word: str, is_result: bool = False) -> int:
        """
        获取某字母在某位置的系数
        
        Args:
            letter: 字母
            position: 位置(从右开始,0索引)
            word: 单词
            is_result: 是否是结果单词
        
        Returns:
            系数
        """
        char = word[-(position + 1)].upper() if position < len(word) else None
        if char == letter:
            coeff = pow(10, position)
            return -coeff if is_result else coeff
        return 0


def solve_alphametic(equation: str, base: int = 10) -> Optional[Dict[str, int]]:
    """
    求解密码算术问题的便捷函数
    
    Args:
        equation: 方程字符串
        base: 进制
    
    Returns:
        解或None
    """
    solver = AlphameticSolver()
    solver.parse_equation(equation)
    return solver.solve(base)


def verify_solution(equation: str, assignment: Dict[str, int], base: int = 10) -> Tuple[bool, int, int]:
    """
    验证解的正确性
    
    Args:
        equation: 方程
        assignment: 解
        base: 进制
    
    Returns:
        (是否正确, 左边和, 右边和)
    """
    parts = equation.replace('+', '=').split('=')
    words = [w.strip() for w in parts[:-1]]
    result = parts[-1].strip()
    
    def word_to_num(word: str) -> int:
        val = 0
        for char in word.upper():
            val = val * base + assignment[char]
        return val
    
    left_sum = sum(word_to_num(w) for w in words)
    right_val = word_to_num(result)
    
    return left_sum == right_val, left_sum, right_val


# 测试代码
if __name__ == "__main__":
    # 测试1: SEND + MORE = MONEY
    print("测试1 - SEND + MORE = MONEY:")
    result = solve_alphametic("SEND + MORE = MONEY")
    print(f"  解: {result}")
    
    if result:
        valid, left, right = verify_solution("SEND + MORE = MONEY", result)
        print(f"  验证: {left} = {right}, 正确={valid}")
    
    # 测试2: 简单加法
    print("\n测试2 - A + B = AB (不允许两位数首字母为0):")
    result = solve_alphametic("A + B = AB")
    print(f"  解: {result}")
    
    # 测试3: 三数相加
    print("\n测试3 - A + B + C = ABC:")
    result = solve_alphametic("A + B + C = ABC")
    print(f"  解: {result}")
    
    # 测试4: 更大问题
    print("\n测试4 - CROSS + ROADS = DANGER:")
    result = solve_alphametic("CROSS + ROADS = DANGER")
    print(f"  解: {result}")
    
    if result:
        valid, left, right = verify_solution("CROSS + ROADS = DANGER", result)
        print(f"  验证: {left} = {right}, 正确={valid}")
    
    # 测试5: 减法
    print("\n测试5 - VIM + VIM + VIM = HELM:")
    result = solve_alphametic("VIM + VIM + VIM = HELM")
    print(f"  解: {result}")
    
    # 测试6: 乘法(使用简化版本)
    print("\n测试6 - A * BC = DBC (需要特殊处理):")
    # 对于乘法问题,需要更复杂的建模
    def solve_multiplication():
        """简单乘法求解"""
        # A * BC = DBC
        # 遍历A和B,C,D
        for a in range(1, 10):
            for b in range(10):
                for c in range(10):
                    for d in range(10):
                        if len({a, b, c, d}) != 4:
                            continue
                        bc = b * 10 + c
                        dbc = d * 100 + b * 10 + c
                        if a * bc == dbc:
                            return {'A': a, 'B': b, 'C': c, 'D': d}
        return None
    
    result = solve_multiplication()
    print(f"  解: {result}")
    
    # 测试7: 检查解的唯一性
    print("\n测试7 - 检查解的数量:")
    def count_solutions(equation: str) -> int:
        solver = AlphameticSolver()
        solver.parse_equation(equation)
        
        letters = sorted(list(solver.letters))
        n_letters = len(letters)
        
        count = 0
        leading_letters = set()
        for word in solver.words + [solver.result_word]:
            leading_letters.add(word.upper()[0])
        
        for digits in itertools.permutations(range(10), n_letters):
            assignment = {letters[i]: digits[i] for i in range(n_letters)}
            
            for lead in leading_letters:
                if lead in assignment and assignment[lead] == 0:
                    break
            else:
                def word_to_num(word):
                    val = 0
                    for char in word.upper():
                        val = val * 10 + assignment[char]
                    return val
                
                left_sum = sum(word_to_num(w) for w in solver.words)
                right_val = word_to_num(solver.result_word)
                
                if left_sum == right_val:
                    count += 1
        
        return count
    
    print(f"  SEND + MORE = MONEY 解数量: {count_solutions('SEND + MORE = MONEY')}")
    print(f"  A + B = AB 解数量: {count_solutions('A + B = AB')}")
    
    print("\n所有测试完成!")
