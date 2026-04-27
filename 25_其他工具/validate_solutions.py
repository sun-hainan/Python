# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / validate_solutions

本文件实现 validate_solutions 相关的算法功能。
"""

#!/usr/bin/env python3
"""
==============================================================
其他工具 - Project Euler 解答验证
==============================================================
验证 Project Euler 各题目的解答是否正确。

工作原理：
1. 加载预计算的答案哈希（scripts/project_euler_answers.json）
2. 遍历 solution 目录中的 Python 文件
3. 执行每个 solution() 函数
4. 比较答案哈希（SHA-256）

依赖：
- httpx: 用于 GitHub API 请求
- pytest: 用于测试框架

参考：Project Euler (https://projecteuler.net/)
"""

# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "httpx",
#     "pytest",
# ]
# ///

import hashlib
import importlib.util
import json
import os
import pathlib
from types import ModuleType

import httpx
import pytest

# Project Euler 目录和答案文件路径
PROJECT_EULER_DIR_PATH = pathlib.Path.cwd().joinpath("project_euler")
PROJECT_EULER_ANSWERS_PATH = pathlib.Path.cwd().joinpath(
    "scripts", "project_euler_answers.json"
)

with open(PROJECT_EULER_ANSWERS_PATH) as file_handle:
    PROBLEM_ANSWERS: dict[str, str] = json.load(file_handle)


def convert_path_to_module(file_path: pathlib.Path) -> ModuleType:
    """
    将文件路径转换为 Python 模块。
    
    Args:
        file_path: .py 文件路径
    
    Returns:
        加载后的模块对象
    """
    spec = importlib.util.spec_from_file_location(file_path.name, str(file_path))
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def all_solution_file_paths() -> list[pathlib.Path]:
    """
    收集所有解答文件路径。
    
    Returns:
        所有 .py 解答文件的路径列表
    """
    solution_file_paths = []
    for problem_dir_path in PROJECT_EULER_DIR_PATH.iterdir():
        if problem_dir_path.is_file() or problem_dir_path.name.startswith("_"):
            continue
        for file_path in problem_dir_path.iterdir():
            if file_path.suffix != ".py" or file_path.name.startswith(("_", "test")):
                continue
            solution_file_paths.append(file_path)
    return solution_file_paths


def get_files_url() -> str:
    """
    获取 GitHub PR 的文件列表 URL。
    
    Returns:
        PR 文件 API 的 URL
    """
    with open(os.environ["GITHUB_EVENT_PATH"]) as file:
        event = json.load(file)
    return event["pull_request"]["url"] + "/files"


def added_solution_file_path() -> list[pathlib.Path]:
    """
    获取当前 PR 中新增的解答文件路径。
    
    仅在 GitHub Actions 中运行。
    
    Returns:
        新增的解答文件路径列表
    """
    solution_file_paths = []
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": "token " + os.environ["GITHUB_TOKEN"],
    }
    files = httpx.get(get_files_url(), headers=headers, timeout=10).json()
    for file in files:
        filepath = pathlib.Path.cwd().joinpath(file["filename"])
        if (
            filepath.suffix != ".py"
            or filepath.name.startswith(("_", "test"))
            or not filepath.name.startswith("sol")
        ):
            continue
        solution_file_paths.append(filepath)
    return solution_file_paths


def collect_solution_file_paths() -> list[pathlib.Path]:
    """
    收集要测试的解答文件路径。
    
    若在 PR 中运行，只测试新增文件；否则测试所有文件。
    
    Returns:
        解答文件路径列表
    """
    if (
        os.environ.get("CI")
        and os.environ.get("GITHUB_EVENT_NAME") == "pull_request"
        and (filepaths := added_solution_file_path())
    ):
        return filepaths
    return all_solution_file_paths()


@pytest.mark.parametrize(
    "solution_path",
    collect_solution_file_paths(),
    ids=lambda path: f"{path.parent.name}/{path.name}",
)
def test_project_euler(solution_path: pathlib.Path) -> None:
    """
    测试 Project Euler 解答是否正确。
    
    Args:
        solution_path: 解答文件路径
    """
    # 从目录名提取题号（如 problem_001 -> 001）
    problem_number: str = solution_path.parent.name[8:].zfill(3)
    expected: str = PROBLEM_ANSWERS[problem_number]
    
    # 执行解答
    solution_module = convert_path_to_module(solution_path)
    answer = str(solution_module.solution())
    answer = hashlib.sha256(answer.encode()).hexdigest()
    
    # 验证答案哈希
    assert answer == expected, (
        f"Expected solution to {problem_number} to have hash {expected}, got {answer}"
    )
if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
