# 2FA 验证码生成器

一个基于 Python 和 Tkinter 的本地 2FA 动态验证码生成工具。

## 功能特点
- 支持 16位 / 32位 等标准 Base32 2FA 密钥解析
- 实时显示 30秒 倒计时
- 一键复制验证码到剪贴板
- 本地记忆密钥功能（加密/明文存储于本地，不随代码上传）

## 使用方法
1. 安装依赖：`pip install -r requirements.txt`
2. 运行程序：`python main.py`