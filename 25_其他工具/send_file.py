# -*- coding: utf-8 -*-

"""

算法实现：25_其他工具 / send_file



本文件实现 send_file 相关的算法功能。

"""



# send_file 函数实现

def send_file(filename: str = "mytext.txt", testing: bool = False) -> None:

    import socket



    port = 12312  # Reserve a port for your service.

    sock = socket.socket()  # Create a socket object

    host = socket.gethostname()  # Get local machine name

    sock.bind((host, port))  # Bind to the port

    sock.listen(5)  # Now wait for client connection.



    print("Server listening....")



    while True:

    # 条件循环

        conn, addr = sock.accept()  # Establish connection with client.

        print(f"Got connection from {addr}")

        data = conn.recv(1024)

        print(f"Server received: {data = }")



        with open(filename, "rb") as in_file:

            data = in_file.read(1024)

            while data:

    # 条件循环

                conn.send(data)

                print(f"Sent {data!r}")

                data = in_file.read(1024)



        print("Done sending")

        conn.close()

        if testing:  # Allow the test to complete

    # 条件判断

            break



    sock.shutdown(1)

    sock.close()





if __name__ == "__main__":

    # 条件判断

    send_file()

