## 在 Python 中，将字符串反序列化为对象
除了`json`, `pickle`，如果字符串表示的是 Python 的字面量结构（如元组、列表、字典等），可以使用 ast.literal_eval。
```python
import ast

# 字符串表示的字典
literal_string = "{'name': 'Alice', 'age': 30}"

# 反序列化为字典
obj = ast.literal_eval(literal_string)

# 输出结果
print(obj)  # 输出: {'name': 'Alice', 'age': 30}
print(type(obj))  # 输出: <class 'dict'>
```

```python
import ast

# 字符串表示的字符串
literal_string = "\"str\""

# 反序列化为字符串
obj = ast.literal_eval(literal_string)

# 输出结果
print(obj)  # 输出: AA
print(type(obj))  # 输出: <class 'str'>
```

## __dir__
Python offers an in-built method to print out all attributes of an object (Now, this object may be anything in Python). This method is also known as a magic method or a dunder method in Python.

Syntax:
```
    print(objectName.__dir__())

    print(obj.__dict__.keys())
    print(obj.__dir__())
```

## locale.Error: unsupported locale setting
问题背景：

`python`包依赖特定语言包，查看当前安装的语言包：
```# locale -a
C
POSIX
```


解决方案：安装语言包


```
yum reinstall -y glibc-common
locale -a
```



## pip install with --extra-index-url
问题背景：

`pip install -i`指定内部`Base URL of the Python Package Index`时，所安装的包依赖`setuptools`更高级版本，但是`-i`所指的源中没有`setuptools`包。


解决方案：添加`--extra-index-url`指定默认源

```
/usr/local/bin/python3.8 -m pip install  venus-api-base -i https://mirrors.my.com/repository/pypi/simple/ --trusted-host mirrors.my.com --extra-index-url https://pypi.python.org/simple
```
