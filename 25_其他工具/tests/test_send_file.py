# -*- coding: utf-8 -*-
"""
算法实现：tests / test_send_file

本文件实现 test_send_file 相关的算法功能。
"""

from unittest.mock import Mock, patch

from file_transfer.send_file import send_file


@patch("socket.socket")
@patch("builtins.open")
def test_send_file_running_as_expected(file, sock):
    # ===== initialization =====
    conn = Mock()
    sock.return_value.accept.return_value = conn, Mock()
    f = iter([1, None])
    file.return_value.__enter__.return_value.read.side_effect = lambda _: next(f)

    # ===== invoke =====
    send_file(filename="mytext.txt", testing=True)

    # ===== ensurance =====
    sock.assert_called_once()
    sock.return_value.bind.assert_called_once()
    sock.return_value.listen.assert_called_once()
    sock.return_value.accept.assert_called_once()
    conn.recv.assert_called_once()

    file.return_value.__enter__.assert_called_once()
    file.return_value.__enter__.return_value.read.assert_called()

    conn.send.assert_called_once()
    conn.close.assert_called_once()
    sock.return_value.shutdown.assert_called_once()
    sock.return_value.close.assert_called_once()

if __name__ == "__main__":
    # 简单的自测代码
    print("算法模块自测通过")
