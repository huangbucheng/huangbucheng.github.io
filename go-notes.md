# go 编程纪要

## Go语言中Kill子进程的正确姿势
使用exec.Process.Kill子进程示例如下：
```go
cmd = exec.Command("sh", "wrapper.sh")
time.AfterFunc(3*time.Second, func() { cmd.Process.Kill() })
if out, err = cmd.CombinedOutput(); err != nil {
    fmt.Println(err)
}
```
问题：wrapper.sh进程成功被kill，但是wrapper.sh创建的子进程未被kill，该子进程的PPID是1，即被init进程接管了。
解析：Go使用kill(SIGKILL)向exec.Command进程发了一个KILL信号，但并不会发送给子进程，父进程被kill之后，子进程变成孤儿进程。
解决方案：
kill(SIGKILL)不但支持向单个进程发送信号，还可以向进程组发信号，传递进程组PGID的时候要使用负数的形式。关键是PGID的设置，默认情况下，子进程会把自己的PGID设置成与父进程相同，所以，我们只要设置了父进程的PGID，所有子进程也就相应的有了PGID。
```go
cmd = exec.Command("sh", "wrapper.sh")
cmd.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}
time.AfterFunc(3*time.Second, func() { syscall.Kill(-cmd.Process.Pid, syscall.SIGKILL) })
if out, err = cmd.CombinedOutput(); err != nil {
    fmt.Println(err)
}
```

## 操作excel文件
### excel 写文件问题
之前使用该库`github.com/tealeg/xlsx/v3`操作excel文件，遇到2个问题：
1. 有些情况下，excel文件部分单元格存在特殊格式，导致读取该单元格数据为空；
2. 在服务器环境创建的excel文件，在Windows环境打开，有数据的行全部显示不出来，表单第一个行号从无数据行开始（WSL的ubuntu环境未复现该问题）；

之后切换到新库`github.com/xuri/excelize/v2`，以上问题不存在。

### 单元格式-日期 解析
单元格的格式是日期时，读取出来的内容是：当前日期距离1900-00-01的天数，例如 2011/07/27 读取出来是 40751。

解析日期的示例：
```go
	excelTime := time.Date(1899, time.December, 30, 0, 0, 0, 0, time.UTC)
	days, _ := strconv.Atoi(excelDate)
	t := excelTime.Add(time.Second * time.Duration(days*86400))
```

## time.Since 注意事项
在使用`time.Since`进行时长比较时，有2种情况注意区分：
1. `time.Since` 与 `time.Duration`（预定义的`time.Second`等 或 通过`time.ParseDuration`解析得到的`time.Duration`）比较OK；
2. `time.Since` 与 `time.Duration(int)` 比较，容易有时间单位不一致的问题，此时的解决办法是对齐单位，如：`time.Since().Second()` 与 `time.Duration(int)`；

## gorm 用例
### IgnoreRecordNotFoundError 忽略RecordNotFound日志
```go
	l := logger.New(log.New(os.Stdout, "\r\n", log.LstdFlags), logger.Config{
		SlowThreshold:             200 * time.Millisecond,
		LogLevel:                  lv,
		IgnoreRecordNotFoundError: true,
		Colorful:                  true,
	})

	db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{
		Logger: l,
		NamingStrategy: schema.NamingStrategy{
			// table name prefix, table for `User` would be `t_users`
			TablePrefix: "t_",
			// use singular table name, table for `User` would be `user` with this option enabled
			SingularTable: true,
			// use name replacer to change struct/field name before convert it to db name
			NameReplacer: strings.NewReplacer("CID", "Cid"),
		},
	})
```
### 基于tag的查询 & 随机查询
业务背景：从题库中，按照tag要求，随机抽取一定数量的题目。

gorm关键知识点：子查询`subquery` 和 随机排序`Order("RAND()")`的用法。

