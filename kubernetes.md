## 容器内存（含cache）逐渐用完limit 限额
### 问题背景
一个服务的内存（含cache）逐渐上升，但内存（不含cache）则保持稳定趋势。业务中会此处操作文件。
### 解析
参考：[Page Cache：为什么我的容器内存使用量总是在临界点？](https://blog.lichao.xin/back-end/docker/docker-05/#Page-Cache%EF%BC%9A%E4%B8%BA%E4%BB%80%E4%B9%88%E6%88%91%E7%9A%84%E5%AE%B9%E5%99%A8%E5%86%85%E5%AD%98%E4%BD%BF%E7%94%A8%E9%87%8F%E6%80%BB%E6%98%AF%E5%9C%A8%E4%B8%B4%E7%95%8C%E7%82%B9)
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

### 解析
从服务日志看，请求正常处理完成，但是在web框架中，处理完请求后会上报请求结果状态数据至 监控平台，上报监控平台走的是外网。而腾讯云虚拟节点默认是没有外网访问能力的。

解决办法：[弹性容器服务（Elastic Kubernetes Service，EKS）支持通过配置 NAT 网关 和 路由表 来实现集群内服务访问外网](https://cloud.tencent.com/document/product/457/48710)


