# -*- coding: utf-8 -*-
"""
位向量理论(BitVector)求解器
功能：实现固定宽度二进制向量的运算和约束

位向量运算：
- 算术: bvadd, bvsub, bvmul, bvudiv, bvurem, bvneg
- 位运算: bvand, bvor, bvnot, bvxor, bvshl, bvlshr
- 比较: bvult, bvule, bvugt, bvuge, (=)
- 扩展: zext(零扩展), sext(符号扩展)
- 切片: concat, extract

作者：BitVector Theory Team
"""

from typing import List, Dict, Tuple, Optional, Any


class BitVector:
    """位向量：固定宽度二进制数据"""
    
    def __init__(self, value: int, width: int):
        """
        Args:
            value: 整数值
            width: 位宽（比特数）
        """
        self.width = width
        # 截断到指定宽度
        mask = (1 << width) - 1
        self.value = value & mask
    
    def __repr__(self):
        return f"bv{self.width}[{self.value}]"
    
    def __int__(self):
        return self.value
    
    def to_binary_string(self) -> str:
        """转换为二进制字符串"""
        return format(self.value, f'0{self.width}b')
    
    # 算术运算
    def bvadd(self, other: 'BitVector') -> 'BitVector':
        result = (self.value + other.value) & ((1 << self.width) - 1)
        return BitVector(result, self.width)
    
    def bvsub(self, other: 'BitVector') -> 'BitVector':
        result = (self.value - other.value) & ((1 << self.width) - 1)
        return BitVector(result, self.width)
    
    def bvmul(self, other: 'BitVector') -> 'BitVector':
        result = (self.value * other.value) & ((1 << self.width) - 1)
        return BitVector(result, self.width)
    
    def bvneg(self) -> 'BitVector':
        result = (-self.value) & ((1 << self.width) - 1)
        return BitVector(result, self.width)
    
    # 位运算
    def bvand(self, other: 'BitVector') -> 'BitVector':
        result = self.value & other.value
        return BitVector(result, self.width)
    
    def bvor(self, other: 'BitVector') -> 'BitVector':
        result = self.value | other.value
        return BitVector(result, self.width)
    
    def bvnot(self) -> 'BitVector':
        mask = (1 << self.width) - 1
        result = (~self.value) & mask
        return BitVector(result, self.width)
    
    def bvxor(self, other: 'BitVector') -> 'BitVector':
        result = self.value ^ other.value
        return BitVector(result, self.width)
    
    def bvshl(self, other: 'BitVector') -> 'BitVector':
        shift = other.value % self.width
        result = (self.value << shift) & ((1 << self.width) - 1)
        return BitVector(result, self.width)
    
    def bvlshr(self, other: 'BitVector') -> 'BitVector':
        shift = other.value % self.width
        result = self.value >> shift
        return BitVector(result, self.width)
    
    # 比较运算
    def bvult(self, other: 'BitVector') -> bool:
        return self.value < other.value
    
    def bvule(self, other: 'BitVector') -> bool:
        return self.value <= other.value
    
    # 扩展运算
    def zext(self, new_width: int) -> 'BitVector':
        """零扩展：高位补0"""
        return BitVector(self.value, new_width)
    
    def sext(self, new_width: int) -> 'BitVector':
        """符号扩展：高位补符号位"""
        sign_bit = (self.value >> (self.width - 1)) & 1
        if sign_bit == 0:
            return self.zext(new_width)
        mask = (1 << self.width) - 1
        ext_mask = ((1 << new_width) - 1) ^ mask
        return BitVector(self.value | ext_mask, new_width)
    
    # 切片和连接
    def extract(self, high: int, low: int) -> 'BitVector':
        """提取位: result[i] = self[low+i]"""
        mask = (1 << (high - low + 1)) - 1
        result = (self.value >> low) & mask
        return BitVector(result, high - low + 1)
    
    @staticmethod
    def concat(high: 'BitVector', low: 'BitVector') -> 'BitVector':
        """连接两个位向量"""
        new_width = high.width + low.width
        result = (high.value << low.width) | low.value
        return BitVector(result, new_width)


class BitVectorExpr:
    """位向量表达式基类"""
    pass


class BVVar(BitVectorExpr):
    """位向量变量"""
    def __init__(self, name: str, width: int):
        self.name = name
        self.width = width


class BVConst(BitVectorExpr):
    """位向量常量"""
    def __init__(self, value: int, width: int):
        self.value = value
        self.width = width


class BVAdd(BitVectorExpr):
    def __init__(self, left: BitVectorExpr, right: BitVectorExpr):
        self.left = left
        self.right = right
        self.width = left.width


class BVSub(BitVectorExpr):
    def __init__(self, left: BitVectorExpr, right: BitVectorExpr):
        self.left = left
        self.right = right
        self.width = left.width


class BVMul(BitVectorExpr):
    def __init__(self, left: BitVectorExpr, right: BitVectorExpr):
        self.left = left
        self.right = right
        self.width = left.width


class BVNot(BitVectorExpr):
    def __init__(self, arg: BitVectorExpr):
        self.arg = arg
        self.width = arg.width


class BVAnd(BitVectorExpr):
    def __init__(self, left: BitVectorExpr, right: BitVectorExpr):
        self.left = left
        self.right = right
        self.width = left.width


class BVOr(BitVectorExpr):
    def __init__(self, left: BitVectorExpr, right: BitVectorExpr):
        self.left = left
        self.right = right
        self.width = left.width


class BVShl(BitVectorExpr):
    def __init__(self, left: BitVectorExpr, right: BitVectorExpr):
        self.left = left
        self.right = right
        self.width = left.width


