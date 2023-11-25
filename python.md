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
