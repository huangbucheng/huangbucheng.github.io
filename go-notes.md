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
之前使用该库`github.com/tealeg/xlsx/v3`操作excel文件，遇到2个问题：
1. 有些情况下，excel文件部分单元格存在特殊格式，导致读取该单元格数据为空；
2. 在服务器环境创建的excel文件，在Windows环境打开，有数据的行全部显示不出来，表单第一个行号从无数据行开始（WSL的ubuntu环境未复现该问题）；

之后切换到新库`github.com/xuri/excelize/v2`，以上问题不存在。

## time.Since 注意事项
在使用`time.Since`进行时长比较时，有2种情况注意区分：
1. `time.Since` 与 `time.Duration`（预定义的`time.Second`等 或 通过`time.ParseDuration`解析得到的`time.Duration`）比较OK；
2. `time.Since` 与 `time.Duration(int)` 比较，容易有时间单位不一致的问题，此时的解决办法是对齐单位，如：`time.Since().Second()` 与 `time.Duration(int)`；

## gorm 用例
### 基于tag的查询 & 随机查询
业务背景：从题库中，按照tag要求，随机抽取一定数量的题目。

gorm关键知识点：子查询`subquery` 和 随机排序`Order("RAND()")`的用法。
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
