## use websocket with gin
```go
import (
	"context"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/go-redis/redis_rate/v9"
	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
)

var upgrade = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true
	},
}

func NewGame(c *gin.Context) {
	game := c.Query("game")
	stage := c.Query("stage")
	cid := c.Query("cid")
	scene := c.Query("scene")
	if len(scene) == 0 {
		scene = models.STAGE_SCENE_STUDIO
	}

	if len(game) == 0 || len(game) > 32 || len(stage) == 0 || len(stage) > 128 ||
		len(cid) > 128 {
		OnWsError(c, proto.ErrCodeInvalidParameter)
		return
	}

	// get uid from cookie
	var uid uint64

	runner, err := alloc_gamer(c.Request.Context(), game, stage, scene, cid, uid)
	if err != nil {
		OnWsError(c, err)
		return
	}

	addr := runner.ServiceAddress
	c.Header("UserId", strconv.FormatUint(uid, 10))
	c.Redirect(http.StatusMovedPermanently, addr)
}

func OnWsError(c *gin.Context, wserr error) {
	// 升级成 websocket 连接
	ws, err := upgrade.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		c.AbortWithStatus(http.StatusInternalServerError)
		return
	}

	// 关闭连接释放资源
	var closeCode int
	message := wserr.Error()
	switch errcode.ErrorCode(wserr) {
	case proto.ErrCodeInvalidClaims.Code:
		closeCode = 4001
	case proto.ErrCodeInvalidParameter.Code:
		closeCode = 4002
	case proto.ErrCodeInternalError.Code:
		closeCode = 4003
	case proto.ErrCodeScheduleRetry.Code:
		closeCode = 4004
		message = "暂无空闲资源，请稍后再试"
	}

	closeMessage := websocket.FormatCloseMessage(closeCode, message)
	deadline := time.Now().Add(time.Second)
	e := ws.WriteControl(websocket.CloseMessage, closeMessage, deadline)
	if e != nil {
		c.AbortWithStatus(http.StatusInternalServerError)
		return
	}
}
```

ref: 
1. https://juejin.cn/post/7103737973782511646
2. https://github.com/huangbucheng/huangbucheng.github.io/blob/master/nginx-notes.md#how-to-follow-http-redirects-inside-nginx

