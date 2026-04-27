# -*- coding: utf-8 -*-
"""
算法实现：差异理论 / patch_generation

本文件实现 patch_generation 相关的算法功能。
"""

import difflib
import re


def generate_unified_diff(original_lines, new_lines, original_name="original.txt", new_name="new.txt", context=3):
    """
    生成统一diff格式的补丁
    
    参数:
        original_lines: 原始文件内容的行列表
        new_lines: 新文件内容的行列表
        original_name: 原始文件名
        new_name: 新文件名
        context: 上下文行数（前后各显示多少行）
    
    返回:
        统一diff格式的字符串
    """
    # 使用difflib生成差异
    matcher = difflib.SequenceMatcher(None, original_lines, new_lines)
    
    # 生成差异块
    diff_blocks = []
    for group in matcher.get_grouped_opcodes(context):
        # 计算hunk的头部和尾部位置
        i1, i2, j1, j2 = group
        
        # 检查第一个和最后一个opcode的类型
        # 用于确定是否需要在前面添加"起始于"标记
        first_op = matcher.opcodes[matcher.matching_blocks[0][0]] if matcher.matching_blocks else None
        
        # 构建hunk
        hunk_lines = []
        
        # Hunk头部：@@ -i1,i2 +j1,j2 @@
        # 计算原始文件中的行范围
        original_start = i1 + 1  # 转换为1-based
        original_count = i2 - i1
        # 计算新文件中的行范围
        new_start = j1 + 1
        new_count = j2 - j1
        
        hunk_header = f"@@ -{original_start},{original_count} +{new_start},{new_count} @@"
        hunk_lines.append(hunk_header)
        
        # 添加变更行
        for tag, i1, i2, j1, j2 in [group]:
            pass  # 已经在循环中处理
        
        # 遍历原始文件的变更
        for tag, i1, i2, j1, j2 in [group]:
            if tag == 'equal':
                # 未修改的行（上下文）
                for i in range(i1, i2):
                    hunk_lines.append(f" {original_lines[i]}")
            elif tag == 'delete':
                # 删除的行
                for i in range(i1, i2):
                    hunk_lines.append(f"-{original_lines[i]}")
            elif tag == 'insert':
                # 插入的行
                for j in range(j1, j2):
                    hunk_lines.append(f"+{new_lines[j]}")
            elif tag == 'replace':
                # 替换：先删除后添加
                for i in range(i1, i2):
                    hunk_lines.append(f"-{original_lines[i]}")
                for j in range(j1, j2):
                    hunk_lines.append(f"+{new_lines[j]}")
        
        diff_blocks.append('\n'.join(hunk_lines))
    
    # 构建完整的diff
    result = []
    result.append(f"--- {original_name}")
    result.append(f"+++ {new_name}")
    result.append('\n'.join(diff_blocks))
    
    return '\n'.join(result)


def parse_diff_line(line):
    """
    解析单行diff内容
    
    参数:
        line: diff中的一行
    
    返回:
        (status, content)元组
        status: 'add'(+), 'delete'(-), 'context'( ), None(其他)
    """
    if not line:
        return None, ''
    
    if line[0] == '+':
        return 'add', line[1:]
    elif line[0] == '-':
        return 'delete', line[1:]
    elif line[0] == ' ':
        return 'context', line[1:]
    elif line.startswith('@@'):
        return 'header', line
    elif line.startswith('---') or line.startswith('+++'):
        return 'file_header', line
    else:
        return None, line


