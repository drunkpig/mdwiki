tags: shadowsocks
    代理



[TOC]



# Shadowsocks:  一个安全socks5代理

 <center>S.D.T</center>
<center>January 4, 2019</center>
## 1. 概述

Shadowsocks (后面简称ss)是一个基于[SOCKS5](https://tools.ietf.org/html/rfc1928)的安全代理。

`客户端 <---> ss-client <--[加密传输]--> SS-server <---> 受限主机`

ss-client 扮演了传统上的SOCKS5代理服务的功能，ss-client加密并转发客户端的数据到ss-server，ss-server将会解密并转发数据到远端受限的主机。受限主机的响应将会被ss-server加密并转发给ss-client， 最后客户端解密并发送数据到发起请求的客户端。



### 1.1 ss的地址/寻址方式

代表ss服务的地址和SOCKS5的地址格式保持一致：

`[1-byte type][variable-length host][2-byte port]`

有三种类型的地址类型被定义：

1. 0x01: host是一个4-byte的IPV4地址。
2. 0x03： host是一个变长字符串。第一个byte是一个变长字符串长度， 接下来是一个最长255-byte的域名。
3. 0x04: host是一个IPV6地址。

最后的2-byte port是一个大端模式的无符号整形（big-endian unsigned integer)。



### 1.2 TCP数据寻址

ss-client初始化一个TCP连接到ss-server, 然后ss-client发送加密的数据流到ss-server, 数据流格式如下：

`[target address][payload]`

