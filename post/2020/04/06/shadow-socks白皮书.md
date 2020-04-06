[TOC]



# Shadowsocks:  一个安全socks5代理

 <center>S.D.T</center>
<center>January 4, 2019</center>
## 1 概述

Shadowsocks (后面简称ss)是一个基于[SOCKS5](https://tools.ietf.org/html/rfc1928)的安全代理。

`客户端 <---> ss-client <--[加密传输]--> SS-server <---> 受限主机`

ss-client 扮演了传统上的SOCKS5代理服务的功能，ss-client加密并转发客户端的数据到ss-server，ss-server将会解密并转发数据到远端受限的主机。受限主机的响应将会被ss-server加密并转发给ss-client， 最后客户端解密并发送数据到发起请求的客户端。



### 1.1 地址

代表ss服务的地址和SOCKS5的地址格式保持一致：

`[1-byte type][variable-length host][2-byte port]`

有三种类型的地址类型被定义：

1. 0x01: host是一个4-byte的IPV4地址。
2. 0x03： host是一个变长字符串。第一个byte是一个变长字符串长度， 接下来是一个最长255-byte的域名。
3. 0x04: host是一个IPV6地址

最后的2-byte port是一个大端模式的无符号整形（big-endian unsigned integer)。



### 1.2 TCP

ss-client初始化一个TCP连接到ss-server, 然后ss-client发送加密的数据流到ss-server, 数据流格式如下：

`[target address][payload]`

以上内容会被客户端加密，加密由ss-server和ss-client配置的加密算法决定(双方算法必须保持一致）。

ss-server收到ss-client发送过来的加密数据，解密之后解析其中的目标地址，并与之简历一个新的TCP连接并转发payload到目标地址。ss-server随后会收到目标地址发送的响应，ss-server把响应内容加密并回传给ss-client，这个过程一致重复直到ss-client关闭连接。



### 1.3 UDP





## 2 数据流加密

数据流加密算法只提供数据保密性，而数据的完整性和正确性并不能保证。用户尽可能使用AEAD算法。

下面的算法提供了合理的保密性。

| 名称             | Key Size | IV Length |
| ---------------- | -------- | --------- |
| aes-128-ctr      | 16       | 16        |
| aes-192-ctr      | 24       | 16        |
| aes-256-ctr      | 32       | 16        |
| aes-128-cfb      | 16       | 16        |
| aes-192-cfb      | 24       | 16        |
| aes-256-cfb      | 32       | 16        |
| camellia-128-cfb | 16       | 16        |
| camellia-192-cfb | 24       | 16        |
| camellia-256-cfb | 32       | 16        |
| chacha20-ietf    | 32       | 12        |



### 2.1 数据流加解密

stream_encrypt是一个这样的加密函数：它接收一个密钥(secret key)，一个初始向量(init vector)，一条数据(message)， 函数输出一条与数据想通长度的密文(ciphertext)，过程表示如下：

`stream_encrypt(secret_key, IV, message)  => ciphertext`



stream_decrypt是一个解密函数，它还原原始的数据（original message)，过程如下：

`stream_decrypt(secret_key, IV, ciphertext) => message`



secret key可以是用户指定，也可以从一个（用户的）密码生成。secret key的生成遵从 OpenSSl里的 EVP_bytesToKey，详情可以参考 https://wiki.openssl.org/index.php/Manual:EVP_BytesToKey(3)



### 2.2 TCP





### 2.3 UDP



