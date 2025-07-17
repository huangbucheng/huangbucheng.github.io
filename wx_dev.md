## 微信公众号开发
1. 接入概述：https://developers.weixin.qq.com/doc/offiaccount/Basic_Information/Access_Overview.html


## 微信开放平台 移动应用迁移
https://developers.weixin.qq.com/doc/oplatform/Mobile_App/guideline/migrate.html
移动应用的应用迁移指的是：应用与主体之间因为运营归属/变更等原因，将原移动应用 Appid 账号从当前的开放平台 Appid 账号迁移到新的开放平台 Appid 账号。

1、迁移后的影响
移动应用迁移后移动应用的 Appid、appSecret、以及该移动应用的用户的 openid 不变；但是 unionid 会变（因为迁移后移动应用所属的开放平台 Appid 账号已经变化）
其他影响：迁移过程中和迁移后对已经发布的 App 用户登录、App 微信分享、app微信支付功能等不会有影响（即，功能不受影响）
2、迁移的注意事项
应用迁移不会涉及到用户个人信息迁移，平台也不提供 unionid 转 openid 接口或者 openid 转 unionid接口
因此，在迁移之前，开发者需要做好数据备份或数据映射等工作，如果某些环节是依赖 unionid 存储和展示，那么迁移后，由于 unionid 与旧的 unionid 不同，如果开发者没有做好数据映射，前端可能会有感知，是否有影响，因此在申请应用迁移前开发者需慎重进行评估。

