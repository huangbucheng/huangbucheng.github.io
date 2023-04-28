## pip install with --extra-index-url
问题背景：
`pip install -i`指定内部`Base URL of the Python Package Index`时，所安装的包依赖`setuptools`更高级版本，但是`-i`所指的源中没有`setuptools`包。


解决方案：添加`--extra-index-url`指定默认源
/usr/local/bin/python3.8 -m pip install  venus-api-base -i https://mirrors.my.com/repository/pypi/simple/ --trusted-host mirrors.my.com --extra-index-url https://pypi.python.org/simple
