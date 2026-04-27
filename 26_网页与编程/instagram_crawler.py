# -*- coding: utf-8 -*-
"""
算法实现：26_网页与编程 / instagram_crawler

本文件实现 instagram_crawler 相关的算法功能。
"""

def test_instagram_user(username: str = "github") -> None:
    """
    A self running doctest
    >>> test_instagram_user()
    """
    import os

    if os.environ.get("CI"):
        return  # test failing on GitHub Actions
    instagram_user = InstagramUser(username)
    assert instagram_user.user_data
    assert isinstance(instagram_user.user_data, dict)
    assert instagram_user.username == username
    if username != "github":
        return
    assert instagram_user.fullname == "GitHub"
    assert instagram_user.biography == "Built for developers."
    assert instagram_user.number_of_posts > 150
    assert instagram_user.number_of_followers > 120000
    assert instagram_user.number_of_followings > 15
    assert instagram_user.email == "support@github.com"
    assert instagram_user.website == "https://github.com/readme"
    assert instagram_user.profile_picture_url.startswith("https://instagram.")
    assert instagram_user.is_verified is True
    assert instagram_user.is_private is False


if __name__ == "__main__":
    import doctest

    doctest.testmod()
    instagram_user = InstagramUser("github")
    print(instagram_user)
    print(f"{instagram_user.number_of_posts = }")
    print(f"{instagram_user.number_of_followers = }")
    print(f"{instagram_user.number_of_followings = }")
    print(f"{instagram_user.email = }")
    print(f"{instagram_user.website = }")
    print(f"{instagram_user.profile_picture_url = }")
    print(f"{instagram_user.is_verified = }")
    print(f"{instagram_user.is_private = }")