def apply_patch(original_lines, patch_content):
    """
    将补丁应用到原始文件
    
    参数:
        original_lines: 原始文件内容的行列表
        patch_content: 补丁内容（统一diff格式字符串）
    
    返回:
        应用补丁后的文件内容行列表
    
    异常:
        ValueError: 补丁格式错误或无法应用
    """
    lines = patch_content.split('\n')
    result_lines = []
    
    # 跳过文件头
    i = 0
    while i < len(lines) and not lines[i].startswith('@@'):
        i += 1
    
    if i >= len(lines):
        raise ValueError("Invalid patch format: no hunk header found")
    
    # 解析每个hunk
    while i < len(lines):
        line = lines[i]
        
        if line.startswith('@@'):
            # 解析hunk头: @@ -start,count +start,count @@
            match = re.match(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@', line)
            if not match:
                raise ValueError(f"Invalid hunk header: {line}")
            
            orig_start = int(match.group(1)) - 1  # 转换为0-based
            orig_count = int(match.group(2))
            new_start = int(match.group(3)) - 1
            new_count = int(match.group(4))
            
            # 将结果行指针设置到正确位置
            # 首先添加原始文件中hunk之前的行
            result_idx = len(result_lines)
            while result_idx < orig_start:
                if result_idx < len(original_lines):
                    result_lines.append(original_lines[result_idx])
                result_idx += 1
            
            i += 1
            
            # 处理hunk内容
            orig_pos = orig_start
            while i < len(lines) and not lines[i].startswith('@@') and not lines[i].startswith('---'):
                diff_line = lines[i]
                
                if diff_line.startswith('+'):
                    # 添加行（来自新文件）
                    result_lines.append(diff_line[1:])
                elif diff_line.startswith('-'):
                    # 删除行（跳过原始文件的行）
                    orig_pos += 1
                elif diff_line.startswith(' '):
                    # 上下文行：复制原始文件的行
                    result_lines.append(diff_line[1:])
                    orig_pos += 1
                elif diff_line.startswith('\\'):
                    # 这是difflib添加的"删除末尾空白"标记
                    pass
                else:
                    # 其他内容，可能是空行或未知格式
                    if diff_line == '':
                        result_lines.append('')
                
                i += 1
            
            # 如果hunk结束时还没有处理完所有上下文
            while orig_pos < orig_start + orig_count:
                if orig_pos < len(original_lines):
                    result_lines.append(original_lines[orig_pos])
                orig_pos += 1
        else:
            i += 1
    
    # 添加原始文件中hunk之后的所有行
    while len(result_lines) < len(original_lines):
        result_lines.append(original_lines[len(result_lines)])
    
    return result_lines


def reverse_patch(patch_content):
    """
    反转补丁（从新版本恢复到原始版本）
    
    参数:
        patch_content: 原始补丁内容
    
    返回:
        反转后的补丁内容
    """
    lines = patch_content.split('\n')
    result = []
    
    for line in lines:
        if line.startswith('+++'):
            # 交换文件头
            result.append(line.replace('+++', '---'))
        elif line.startswith('---'):
            result.append(line.replace('---', '+++'))
        elif line.startswith('+'):
            # 添加变成删除
            result.append('-' + line[1:])
        elif line.startswith('-'):
            # 删除变成添加
            result.append('+' + line[1:])
        else:
            result.append(line)
    
    return '\n'.join(result)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：基本的行添加
    print("=" * 50)
    print("测试1: 基本行添加")
    print("=" * 50)
    
    original = [
        "line 1",
        "line 2",
        "line 3",
        "line 4",
        "line 5"
    ]
    new = [
        "line 1",
        "line 2",
        "new line",
        "line 3",
        "line 4",
        "line 5"
    ]
    
    patch = generate_unified_diff(original, new, "test.txt", "test_new.txt")
    print("生成的补丁:")
    print(patch)
    
    # 应用补丁
    applied = apply_patch(original, patch)
    print("\n应用补丁后的内容:")
    for i, line in enumerate(applied):
        print(f"{i+1}: {line}")
    
    # 测试用例2：行删除
    print("\n" + "=" * 50)
    print("测试2: 行删除")
    print("=" * 50)
    
    original = [
        "header",
        "line 1",
        "line 2",
        "line 3",
        "footer"
    ]
    new = [
        "header",
        "line 1",
        "line 3",
        "footer"
    ]
    
    patch = generate_unified_diff(original, new)
    print("删除行的补丁:")
    print(patch)
    
    # 测试用例3：行修改
    print("\n" + "=" * 50)
    print("测试3: 行修改")
    print("=" * 50)
    
    original = [
        "def hello():",
        "    print('old')",
        "    return 1"
    ]
    new = [
        "def hello():",
        "    print('new')",
        "    return 2"
    ]
    
    patch = generate_unified_diff(original, new)
    print("修改行的补丁:")
    print(patch)
    
    # 测试用例4：反转补丁
    print("\n" + "=" * 50)
    print("测试4: 补丁反转")
    print("=" * 50)
    
    original = ["a", "b", "c"]
    new = ["a", "x", "c"]
    
    patch = generate_unified_diff(original, new)
    print("原始补丁:")
    print(patch)
    
    reversed_patch = reverse_patch(patch)
    print("\n反转后的补丁:")
    print(reversed_patch)
    
    # 测试用例5：多hunk补丁
    print("\n" + "=" * 50)
    print("测试5: 多处修改")
    print("=" * 50)
    
    original = ["a", "b", "c", "d", "e", "f", "g"]
    new = ["a", "x", "c", "d", "y", "f", "g"]
    
    patch = generate_unified_diff(original, new, context=1)
    print("多处修改的补丁:")
    print(patch)
