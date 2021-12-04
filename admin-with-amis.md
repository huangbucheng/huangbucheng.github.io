# 管理后台快速搭建

## 简介
业务系统的管理后台，要求OA授权，并且对用户权限进行控制。

## 前端框架
由于没有太多前端开发经验，调研了一些后台管理系统的开发框架，偶然看到amis使用json开发页面，一种似曾相识的感觉油然而生。
我之前是做低代码平台研发的，使用json开发业务流程，对于这种配置化的开发方式非常熟悉，而且不用被前端的知识体系和框架拦在门外。

前端的代码模板直接使用amis-admin，基于amis-admin对页面进行开发：
`https://github.com/aisuda/amis-admin`

## 统一OA认证授权
在ningx接入层，对所有请求通过auth_request进行OA授权认证：
```
        location = /auth {
            proxy_pass http://127.0.0.1:3000;
            proxy_pass_request_body off;
            proxy_set_header Content-Length ""; 
            proxy_set_header X-Original-URI $request_uri;
        }

        location / { 
            auth_request /auth;
            error_page 403 = @error403;

            root /data/webroot;
        }
        location @error403 {
                  add_header Set-Cookie "NSREDIRECT=$scheme://$http_host$request_uri;Path=/";
                  return 302 https://passport.oa.com/modules/passport/signin.ashx?url=http://ginfra.com;
        }

        location /api {
          error_page 403 = @error403;

          proxy_pass http://127.0.0.1:3000;
        }
```
OA认证失败的，统一redirect到OA登录页面。

后端API接口，通过中间件进行同样的OA认证。

## web服务
web服务使用Express快速搭建web服务框架：`npx express-generator`
```
var authRouter = require('./routes/oa-auth');
var indexRouter = require('./routes/index');
var usersRouter = require('./routes/users');
var smartProxy = require('../smartproxy/smart-proxy'); // OA认证

var app = express();

// view engine setup
...
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));
app.use(smartProxy); // 加载中间件进行OA认证

app.use('/', indexRouter);
app.use('/auth', authRouter); // 处理nginx auth_request的OA认证请求
app.use('/api/user', usersRouter); // 业务接口
```
