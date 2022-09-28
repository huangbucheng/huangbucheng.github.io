# 业务系统集成Discuz-Q实践

## 集成方案
业务系统需要集成论坛模块，方案上选择`Discuz-Q`作为论坛的功能模块集成到业务系统。在集成时，主要面临的2个问题是：账号打通 和 服务路由 的问题。

`Discuz-Q`系统是一个完备的系统，有自己的账号系统，业务系统集成`Discuz-Q`系统，首先需要解决2个账号系统统一的问题。

我们基于开发维护成本和解耦的考虑，没有选择修改`Discuz-Q`的账号系统，而是建立业务账号系统和`Discuz-Q`的账号系统的映射。

服务路由的问题比较简单，所有`Discuz-Q`的请求，都通过子域名进入`Discuz-Q`的`Nginx`接入层，实现业务和`Discuz-Q`的路由完全分离。

## 账号打通
用户在业务系统登录之后，不需要再登录`Discuz-Q`系统。

但是`Discuz-Q`本身有自己的账号系统，并且所有用户数据是与`Discuz-Q`系统自身的账号系统关联的，所以需要将业务系统账号转换为`Discuz-Q`账号，再将请求转发给`Discuz-Q`后台服务。


这种需求就非常适合使用`Nginx auth_request`来实现：
```
server {
        listen 80 default_server;
        listen [::]:80 default_server;

        root /var/www/dzq_latest_install/public;

        # Add index.php to the list if you are using PHP
        index index.php index.html index.htm index.nginx-debian.html;

        server_name _;

        location / {
                try_files $uri $uri/ /index.php?$query_string;
        }

        # pass PHP scripts to FastCGI server
        #
        location ~ \.php$ {
                access_log /var/log/nginx/discuz.log;

                auth_request /auth;
                auth_request_set $discuztoken $upstream_http_discuztoken;
                fastcgi_param HTTP_authorization $discuztoken;

                include snippets/fastcgi-php.conf;

                # With php-fpm (or other unix sockets):
                fastcgi_pass unix:/var/run/php7.3-fpm.sock;
                # With php-cgi (or other tcp sockets):
                # fastcgi_pass 127.0.0.1:9000;
        }

        location /auth {
            internal;
            proxy_set_header Host $host;
            proxy_pass_request_body off;
            proxy_set_header Content-Length "";
            proxy_pass http://127.0.0.1:30456/api/auth/getdiscuztoken;
        }
}
```
将所有`Discuz-Q`的访问先通过`auth_request`转发至`/api/auth/getdiscuztoken`服务，该服务主要实现以下逻辑：

1. 如果请求不带业务`token`，则什么也不做；
2. 如果请求带业务`token`，则查库找业务账号对应的`Discuz-Q`账号。如果不存在对应的`Discuz-Q`账号，则创建之。
3. 用`JWT`生成`Discuz-Q token`;

服务go代码：
```golang
func GetDiscuzToken(c *gin.Context) {
	// 尝试解析业务token
	claims, err := mw.TryParseToken(c)
	if err != nil {
		// token无效，则当作未登录态
		return
	}

	if claims == nil {
		// 无业务token，则当作未登录态
		return
	}

	// 通过token查询业务账号
	claimuser := utils.GetUser(claims)
	if claimuser == nil {
		// 无相应业务账号，则当作未登录态
		return
	}

	// 查询业务账号对应的Discuz账号
	discuzuser, err := caches.GRedisCache.GetDiscuzUser(c.Request.Context(), claimuser.Uid)
	if err != nil {
		// 查询异常，则当作未登录态
		return
	}
  
	if discuzuser == nil {
		// 无对应的Discuz账号，则创建Discuz账号及映射关系
		discuzuser, err = domain.CreateDiscuzUser(c.Request.Context(), claimuser)
		if err != nil {
			return
		}
	}

	// 生成Discuz token
	data := make(map[string]interface{})
	data["sub"] = discuzuser.DiscuzUid
	data["jti"] = "xxxx"
	data["aud"] = ""
	data["scopes"] = []interface{}{nil}
	data["exp"] = time.Now().Add(30 * 24 * time.Hour).Unix()
	data["iat"] = time.Now().Unix()
	data["nbf"] = time.Now().Unix()
	token, err := utils.CreateJWTTokenFromMapWithRS256(Discuz_Private_key, data)
	if err != nil {
		return
	}

	// 将Discuz token写入reponse header
	c.Header("discuztoken", "Bearer "+token)
}

// 创建Discuz账号及映射关系
func CreateDiscuzUser(ctx context.Context, user *models.User) (*models.DiscuzUserAssociation, error) {
	// 1. 创建Discuz 用户 - 无密码，不支持密码登录
	username := strconv.FormatUint(user.Uid, 10)
	sql := "insert into discuz.users (`username`, `password`, `nickname`, `register_reason`, `created_at`, `updated_at`) values (?, ?, ?, ?, ?, ?)"
	res := datasource.GormRW(ctx).Exec(sql,
		username, "", user.Name, "autocreate", time.Now(), time.Now())
	if res.Error != nil {
		if !strings.Contains(res.Error.Error(), "Duplicate entry") {
			return nil, err
		}
	}

	var discuzuid uint64
	sql = "select id from discuz.users where username=?"
	query := datasource.GormRW(ctx).Raw(sql, username)
	err := query.Scan(&discuzuid).Error
	if err != nil {
		return nil, err
	}

	// 2. 设置Discuz用户组 - 普通用户组ID=10
	sql = "insert into discuz.group_user (`group_id`, `user_id`) values (?, ?)"
	res = datasource.GormRW(ctx).Exec(sql, 10, discuzuid)
	if res.Error != nil {
		if !strings.Contains(res.Error.Error(), "Duplicate entry") {
			return nil, err
		}
	}

	// 3. 创建业务账号与Discuz账号映射关系
	var assoc models.DiscuzUserAssociation
	assoc.Uid = user.Uid
	assoc.DiscuzUid = discuzuid
	_, err = assoc.FirstOrCreate(datasource.GormRW(ctx))
	if err != nil {
		return nil, err
	}

	return &assoc, nil
}
```


`auth_request`之后，将`Discuz-Q token`写入请求`Header`，然后将请求转发给`Discuz-Q`后台服务。

### nginx auth_request 配置
下面对`auth_request`的配置做一下解析：
```
log_format discuzlog '$remote_addr - $remote_user [$time_local] '
    '"$request" $status $body_bytes_sent '
    '[token=$http_token] [discuztoken=$discuztoken] '
    '"$http_referer" "$http_user_agent"';

server {
    location ~ \.php$ {
	access_log /var/log/nginx/discuz.log discuzlog;

	auth_request /auth;
	auth_request_set $discuztoken $upstream_http_discuztoken;
	fastcgi_param HTTP_authorization $discuztoken;
	... ...
    }
}
```
1. `auth`服务将`Discuz token`写在`response`的`Header: discuztoken`中，`auth_request_set`将该`token`从`$upstream_http_discuztoken`中读取出来，并保存到`$discuztoken`变量中；
2. 再通过`fastcgi_param`将该`token`写入`request`的`Header: authorization`中，此处`fastcgi_param`使用的`Header`名称是`HTTP_authorization`；
3. 通过`log_format`可以将业务`token`和`Discuz token`记录下来调试：`log_format discuzlog ... [token=$http_token] [discuztoken=$discuztoken] ...; `



