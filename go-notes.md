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
