# 启动.skill
|还在为项目部署而烦恼吗？还在要一步步复制粘贴和翻译的复杂步骤吗？这个agent skill或许能帮到你！

自动检测本地环境，一键拉取、智能部署项目，一键启动！

## 核心功能

- ✅ 自动检测 Node.js、Python、Go、Rust、Docker、Git 环境
- ✅ 支持 Yarn、pnpm、Conda 等多种包管理器
- ✅ 缺失时提供国内镜像下载链接和安装指引
- ✅ GitHub 克隆自动使用国内镜像加速
- ✅ 自动配置 pip/npm 国内镜像源
- ✅ 支持导入外部 MD/TXT 部署说明文件
- ✅ 一键生成 run.bat / run.sh 启动脚本

## 技术栈支持

| 语言/框架 | 特征文件 | 包管理器 |
|-----------|----------|----------|
| Node.js | package.json | npm, yarn, pnpm |
| Python | requirements.txt, pyproject.toml | pip, conda, pipenv |
| Go | go.mod | go |
| Rust | Cargo.toml | cargo |
| Docker | Dockerfile, docker-compose.yml | docker-compose |

## 使用方法
下载zip项目

```bash
# 方式1：直接运行
python scripts/launcher.py <GitHub地址或本地路径>

# 方式2：导入为 Claude Code Skill
将 skill.md 和 scripts/ 目录一起导入

# 方式3：直接丢进ccswitch或cherry studio的以zip方式导入
```

## 使用示例

```
帮我部署 https://github.com/expressjs/express
```

技能会自动：
1. 检测你的本地环境
2. 如有缺失，提供国内镜像下载链接
3. 使用国内镜像加速克隆 GitHub
4. 检测项目技术栈和依赖
5. 生成一键启动脚本

## 文件结构

```
项目一键启动-智能环境版/
├── skill.md              # Skill 定义文件
├── scripts/
│   ├── launcher.py       # 主入口
│   ├── env_detector.py   # 环境检测模块
│   ├── installer.py      # 国内镜像安装模块
│   └── requirements.txt  # 依赖
└── README.md
```

## 触发关键词

- 启动项目
- 部署项目
- 一键启动
- run project
- deploy
