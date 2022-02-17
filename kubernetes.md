## 腾讯云容器集群虚拟节点问题
### 问题背景
业务Pod在高负载情况下，自动扩容，由于集群使用了虚拟节点，部分扩容Pod调度到虚拟节点上。然后通过监控发现，虚拟节点上的Pod，在正常处理请求后，客户端并没有收到响应而超时，同时CVM节点上的Pod没有该问题。
虚拟节点的Pod因超时而得不到负载分配，进而导致CVM节点上的Pod跑满而得不到缓解。

![企业微信截图_16450168381759(1)](https://user-images.githubusercontent.com/16696251/154393604-d1cd0931-ba78-4457-b993-25280c7a9866.png)

### 问题分析
通过curl直接请求虚拟节点上的Pod的服务：
```bash
curl -v -XPOST http://172.16.1.45:80/api/user/status -d '{}'

* About to connect() to 172.16.1.45 port 80 (#0)
*   Trying 172.16.1.45...
* Connected to 172.16.1.45 (172.16.1.45) port 80 (#0)
> POST /api/user/status HTTP/1.1
> User-Agent: curl/7.29.0
> Host: 172.16.1.45:80
> Accept: */*
> Content-Length: 2
> Content-Type: application/x-www-form-urlencoded
> 
* upload completely sent off: 2 out of 2 bytes
* Empty reply from server
* Connection #0 to host 172.16.1.45 left intact
curl: (52) Empty reply from server
```
