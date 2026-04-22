---
name: qi-dong
description: 自动检测本地开发环境，GitHub克隆使用国内镜像加速，一键生成启动脚本。支持导入MD/TXT部署说明文件。
user-invocable: true
argument-hint: <github地址或本地项目路径>
---

# 启动

## 调用方式

当用户说"启动项目"、"部署项目"、"一键启动"或提供GitHub地址时，执行以下步骤：

### 第1步：检测环境

运行 `python scripts/launcher.py <github地址或路径> --auto`

或手动检测：
- 检查 python、nodejs、git 是否安装
- 运行 `python scripts/env_detector.py` 查看完整环境报告

### 第2步：如缺失环境

根据用户系统提供安装指引，使用国内镜像：
- Node.js: https://npmmirror.com/mirrors/node/
- Python: https://mirrors.tuna.tsinghua.edu.cn/python/
- Git: https://npmmirror.com/mirrors/git-for-windows/

### 第3步：克隆项目

如提供GitHub地址，使用国内镜像克隆：
- kgithub.com
- gitclone.com

### 第4步：生成启动脚本

自动检测技术栈并生成 run.bat/run.sh

## 技术栈支持

| 技术栈 | 特征文件 | 安装命令 | 启动命令 |
|--------|----------|----------|----------|
| Node.js | package.json | npm install | npm start/run dev |
| Python | requirements.txt | pip install -r requirements.txt | python app.py |
| Go | go.mod | go mod tidy | go run . |
| Rust | Cargo.toml | cargo build | cargo run |
| Docker | docker-compose.yml | - | docker-compose up |

## 直接调用

```bash
python scripts/launcher.py https://github.com/user/repo
python scripts/launcher.py /local/project/path
python scripts/launcher.py --help
```

## 检查环境

```bash
python scripts/env_detector.py
python scripts/env_detector.py --json
```

## 获取安装指引

```bash
python scripts/installer.py guide windows
python scripts/installer.py nodejs windows
python scripts/installer.py python windows
```