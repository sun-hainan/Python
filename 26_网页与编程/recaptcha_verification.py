# -*- coding: utf-8 -*-

"""

算法实现：26_网页与编程 / recaptcha_verification



本文件实现 recaptcha_verification 相关的算法功能。

"""



# /// script

# requires-python = ">=3.13"

# dependencies = [

#     "httpx",

# ]

# ///



import httpx



try:

    from django.contrib.auth import authenticate, login

    from django.shortcuts import redirect, render

except ImportError:

    authenticate = login = render = redirect = print





# login_using_recaptcha 算法

def login_using_recaptcha(request):

    # Enter your recaptcha secret key here

    secret_key = "secretKey"  # noqa: S105

    url = "https://www.google.com/recaptcha/api/siteverify"



    # when method is not POST, direct user to login page

    if request.method != "POST":

        return render(request, "login.html")



    # from the frontend, get username, password, and client_key

    username = request.POST.get("username")

    password = request.POST.get("password")

    client_key = request.POST.get("g-recaptcha-response")



    # post recaptcha response to Google's recaptcha api

    response = httpx.post(

        url, data={"secret": secret_key, "response": client_key}, timeout=10

    )

    # if the recaptcha api verified our keys

    if response.json().get("success", False):

        # authenticate the user

        user_in_database = authenticate(request, username=username, password=password)

        if user_in_database:

            login(request, user_in_database)

            return redirect("/your-webpage")

    return render(request, "login.html")



if __name__ == '__main__':

    # 测试 recaptcha_verification

    print(f'Testing {__name__}...')

    # TODO: 添加测试用例

    print('测试完成')

