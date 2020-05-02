tags: shadowsocks



[TOC]

## server配置

1. `$sudo apt install shadowsocks-libev`
2. `$sudo vim /etc/shadowsocks-libev/config.json`
```js
{
    "server":"<your-public-ip>",
    "server_port":<your-port>,
    "password":"<your-password>",
    "timeout":60,
    "method":"chacha20-ietf-poly1305|aes-128-gcm|aes-192-gcm|aes-256-gcm|chacha20-ietf-poly1305|xchacha20-ietf-poly1305"
}

```
3. `#systemctl start shadowsocks-libev.service`


## client配置
1. `$sudo apt install shadowsocks-libev`
2. `$sudo vim /etc/shadowsocks-libev/config.json`
```js
{
    "server":"<your-public-ip>",
    "server_port":<your-server-port>,
    "local_port":<local-proxy-port>,
    "password":"<your-password>",
    "timeout":60,
    "method":"<same-to-server-method>"
}

```
3. `#ss-local`