以上内容会被客户端加密，加密由ss-server和ss-client配置的加密算法决定(双方算法必须保持一致）。

ss-server收到ss-client发送过来的加密数据，解密之后解析其中的目标地址，并与之简历一个新的TCP连接并转发payload到目标地址。ss-server随后会收到目标地址发送的响应，ss-server把响应内容加密并回传给ss-client，这个过程一致重复直到ss-client关闭连接。



### 1.3 UDP数据寻址





## 2. 数据流加密

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



secret key可以是用户指定，也可以从一个（用户的）密码生成。secret key的生成遵从 OpenSSl里的 [EVP_bytesToKe](https://www.openssl.org/docs/man1.0.2/man3/EVP_BytesToKey.html)，详情可以参考 https://wiki.openssl.org/index.php/Manual:EVP_BytesToKey(3)



### 2.2 TCP

密文流由一个随机生成的IV紧跟着被加密的payload data组成：

`[IV][encrypted payload]`



### 2.3 UDP

`[IV][encrypted payload]`



## 3. AEAD 密码

[AEAD](https://en.wikipedia.org/wiki/Authenticated_encryption),  ([这篇讲的更好点](https://zhuanlan.zhihu.com/p/28566058))代表 Authenticated Encryption with Associated Data。AEAD密码同事提供了保密性，完整性和真实性。这种算法在现代硬件上具有卓越的性能和效率。用户在任何时候应该尽量选择AEAD密码。

下表的AEAD密码是我们推荐的，相关的ss实现必须支持`chacha20-ietf-poly1305`。在具备AES硬件加速的设备上的ss实现必须支持`aes-128-gcm`, `aes-192-gcm`和`aes-256-gcm`。

| Name                   | Key Size | Salt Size | Nonce Size | Tag Size |
| ---------------------- | -------- | --------- | ---------- | -------- |
| chacha20-ietf-poly1305 | 32       | 32        | 12         | 16       |
| aes-256-gcm            | 32       | 32        | 12         | 16       |
| aes-192-gcm            | 24       | 24        | 12         | 16       |
| aes-128-gcm            | 16       | 16        | 12         | 16       |



ss如何使用AEAD密码在 [SIP004](https://github.com/shadowsocks/shadowsocks-org/issues/30)中做了规范，并在 [SIP007](https://github.com/shadowsocks/shadowsocks-org/issues/42)中做了修订。



### 3.1 key的生成

主key可以是用户直接输入的，也可以从用户密码生成。生成算法依旧沿用OpenSSL的`EVP_BytesToKey(3)`。

[HKDF_SHA1](https://tools.ietf.org/html/rfc5869)是这样一个函数：接收一个secret key, 一个非保密salt, 一个字符串，最终输出一个密码学上来说高强度的subkey， 即使输入的secrey key比较弱。



`HKDF_SHA1(secret key, salt, info_string) => subkey`

info_string在应用上下文与subkey强绑定。

我们利用函数HKDF_SHA1利用预先双方共享的主key（我觉得可以简单理解为ss-client的密码）生成了每次会话的临时subkey， salt 需要保证在主key不变的情况下保持唯一性。



### 3.2 经验证的加解密 （Authenticated Encryption/Decryption）

**AE_encrypt** 是一个函数，它接收一个secret key, 一个非保密的一次性随机字符串(nonce)，一条message， 最后输出密文和认证标签（authentication tag)。使用同一key的每次调用中，一次性随机串必须保持唯一（也就是对于同一个key调用函数时，nonce必须不一样）。

`AE_encrypt(secret key, nonce, message) => (ciphertext, tag)`

**AE_decrypt**是一个函数，它接收一个secrey key, 非保密一次性字符串(nonce), 密文(ciphertext), 认证标签(authentication tag)，最终输出原始数据。如果任何一个数据被篡改，解密就会失败。

`AE_decrypt(secret key, nonce, ciphertext, tag) => message`



### 3.3 TCP

AEAD  加密的TCP数据流由一个随机盐值开头(用来生成per-session subkey)， 后面跟随着任意数量的加密数据块，每个块拥有如下结构：

`[encrypted payload length][length tag][encrypted payload][payload tag]`

开头的payload length是2-byte的大端无符号整形，被限定在最大0x3FFF。最高两位保留，目前总是被设置为0。因此payload的最大长度为 $$ 2^{14}-1 $$  bytes。





### 3.4 UDP

一个AEAD加密的UDP包结构如下：

`[salt][encrypted payload][tag]`

salt被用来生成per-session的subkey，salt必须保证随机性和唯一性。每个UDP包使用salt生成的subkey和全0的nonce独立加解密。



## 4. 传输插件

### 4.1 架构概述

ss的插件和tor的 [Pluggable Transport](https://gitweb.torproject.org/torspec.git/tree/pt-spec.txt)（简称PT）类似，但是和PT里的SOCKS5代理不同的是， ss的每个SIP003插件都作为一个tunnel(或者叫做local port forwarding)。这个设计的目的是为了避免PT里每连接参数（per-connection arguments)， 从而使得ss的插件容易实现。



+-----------+                                         +--------------------------+
| SS Client +-- Local Loopback --+ Plugin Client (Tunnel) +--+
+-----------+                                         +--------------------------+         |
                                                                                                         |
        Public Internet (Obfuscated/Transformed traffic) ==>   |
                                                                                                         |
+-----------+                                                 +--------------------------+  |
| SS Server +-- Local Loopback --+ Plugin Server (Tunnel) +--+
+-----------+                                                +--------------------------+



###  4.2 插件的生命周期

和PT类似，插件的client/server作为ss client/server的子进程存在。

如果插件中有错误发生，那么作为插件的子进程就会退出(exit)，并给出error code。然后ss父进程也会停止(SIGCHLD)。

当用户停止了ss client/server时，插件自然也被终止。



### 4.3 向插件传递参数

插件通过环境变量接收参数

1. 4个必须参数环境变量为： 

| SS_REMOTE_HOST | 远端插件服务host     |
| -------------- | -------------------- |
| SS_REMOTE_PORT | 远端插件服务port     |
| SS_LOCAL_HOST  | 本地ss服务或插件host |
| SS_LOCAL_PORT  | 本地ss服务或插件port |



2. 1个可选环境变量 SS_PLUGIN_OPTIONS。如果插件有个性化参数需要传递可以放在这个环境变量里。值例如 `obfs=http;obfs-host=www.baidu.com`，如果值里有分号和等号需要进行backslash转义。



### 4.4 与PT的兼容性

为了使用tor project的插件，有2种方法可行：

1. fork tor的插件，按照SIP003进行修改
2. 对PT进行适配以符合SIP003



### 4.5 插件的许可

所有插件必须运行在独立的进程中，插件开发者可以选择任何许可证。对插件提供者来说并不存在GPL许可的限制。



### 4.6 插件的限制

1. 插件不支持互相串联。ss启动的时候只有一个插件被启动。如果真的想这样，那么就按照SIP003来实现一个plugin-over-plugin
2. 只有TCP数据被转发，UDP目前还不支持

### 4.7 插件样例工程

1. 流量混淆， SIP003 标准插件  [simple-obfs](https://github.com/shadowsocks/simple-obfs)
2.  基于SIP003实现的ss https://github.com/shadowsocks/shadowsocks-libev



## 5. URL scheme

ss的url模式遵循 [RFC3986](https://www.ietf.org/rfc/rfc3986.txt)标准

`SS-URI = "ss://" userinfo "@" hostname ":" port ["/"] ["?"plugin] ["#" tag]
userinfo = websafe-base64-encode-utf8(method ":" password)`

url最后的/必须加上，如果有插件。但如果只有tag(#开图)，最后的/可以省掉。

例子：

1. `ss://YWVzLTEyOC1nY206dGVzdA==@192.168.100.1:8888#Example1`
2. `ss://cmM0LW1kNTpwYXNzd2Q=@192.168.100.1:8888/?plugin=obfs-local%3Bobfs%3Dhttp#Example2`







## 6. 官方ss具体实现

### 6.1 服务端实现

1. [shadowsocks](https://github.com/shadowsocks/shadowsocks) python 

2. [shadowsocks-libev](https://github.com/shadowsocks/shadowsocks-libev)  C

3. [shadowsocks-go](https://github.com/shadowsocks/shadowsocks-go)  Go

4. [go-shadowsocks2](https://github.com/shadowsocks/go-shadowsocks2) Go

   

#### 6.1.1 服务端功能比较

|                | ss   | ss-libev | ss-go | go-ss2 |
| -------------- | ---- | -------- | ----- | ------ |
| TCP fast open  | Y    | Y        | N     | N      |
| Multiuser      | Y    | Y        | Y     | N      |
| Management API | Y    | Y        | N     | N      |
| Redirect mode  | N    | Y        | N     | Y      |
| Tunnel mode    | Y    | Y        | N     | Y      |
| UDP Relay      | Y    | Y        | Y     | Y      |
| AEAD ciphers   | Y    | Y        | N     | Y      |
| Plugin         | N    | Y        | N     | N      |



### 6.2 客户端



#### 6.2.1 客户端功能对比

