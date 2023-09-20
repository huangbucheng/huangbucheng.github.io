#openapi简介

## openapi 介绍
引用swagger官网介绍：

"The OpenAPI Specification (OAS) defines a standard, language-agnostic interface to HTTP APIs which allows both humans and computers to discover and understand the capabilities of the service without access to source code, documentation, or through network traffic inspection. When properly defined, a consumer can understand and interact with the remote service with a minimal amount of implementation logic.

An OpenAPI definition can then be used by documentation generation tools to display the API, code generation tools to generate servers and clients in various programming languages, testing tools, and many other use cases.
"

示例
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

## 
