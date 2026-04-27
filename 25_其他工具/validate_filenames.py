# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / validate_filenames

本文件实现 validate_filenames 相关的算法功能。
"""

#!/usr/bin/env python3
"""
==============================================================
其他工具 - Validate Filenames（文件名验证）
==============================================================
验证文件名是否符合规范：
- 不能包含大写字母
- 不能包含空格
- 不能包含连字符（除非在 site-packages 中）
- 必须在目录中（有路径分隔符）

参考：build_directory_md.py 的 good_file_paths()
"""

import os

try:
    from .build_directory_md import good_file_paths
except ImportError:
    from build_directory_md import good_file_paths  # type: ignore[no-redef]


# 获取所有有效文件路径
filepaths = list(good_file_paths())
assert filepaths, "good_file_paths() failed!"

# 检测包含大写字母的文件
if upper_files := [file for file in filepaths if file != file.lower()]:
    print(f"{len(upper_files)} files contain uppercase characters:")
    print("\n".join(upper_files) + "\n")

# 检测包含空格的文件
if space_files := [file for file in filepaths if " " in file]:
    print(f"{len(space_files)} files contain space characters:")
    print("\n".join(space_files) + "\n")

# 检测包含连字符的文件（排除 site-packages）
if hyphen_files := [
    file for file in filepaths if "-" in file and "/site-packages/" not in file
]:
    print(f"{len(hyphen_files)} files contain hyphen characters:")
    print("\n".join(hyphen_files) + "\n")

# 检测不在目录中的文件
if nodir_files := [file for file in filepaths if os.sep not in file]:
    print(f"{len(nodir_files)} files are not in a directory:")
    print("\n".join(nodir_files) + "\n")

# 如果有违规文件，报告错误数量
if bad_files := len(upper_files + space_files + hyphen_files + nodir_files):
    import sys

    sys.exit(bad_files)


# ==========================================================
# 测试代码
# ==========================================================
if __name__ == "__main__":
    print("文件名验证完成！")