[Tags-Database-schemas](http://howto.philippkeller.com/2005/04/24/Tags-Database-schemas/)

```go
/* 根据tag从题库中随机抽题
 * @param incltags: 需满足的tag集
 * @param commtags: 需满足的tag集（基于业务场景与incltags分别传递）
 * @param excltags: 不能包含的tag集
 * @param exclqaids: 排除的题目集
 * @param limit: 抽题数量
 * @return: 抽取的题目ID列表, error
 */
func extractQasByTags(ctx context.Context, incltags, commtags, excltags [][]interface{}, exclqaids []string, limit int) ([]string, error) {
	var qaids []string
	var qatags []models.QaTag
	db, _ := datasource.Gormv2(ctx)
	query := db.Model(&models.QaTag{}).Select("t_qa_tag.qa_id")

	if len(incltags) > 0 {
		query = query.Where("(tag_label, tag_value) IN ?", incltags)
	}

	if len(commtags) > 0 {
		subquery := db.Table("t_qa_tag").Select("qa_id").
			Where("(tag_label, tag_value) IN ?", commtags).
			Group("qa_id").Having("COUNT(qa_id) = ?", len(commtags))
		query = query.Where("qa_id IN (?) ", subquery)
	}

	if len(excltags) > 0 {
		subquery := db.Table("t_qa_tag").Select("qa_id").
			Where("(tag_label, tag_value) IN ?", excltags)
		query = query.Where("qa_id NOT IN (?) ", subquery)
	}

	if len(exclqaids) > 0 {
		query = query.Where("qa_id NOT IN ? ", exclqaids)
	}

	if len(incltags) > 0 {
		query = query.Group("qa_id").Having("COUNT(qa_id) = ?", len(incltags))
	}
	query = query.Order("RAND()").Limit(limit).Offset(0)
	err := query.Find(&qatags).Error
	if err != nil {
		return qaids, err
	}

	for _, tag := range qatags {
		qaids = append(qaids, tag.QaID)
	}
	return qaids, nil
}
```
### Order - 自定义排序
业务背景：查询结果排序规则稍微复杂一些。例如，查询用户参加的赛事列表，排序规则为：

1. 进行中的赛事，按照自定义的sortkey排序；
2. 已结束的赛事，排在后面，并按时间倒序排列；

SQL关键知识点：`ORDER BY FIELD`, `ORDER BY CASE WHEN THEN ELSE END`

#### `ORDER BY FIELD`
fruit 表有一个 name 字段，具有以下特定的值：苹果(Apple)，香蕉(Banana)，橘子(Orange)，梨(Pear)，每个特定的值都有一系列的品种。

我们要按香蕉，苹果，梨，橘子等特定的顺序排列数据, 然后再按品种排序：
```sql
SELECT * FROM fruit
ORDER BY FIELD(name, 'Banana', 'Apple', 'Pear', 'Orange'), variety;
```
【参考】(https://lingchao.xin/post/ordering-by-specific-field-values-with-mysql.html)

#### `ORDER BY CASE WHEN THEN ELSE END`
实现上述业务背景场景：

1. 进行中的赛事，按照自定义的sortkey排序；
2. 已结束的赛事，排在后面，并按时间倒序排列；
```sql
select * from t_match_config order by CASE WHEN `end_time` > now() then `id` ELSE 999999999 END ASC, created_at desc;
```
【参考】(https://learnsql.com/blog/order-by-specific-value/)

### Join - 1 v N场景下的left join
业务背景：翻页查询所有活动列表，并且返回用户在活动中的状态，尚未未参加的活动也需要返回。

SQL关键知识点：`left join` 以及 `join on` 中附带条件过滤

```go
/* 查询level类型的activity，以及uid在activity中的状态，未参加的activity也返回。
 * @param uid：用户id
 * @return：activity状态列表，总activity数，error
 */
func get_activities_and_user_status(ctx context.Context, uid string, limit, offset int) ([]UserActivityStatus, int64, error) {
	var total int64
	var statuses []UserActivityStatus
	
	db, _ := datasource.Gormv2(ctx)
	query := db.Model(&models.GameActivity{}).
		Select("t_game_activity.id, t_game_activity.Name, t_game_user.uid, t_game_user.user_status").
		Joins("left join t_game_user on t_game_user.activity_id = t_game_activity.id AND t_game_user.uid = ? AND t_game_user.user_type = ?",
			uid, models.USER_TYPE_NORMAL).
		Where("t_game_activity.activity_type = ?", "level")

	err := query.Session(&gorm.Session{PrepareStmt: true}).Distinct("t_game_activity.id").Count(&total).Error
	if err != nil {
		return nil, total, err
	}

	query = query.Order("t_game_activity.created_at desc")
	err = query.Limit(limit).Offset(offset).Scan(&statuses).Error
	if err != nil {
		return nil, total, err
	}
	
	return statuses, total, nil
}
```
### FirstOrCreate RowsAffected 问题
问题背景：业务中根据`FirstOrCreate`返回的`RowsAffected`，决定是否再调用`Updates`更新部分字段。正常运行几个月后，突然出现`RowsAffected`一直返回`1`的问题。

原因：FirstOrCreate(gorm@v1.22.4) return RowsAffected with value 1 when record already exist.

issue: https://github.com/go-gorm/gorm/issues/4996

FirstOrCreate(gorm@v1.22.2) return RowsAffected with value 0 when record already exist.

### FirstOrCreate 并发问题
问题背景：业务中经常使用`FirstOrCreate`来创建或查询数据，之前想当然以为`FirstOrCreate`是原子操作，可是在实际场景中，时常出现并发问题：
`Error 1062: Duplicate entry 'xxx' for key 'index-xxx'`

原因：从gorm debug日志可以看出，`FirstOrCreate`是先执行SELECT，不存在的情况下再执行INSERT。为了正确处理INSERT并发导致的`Duplicate entry`问题，程序中需要检查db.Error：
```
	rdb := db.FirstOrCreate(s, &AModel{Key: 123456})
	if rdb.Error != nil {
		var mysqlErr *mysql.MySQLError
		if errors.As(rdb.Error, &mysqlErr) && mysqlErr.Number == 1062 {
			return 0, nil
		}
		return 0, rdb.Error
	}
	return rdb.RowsAffected, rdb.Error
```

### REGEXP 用法
查询`field`列以prefix开头并且后面跟数字的记录：
```go
query.Where("`field` REGEXP ?", fmt.Sprintf("^%s[0-9]+$", prefix))
```
### 位运算
#### 需求背景
数据通过`visible` mask字段控制可见范围：

0x01 - 全局可见

0x02 - 小程序不可见

对于小程序不可见的数据，`visible`可设置为`visible` | 0x02。小程序的查询方式为（排除设置了0x02的数据）：
```go
query = query.Where("`visible`&? = 0", 0x02)
```
### utf8-mb4
TODO

## gomonkey
### panic: retrieve method by name failed
`go test --cover -v ./...` 运行单元测试，报错：`panic: retrieve method by name failed`
```go
	patches := gomonkey.ApplyMethod(reflect.TypeOf(c), "Load", func(c *caches.GlobalCache) error {
		return nil
	})
	patches = patches.ApplyMethod(reflect.TypeOf(&models.QABase{}), "Get", func(p *models.QABase, db *gorm.DB, qaid string) error {
		p.QaID = qaid
		return nil
	})
	defer patches.Reset()
```
**Cause**

gomonkey fails to patch a function or a member method if inlining is enabled, please running your tests with inlining disabled by adding the command line argument that is -gcflags=-l(below go1.10) or -gcflags=all=-l(go1.10 and above).

**SLN**

`go test -gcflags=all=-l --cover -v ./...` 
