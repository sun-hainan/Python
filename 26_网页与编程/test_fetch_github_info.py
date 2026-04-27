# -*- coding: utf-8 -*-
"""
算法实现：26_网页与编程 / test_fetch_github_info

本文件实现 test_fetch_github_info 相关的算法功能。
"""

import json

import httpx

from .fetch_github_info import AUTHENTICATED_USER_ENDPOINT, fetch_github_info


# GitHub信息获取测试
def test_fetch_github_info(monkeypatch):
# FakeResponse 类
    class FakeResponse:
        def __init__(self, content) -> None:
            assert isinstance(content, (bytes, str))
            self.content = content

# json 算法
        def json(self):
            return json.loads(self.content)

# mock_response 算法
    def mock_response(*args, **kwargs):
        assert args[0] == AUTHENTICATED_USER_ENDPOINT
        assert "Authorization" in kwargs["headers"]
        assert kwargs["headers"]["Authorization"].startswith("token ")
        assert "Accept" in kwargs["headers"]
        return FakeResponse(b'{"login":"test","id":1}')

    monkeypatch.setattr(httpx, "get", mock_response)
    result = fetch_github_info("token")
    assert result["login"] == "test"
    assert result["id"] == 1

if __name__ == '__main__':
    # 测试 test_fetch_github_info
    print(f'Testing {__name__}...')
    # TODO: 添加测试用例
    print('测试完成')
