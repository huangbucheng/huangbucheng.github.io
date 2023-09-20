#openapi简介

## openapi 介绍
引用swagger官网介绍：

"The OpenAPI Specification (OAS) defines a standard, language-agnostic interface to HTTP APIs which allows both humans and computers to discover and understand the capabilities of the service without access to source code, documentation, or through network traffic inspection. When properly defined, a consumer can understand and interact with the remote service with a minimal amount of implementation logic.

An OpenAPI definition can then be used by documentation generation tools to display the API, code generation tools to generate servers and clients in various programming languages, testing tools, and many other use cases.
"



传统的开发方式，先编写接口说明书，然后前后端再根据接口说明独立开发。

这种方式比较繁琐，前后端开发人员都需要使用相应的开发语言翻译接口协议，并且需要同时维护接口文档和协议代码，容易出现文档代码不一致的情况。

以`protobuf`为代表的`rpc`协议框架，统一了协议的申明和实现，协议文件定义好后，使用方可以通过工具从协议文件生成相应的接口代码。

在`RESTful`领域，起源于`swagger`的`Open API`及相关的工具生态同样统一协议申明和代码实现。




以一个简单的OAS申明为例：
```
{
  "swagger": "2.0",
  "info": {},
  "paths": {
    "/api/v1/Login": {
      "post": {
        "description": "账号+密码方式登录系统，支持学习账号、手机号、邮箱号",
        "summary": "登录请求，校验成功获得Token",
        "operationId": "Login",
        "parameters": [
          {
            "name": "body",
            "in": "body",
            "schema": {
              "type": "object",
              "$ref": "#/definitions/LoginRequest"
            }
          }
        ],
        "responses": {
          "200": {
            "$ref": "#/responses/LoginResponse"
          }
        }
      }
    }
  },
  "definitions": {
    "LoginRequest": {
      "type": "object",
      "required": [
        "Account",
        "CipherPassword"
      ],
      "properties": {
        "Account": {
          "description": "登录账号，支持学习账号、手机号、邮箱号",
          "type": "string"
        },
        "Channel": {
          "description": "登录渠道",
          "type": "string"
        },
        "CipherPassword": {
          "description": "登录密码明文",
          "type": "string"
        },
        "RandStr": {
          "description": "前端回调函数返回的随机字符串",
          "type": "string"
        },
        "Ticket": {
          "description": "前端回调函数返回的用户验证票据",
          "type": "string"
        }
      },
    },
    "LoginResponse": {
      "type": "object",
      "properties": {
        "Token": {
          "description": "登录态Token",
          "type": "string"
        },
        "Uid": {
          "description": "用户UID",
          "type": "string"
        }
      },
    }
  },
  "responses": {
    "LoginResponse": {
      "description": "登录应答",
      "schema": {
        "$ref": "#/definitions/LoginResponse"
      }
    }
  }
}
```

通过工具可以将OAS申明转换为HMTL的接口说明文档：

<img src="https://github.com/huangbucheng/huangbucheng.github.io/assets/16696251/d478bec3-ca96-41ac-919a-11016242d437" alt="drawing" width="200"/>


## 如何自动化生成OAS
以go代码自动生成OAS申明为例，在API开发之前，先写`swagger annation`和相应的输入输出models，用于生成`OAS`的输入：
```
//	API:
//	version: 1.0.0
//	title: API
//	Schemes: https
//	Host: myhost.com
//	BasePath: /
//
//	Consumes:
//	- application/json
//
//	Produces:
//	- application/json
//
//	Security:
//	- basic
//
//	SecurityDefinitions:
//	basic:
//	  type: basic
//
// swagger:meta

package docs

// swagger:route POST /api/v1/Login Login
// 登录请求，校验成功获得Token
//
// 账号+密码方式登录系统，支持学习账号、手机号、邮箱号
//
// Parameters:
//  + name: body
//    require: true
//    in: body
//    type: LoginRequest
//
// responses:
//	200: LoginResponse

// swagger:parameters LoginRequest
type _ struct {
	// 登录请求参数
	// in:body
	// required: true
	Body {LoginRequst Type}
}

// 登录应答
// swagger:response LoginResponse
type LoginResponseWrapper struct {
	// in:body
	Body {LoginResponse Type}
}
```

然后使用`go-swagger`基于`swagger annation`生成`OAS`：
```
go install github.com/go-swagger/go-swagger/cmd/swagger@latest
swagger generate spec -o ./docs/swagger.json
```

### protobuf to swagger
`protoc-gen-swagger`

## 如何通过OAS生成代码
`npx @openapitools/openapi-generator-cli generate -i docs/swagger.json -g javascript -o sdk/js`

