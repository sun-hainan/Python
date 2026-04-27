# -*- coding: utf-8 -*-
"""
算法实现：26_网页与编程 / fetch_github_info

本文件实现 fetch_github_info 相关的算法功能。
"""

#!/usr/bin/env bash
# -*- coding: utf-8 -*-
"""
fetch_github_info

算法分类：网页与编程
描述：实现 fetch_github_info 算法的核心逻辑。
"""

from __future__ import annotations


"""
Created by sarathkaul on 14/11/19
Updated by lawric1 on 24/11/20

Authentication will be made via access token.
To generate your personal access token visit https://github.com/settings/tokens.

NOTE:
Never hardcode any credential information in the code. Always use an environment
file to store the private information and use the `os` module to get the information
during runtime.

Create a ".env" file in the root directory and write these two lines in that file
with your token::

export USER_TOKEN=""
"""

# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "httpx",
# ]
# ///


import os
from typing import Any

import httpx

BASE_URL = "https://api.github.com"

# https://docs.github.com/en/free-pro-team@latest/rest/reference/users#get-the-authenticated-user
AUTHENTICATED_USER_ENDPOINT = BASE_URL + "/user"

# https://github.com/settings/tokens
USER_TOKEN = os.environ.get("USER_TOKEN", "")


def fetch_github_info(auth_token: str) -> dict[Any, Any]:
    """
    Fetch GitHub info of a user using the httpx module
    """
    headers = {
        "Authorization": f"token {auth_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    return httpx.get(AUTHENTICATED_USER_ENDPOINT, headers=headers, timeout=10).json()


if __name__ == "__main__":  # pragma: no cover
    if USER_TOKEN:
        for key, value in fetch_github_info(USER_TOKEN).items():
            print(f"{key}: {value}")
    else:
        raise ValueError("'USER_TOKEN' field cannot be empty.")
