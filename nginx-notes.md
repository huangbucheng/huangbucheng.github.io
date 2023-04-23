# nginx 笔记

## How to follow HTTP redirects inside nginx?
背景：业务中实现有状态的websocket服务集群，客户端建立websocket请求，首先到nginx接入层，nginx将请求先发送给一个proxy服务，
由proxy服务分配一个websocket服务实例，然后将请求重定向至websocket实例。

我们不希望暴露websocket服务实例地址至客户端，所以希望在nginx内完成重定向。

实现：
proxy服务分配websocket实例后，将请求以301重定向至websocket实例的内外地址；
nginx发现301（`proxy_intercept_errors on`），执行`@handle_redirect`进行重定向。
```
    map $http_upgrade $connection_upgrade {
        default upgrade;
        '' close;
    }
    upstream websocket {
        server 10.1.0.1:8888;
    }

    server {
        listen       80;
        listen       [::]:80;
        server_name  _;
        root         /usr/share/nginx/html;

        location / {
            proxy_pass http://websocket;
            proxy_http_version 1.1;
            proxy_read_timeout 100s;

            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection $connection_upgrade;
            proxy_set_header Host $host;

            proxy_intercept_errors on;
            error_page 301 302 307 = @handle_redirect;
        }

        location @handle_redirect {
            set $saved_redirect_location '$upstream_http_location';
            proxy_pass $saved_redirect_location;
            proxy_http_version 1.1;
            proxy_read_timeout 100s;
            
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection $connection_upgrade;
            proxy_set_header Host $host;
        }
    }
```

参考：
1. https://serverfault.com/questions/423265/how-to-follow-http-redirects-inside-nginx
2. https://stackoverflow.com/questions/20254456/intercepting-backend-301-302-redirects-proxy-pass-and-rewriting-to-another-loc/46141557#46141557
