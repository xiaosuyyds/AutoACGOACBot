<h1 align="center">AutoACGOACBot</h1>
<p align="center" class="shields">
    <a href="https://github.com/xiaosuyyds/AutoACGOACBot/issues" style="text-decoration:none">
        <img src="https://img.shields.io/github/issues/xiaosuyyds/AutoACGOACBot.svg?style=for-the-badge" alt="GitHub issues"/>
    </a>
    <a href="https://github.com/xiaosuyyds/AutoACGOACBot/stargazers" style="text-decoration:none" >
        <img src="https://img.shields.io/github/stars/xiaosuyyds/AutoACGOACBot.svg?style=for-the-badge" alt="GitHub stars"/>
    </a>
    <a href="https://github.com/xiaosuyyds/AutoACGOACBot/forks" style="text-decoration:none" >
        <img src="https://img.shields.io/github/forks/xiaosuyyds/AutoACGOACBot.svg?style=for-the-badge" alt="GitHub forks"/>
    </a>
    <!--
    <a href="https://github.com/xiaosuyyds/AutoACGOACBot/actions">
        <img src="https://img.shields.io/github/actions/workflow/status/xiaosuyyds/AutoACGOACBot/vuepress-deploy.yml?style=for-the-badge">
    </a>
    -->
    <a href="https://github.com/xiaosuyyds/AutoACGOACBot/blob/master/LICENSE" style="text-decoration:none" >
        <img src="https://img.shields.io/static/v1?label=LICENSE&message=GPL-3.0&color=lightrey&style=for-the-badge" alt="GitHub license"/>
    </a>
    <br>
    <a href="https://github.com/xiaosuyyds/AutoACGOACBot">
        <img src="https://counter.seku.su/cmoe?name=AutoACGOACBot&theme=rule34" alt=""/>
    </a>
</p>

### 这是一个基于LLM的ACGO刷题平台的自动答题机器人

## ⚠️️warning ⚠️声明
#### ***1.请勿滥用，本项目仅用于学习和测试！请勿滥用，本项目仅用于学习和测试！请勿滥用，本项目仅用于学习和测试！***
#### ***2.利用本项目提供的接口、文档与代码等造成不良影响及后果与本人无关***
#### ***3.由于本项目的特殊性，可能随时停止开发或删档***

## 💻如何部署？

1.将本项目 clone 到本地(没有git的也可以使用github的Code->Download ZIP下载)
```bash
git clone https://github.com/xiaosuyyds/AutoACGOACBot.git
```

2.设置虚拟环境(可选)
```bash
python -m venv .venv
```


3.安装依赖包
```bash
pip install -r requirements.txt
```

4.修改[配置文件](constants.py)，里面有详细的注释，配置好即可。

5.运行程序
```bash
python main.py
```

Tips: 如果自动登录出现问题请参照selenium的文档自行修复

实在不行还可自行登录，将获取到的AccessToken放到项目目录的`access_token.json`文件内，格式如下: 
```json
{
    "access_token": "你的AccessToken"
}
```

## ❤️鸣谢❤️
### 本项目的API参考了 [ACGO-API-collect](https://github.com/xiaosuyyds/ACGO-API-collect) 的内容

## ⭐StarHistory⭐
<div align="center">
  <img src="https://api.star-history.com/svg?repos=xiaosuyyds/AutoACGOACBot&type=Date" alt="Star History"/>
</div>
