# 日志服务数据加工示例
```
log_keep(regex_match(v("__TAG__.pod_label_k8s-app"),regex="app name",full=False))
log_keep(regex_match(v("__CONTENT__"),regex="summary",full=False))
ext_regex("__CONTENT__", regex="userid\": \"(\d+)", output="uid")
ext_regex("__CONTENT__", regex="status\": (\d+)", output="status")
ext_regex("__CONTENT__", regex="path\": \"([^\"]+)\"", output="path")
t_if(regex_match(v("__CONTENT__"),regex="/api/(.*abc|.*cde)/",full=False), fields_set("key","value1"))
```
