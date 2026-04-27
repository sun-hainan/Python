# -*- coding: utf-8 -*-

"""

算法实现：25_其他工具 / receive_file



本文件实现 receive_file 相关的算法功能。

"""



import socket







# main 函数实现

def main():

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    host = socket.gethostname()

    port = 12312



    sock.connect((host, port))

    sock.send(b"Hello server!")



    with open("Received_file", "wb") as out_file:

        print("File opened")

        print("Receiving data...")

        while True:

    # 条件循环

            data = sock.recv(1024)

            if not data:

    # 条件判断

                break

            out_file.write(data)



    print("Successfully received the file")

    sock.close()

    print("Connection closed")





if __name__ == "__main__":

    # 条件判断

    main()