class BVLshr(BitVectorExpr):
    def __init__(self, left: BitVectorExpr, right: BitVectorExpr):
        self.left = left
        self.right = right
        self.width = left.width


class BVZext(BitVectorExpr):
    def __init__(self, arg: BitVectorExpr, new_width: int):
        self.arg = arg
        self.width = new_width


class BVExtract(BitVectorExpr):
    def __init__(self, arg: BitVectorExpr, high: int, low: int):
        self.arg = arg
        self.high = high
        self.low = low
        self.width = high - low + 1


class BitVectorSolver:
    """
    位向量理论求解器
    
    使用符号执行求值位向量表达式
    简化版本：具体求值（所有变量必须被赋值）
    """

    def __init__(self):
        self.assignment: Dict[str, BitVector] = {}
        self.constraints: List[Tuple[BitVectorExpr, BitVectorExpr, str]] = []  # (lhs, rhs, rel)

    def assign(self, name: str, bv: BitVector):
        """变量赋值"""
        self.assignment[name] = bv

    def add_constraint(self, lhs: BitVectorExpr, rhs: BitVectorExpr, rel: str = '='):
        """添加约束"""
        self.constraints.append((lhs, rhs, rel))

    def _eval(self, expr: BitVectorExpr) -> Optional[BitVector]:
        """递归求值表达式"""
        if isinstance(expr, BVConst):
            return BitVector(expr.value, expr.width)
        
        if isinstance(expr, BVVar):
            return self.assignment.get(expr.name)
        
        if isinstance(expr, BVAdd):
            left = self._eval(expr.left)
            right = self._eval(expr.right)
            if left and right:
                return left.bvadd(right)
        
        if isinstance(expr, BVSub):
            left = self._eval(expr.left)
            right = self._eval(expr.right)
            if left and right:
                return left.bvsub(right)
        
        if isinstance(expr, BVMul):
            left = self._eval(expr.left)
            right = self._eval(expr.right)
            if left and right:
                return left.bvmul(right)
        
        if isinstance(expr, BVNot):
            arg = self._eval(expr.arg)
            if arg:
                return arg.bvnot()
        
        if isinstance(expr, BVAnd):
            left = self._eval(expr.left)
            right = self._eval(expr.right)
            if left and right:
                return left.bvand(right)
        
        if isinstance(expr, BVOr):
            left = self._eval(expr.left)
            right = self._eval(expr.right)
            if left and right:
                return left.bvor(right)
        
        if isinstance(expr, BVShl):
            left = self._eval(expr.left)
            right = self._eval(expr.right)
            if left and right:
                return left.bvshl(right)
        
        if isinstance(expr, BVLshr):
            left = self._eval(expr.left)
            right = self._eval(expr.right)
            if left and right:
                return left.bvlshr(right)
        
        if isinstance(expr, BVZext):
            arg = self._eval(expr.arg)
            if arg:
                return arg.zext(expr.width)
        
        if isinstance(expr, BVExtract):
            arg = self._eval(expr.arg)
            if arg:
                return arg.extract(expr.high, expr.low)
        
        return None

    def check_sat(self) -> bool:
        """检查约束是否满足"""
        for lhs, rhs, rel in self.constraints:
            lv = self._eval(lhs)
            rv = self._eval(rhs)
            
            if lv is None or rv is None:
                continue  # 无法求值
            
            if rel == '=':
                if lv.value != rv.value:
                    return False
            elif rel == 'bvult':
                if not lv.bvult(rv):
                    return False
            elif rel == 'bvule':
                if not lv.bvule(rv):
                    return False
        
        return True


def example_bv_arith():
    """位向量算术示例"""
    solver = BitVectorSolver()
    
    x = BVVar("x", 8)
    y = BVVar("y", 8)
    
    # x = 10, y = 20
    solver.assign("x", BitVector(10, 8))
    solver.assign("y", BitVector(20, 8))
    
    # z = x + y
    z_expr = BVAdd(x, y)
    z_val = solver._eval(z_expr)
    
    print(f"8位向量: 10 + 20 = {z_val.value} ({z_val.to_binary_string()})")


def example_bv_bitwise():
    """位向量位操作示例"""
    solver = BitVectorSolver()
    
    x = BVVar("x", 8)
    solver.assign("x", BitVector(0b10101010, 8))
    
    not_x = solver._eval(BVNot(x))
    and_x = solver._eval(BVAnd(x, BVConst(0b11110000, 8)))
    or_x = solver._eval(BVOr(x, BVConst(0b00001111, 8)))
    
    print(f"x = 10101010")
    print(f"~x = {not_x.to_binary_string()}")
    print(f"x & 11110000 = {and_x.to_binary_string()}")
    print(f"x | 00001111 = {or_x.to_binary_string()}")


def example_bv_extract():
    """位提取示例"""
    x = BitVector(0b1111000011110000, 16)
    
    # 提取高8位
    high = x.extract(15, 8)
    # 提取低8位
    low = x.extract(7, 0)
    
    print(f"16位: 1111000011110000")
    print(f"高8位: {high.to_binary_string()}")
    print(f"低8位: {low.to_binary_string()}")
    
    # 连接
    reconcat = BitVector.concat(high, low)
    print(f"重连: {reconcat.to_binary_string()}")


if __name__ == "__main__":
    print("=" * 50)
    print("位向量理论求解器 测试")
    print("=" * 50)
    
    example_bv_arith()
    print()
    example_bv_bitwise()
    print()
    example_bv_extract()
