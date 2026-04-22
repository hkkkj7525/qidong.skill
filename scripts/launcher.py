#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目一键启动器 - 智能环境检测、国内加速、支持导入外部说明
用法: python launcher.py <github地址或本地路径> [--auto]
"""

import os
import sys
import json
import shutil
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 导入自定义模块
from env_detector import (
    get_full_environment_report, format_env_report,
    check_missing_tools, detect_os, detect_docker,
    detect_yarn, detect_pnpm, detect_conda
)
from installer import (
    get_github_mirror_url, get_best_available_github_mirror,
    generate_install_guide, configure_pip_mirror, configure_npm_mirror
)

# ========== 支持的技术栈 ==========
支持的技术栈 = {
    "Node.js": {
        "特征文件": ["package.json"],
        "安装命令": {
            "npm": "npm install --registry=https://registry.npmmirror.com/",
            "yarn": "yarn install --registry=https://registry.npmmirror.com/",
            "pnpm": "pnpm install --registry=https://registry.npmmirror.com/"
        },
        "启动命令": ["npm start", "npm run dev", "npm run serve"],
        "环境问题": [{"问题": "请选择包管理器？", "选项": ["npm", "yarn", "pnpm"], "默认": "npm"}]
    },
    "Python": {
        "特征文件": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"],
        "安装命令": {
            "pip": "pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/",
            "conda": "conda install --file requirements.txt",
            "pipenv": "pipenv install"
        },
        "启动命令": ["python app.py", "python main.py", "python run.py", "python -m flask run"],
        "环境问题": [{"问题": "是否使用虚拟环境？", "选项": ["venv", "conda", "不使用"], "默认": "venv"}]
    },
    "Go": {
        "特征文件": ["go.mod"],
        "安装命令": ["go mod tidy", "go mod download"],
        "启动命令": ["go run .", "go run main.go", "go build -o app ."],
        "环境问题": []
    },
    "Rust": {
        "特征文件": ["Cargo.toml"],
        "安装命令": ["cargo fetch", "cargo build"],
        "启动命令": ["cargo run", "cargo run --release"],
        "环境问题": []
    },
    "Docker": {
        "特征文件": ["docker-compose.yml", "docker-compose.yaml", "Dockerfile"],
        "安装命令": [],
        "启动命令": ["docker-compose up -d", "docker-compose up"],
        "环境问题": []
    }
}

# ========== 工具函数 ==========

def 询问用户(问题: str, 选项: List[str] = None, 默认值: str = None) -> str:
    if 选项:
        选项字符串 = "/".join(选项)
        提示 = f"[?] {问题} ({选项字符串})"
        if 默认值:
            提示 += f" [默认: {默认值}]"
    else:
        提示 = f"[?] {问题}"
    print(提示)
    sys.stdout.flush()
    回答 = sys.stdin.readline().strip()
    if not 回答 and 默认值:
        return 默认值
    return 回答

def 执行命令(命令列表: List[str], 工作目录: str = None) -> Tuple[int, str, str]:
    try:
        结果 = subprocess.run(命令列表, cwd=工作目录, capture_output=True, text=True, timeout=60)
        return 结果.returncode, 结果.stdout, 结果.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "命令执行超时"

def 克隆仓库(仓库地址: str, 目标目录: str, 使用镜像: bool = True) -> bool:
    """克隆仓库，支持国内镜像加速"""
    if 使用镜像 and "github.com" in 仓库地址:
        镜像名称 = get_best_available_github_mirror()
        镜像地址 = get_github_mirror_url(仓库地址, 镜像名称)
        print(f"[*] 使用国内镜像 ({镜像名称}) 加速克隆...")
        克隆地址 = 镜像地址
    else:
        克隆地址 = 仓库地址
    
    print(f"[*] 正在克隆 {克隆地址} ...")
    返回码, 输出, 错误 = 执行命令(["git", "clone", "--depth", "1", 克隆地址, 目标目录])
    if 返回码 != 0:
        print(f"[!] 克隆失败: {错误}")
        if 使用镜像:
            print("[*] 尝试使用原始地址...")
            return 克隆仓库(仓库地址, 目标目录, 使用镜像=False)
        return False
    print("[✓] 克隆成功")
    return True

def 查找README(项目路径: str) -> Optional[str]:
    for 名称 in ["README.md", "readme.md", "README", "readme"]:
        路径 = os.path.join(项目路径, 名称)
        if os.path.isfile(路径):
            return 路径
    return None

def 从文本提取命令(内容: str) -> List[str]:
    """从 Markdown 或纯文本中提取命令"""
    命令列表 = []

    # 提取代码块中的命令（支持更多语言标识）
    for 匹配 in re.finditer(r"```(?:bash|sh|shell|cmd|bat|powershell|js|ts|py|yaml|yml|docker)?\s*\n(.*?)```", 内容, re.DOTALL):
        for 行 in 匹配.group(1).splitlines():
            行 = 行.strip()
            # 过滤注释和空行
            if not 行 or 行.startswith("#") or 行.startswith("//"):
                continue
            if 行.startswith("$ "):
                行 = 行[2:]
            if 行:
                命令列表.append(行)

    # 提取以 $ 开头的行
    for 匹配 in re.finditer(r"^\$\s+(.+)$", 内容, re.MULTILINE):
        命令列表.append(匹配.group(1).strip())

    # 提取 > 提示符后的命令（如 npm install）
    for 匹配 in re.finditer(r">\s*(npm|yarn|pnpm|pip|conda|go|cargo|docker|docker-compose)\s+\w+", 内容, re.MULTILINE):
        命令列表.append(匹配.group(0).lstrip("> ").strip())

    # 提取 Windows 风格的 > 命令
    for 匹配 in re.finditer(r">\s+([a-zA-Z]:\\\.*)$", 内容, re.MULTILINE):
        命令列表.append(匹配.group(1).strip())

    # 去重保持顺序
    去重命令 = []
    for cmd in 命令列表:
        # 过滤明显的非命令
        if cmd and len(cmd) > 2 and cmd not in 去重命令:
            去重命令.append(cmd)

    return 去重命令

def 从文件提取命令(文件路径: str) -> List[str]:
    """从指定文件（.md 或 .txt）提取命令"""
    try:
        with open(文件路径, "r", encoding="utf-8", errors="ignore") as f:
            内容 = f.read()
        return 从文本提取命令(内容)
    except Exception as e:
        print(f"[!] 读取文件失败: {e}")
        return []

def 检测技术栈(项目路径: str) -> Tuple[str, Dict, List[str]]:
    文件列表 = set(os.listdir(项目路径))
    for 技术栈, 配置 in 支持的技术栈.items():
        for 特征文件 in 配置["特征文件"]:
            if 特征文件 in 文件列表:
                安装命令 = 配置["安装命令"].copy()
                启动命令 = 配置["启动命令"].copy()
                if 技术栈 == "Python":
                    for 入口 in ["app.py", "main.py", "run.py", "manage.py", "server.py"]:
                        if 入口 in 文件列表:
                            启动命令 = [f"python {入口}"]
                            break
                    # 检查是否有 requirements.txt 路径
                    if "requirements.txt" in 文件列表:
                        pass  # 使用默认配置即可
                elif 技术栈 == "Node.js":
                    pkg_json = os.path.join(项目路径, "package.json")
                    if os.path.isfile(pkg_json):
                        try:
                            with open(pkg_json, encoding="utf-8") as f:
                                pkg = json.load(f)
                            脚本 = pkg.get("scripts", {})
                            if "dev" in 脚本:
                                启动命令 = ["npm run dev"]
                            elif "start" in 脚本:
                                启动命令 = ["npm start"]
                            elif "serve" in 脚本:
                                启动命令 = ["npm run serve"]
                            # 额外检测依赖管理工具
                            if os.path.join(项目路径, "yarn.lock") in [os.path.join(项目路径, f) for f in 文件列表]:
                                # 优先用 yarn
                                pass
                        except:
                            pass
                return 技术栈, 安装命令, 启动命令
    return "未知", {}, []

def 生成启动脚本(项目路径: str, 命令列表: List[str], 环境变量: Dict[str, str] = None):
    bat路径 = os.path.join(项目路径, "run.bat")
    sh路径 = os.path.join(项目路径, "run.sh")

    with open(bat路径, "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        f.write("chcp 65001 >nul\n")
        f.write("echo 正在启动项目...\n")
        f.write("echo.\n")
        if 环境变量:
            for k, v in 环境变量.items():
                f.write(f"set {k}={v}\n")
        for cmd in 命令列表:
            f.write(f"echo [执行] {cmd}\n")
            f.write(f"{cmd}\n")
            f.write("if %errorlevel% neq 0 (\n")
            f.write("    echo [!] 命令执行失败\n")
            f.write("    pause\n")
            f.write("    exit /b 1\n")
            f.write(")\n")
        f.write("echo.\n")
        f.write("echo 完成！按任意键退出...\n")
        f.write("pause >nul\n")

    with open(sh路径, "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\n")
        f.write("set -e\n")
        f.write("echo '正在启动问题...'\n")
        f.write("echo\n")
        if 环境变量:
            for k, v in 环境变量.items():
                f.write(f"export {k}='{v}'\n")
        for cmd in 命令列表:
            f.write(f"echo '[执行] {cmd}'\n")
            f.write(f"{cmd}\n")
        f.write("echo\n")
        f.write("echo '完成！'")

    os.chmod(sh路径, 0o755)

    print(f"[✓] 已生成启动脚本：{bat路径}, {sh路径}")

def 检查并处理缺失环境() -> bool:
    print("\n[*] 正在检测本地环境...")
    print(format_env_report())

    缺失列表 = check_missing_tools(["git"])
    env = get_full_environment_report()
    if not env["python"]["installed"]:
        缺失列表.append("python")
    if not env["nodejs"]["installed"]:
        缺失列表.append("nodejs")
    if not env["go"]["installed"]:
        缺失列表.append("go")
    if not env["rust"]["installed"]:
        缺失列表.append("rust")

    if not 缺失列表:
        print("[✓] 所有必要环境已就绪！")
        return True

    print(f"\n[!] 检测到缺失以下环境: {', '.join(缺失列表)}")
    for 工具 in 缺失列表:
        print(generate_install_guide(工具))

    回答 = 询问用户("是否已安装缺失的环境？", ["是", "否", "稍后"], "是")
    if 回答 == "否":
        return False
    return True

def 获取用户部署说明() -> Optional[List[str]]:
    """询问用户是否导入外部说明文件，若导入则返回提取的命令"""
    if not 询问用户("是否导入外部部署说明文件（.md 或 .txt）？", ["是", "否"], "否") == "是":
        return None
    
    while True:
        文件路径 = 询问用户("请输入部署说明文件的完整路径", 默认值="")
        if not 文件路径:
            return None
        if not os.path.isfile(文件路径):
            print(f"[!] 文件不存在: {文件路径}")
            continue
        if not (文件路径.endswith(".md") or 文件路径.endswith(".txt")):
            print("[!] 仅支持 .md 或 .txt 文件")
            continue
        
        命令列表 = 从文件提取命令(文件路径)
        if not 命令列表:
            print("[!] 未能从文件中提取到命令，请确认文件格式。")
            if 询问用户("是否重新选择文件？", ["是", "否"], "是") == "是":
                continue
            return None
        print(f"[*] 从文件中提取到 {len(命令列表)} 条命令。")
        return 命令列表

# ========== 主流程 ==========
def main():
    if len(sys.argv) < 2:
        print("用法: python launcher.py <github地址或本地路径> [--auto]")
        sys.exit(1)
    
    目标 = sys.argv[1]
    自动模式 = "--auto" in sys.argv
    
    # 环境检测
    if not 检查并处理缺失环境():
        print("[!] 环境未就绪，请先安装必要的工具。")
        sys.exit(1)
    
    # 判断来源
    if 目标.startswith("http") or "github.com" in 目标:
        来源 = "github"
        仓库名 = 目标.rstrip("/").split("/")[-1].replace(".git", "")
        项目路径 = os.path.join(os.getcwd(), 仓库名)
    else:
        来源 = "local"
        项目路径 = os.path.abspath(目标)
    
    # 获取项目
    if 来源 == "github":
        if os.path.exists(项目路径):
            回答 = 询问用户(f"目录 '{项目路径}' 已存在。如何处理？", ["覆盖", "使用现有", "取消"], "使用现有")
            if 回答 == "覆盖":
                shutil.rmtree(项目路径)
            elif 回答 == "取消":
                sys.exit(1)
        if not os.path.exists(项目路径):
            if not 克隆仓库(目标, 项目路径, 使用镜像=True):
                sys.exit(1)
    else:
        if not os.path.isdir(项目路径):
            print(f"[!] 本地路径 '{项目路径}' 不存在。")
            sys.exit(1)
    
    os.chdir(项目路径)
    print(f"[*] 当前工作目录：{项目路径}")
    
    # ========== 新增：检查 README 并询问导入外部说明 ==========
    内置readme路径 = 查找README(项目路径)
    if 内置readme路径:
        print(f"[*] 项目内已有 README 文件: {os.path.basename(内置readme路径)}")
    else:
        print("[!] 项目内未找到 README 文件")
    
    外部命令 = 获取用户部署说明()
    if 外部命令 is not None:
        # 用户提供了外部说明，直接使用
        最终命令 = 外部命令
        技术栈 = "用户导入"
        print(f"[*] 将使用导入文件中的 {len(最终命令)} 条命令。")
        # 跳过技术栈检测和 README 提取
    else:
        # 正常流程：检测技术栈 + 提取 README
        技术栈, 安装命令, 启动命令 = 检测技术栈(项目路径)
        if 技术栈 == "未知":
            print("[!] 未能自动检测项目类型。")
            技术栈 = 询问用户("请选择项目类型", ["Node.js", "Python", "Go", "Rust", "Docker", "其他"], "Node.js")
            if 技术栈 == "其他":
                sys.exit(1)
            安装命令 = 支持的技术栈.get(技术栈, {}).get("安装命令", [])
            启动命令 = 支持的技术栈.get(技术栈, {}).get("启动命令", [])
        print(f"[*] 检测到技术栈：{技术栈}")
        
        # 提取内置 README 命令
        readme命令 = []
        if 内置readme路径:
            readme命令 = 从文件提取命令(内置readme路径)
            print(f"[*] 从 README 中提取到 {len(readme命令)} 条命令。")
        
        if readme命令:
            最终命令 = readme命令
        else:
            最终命令 = 安装命令 + 启动命令
        
        # 自动配置国内镜像源
        if 技术栈 == "Python":
            configure_pip_mirror("清华")
            print("[*] 已配置 pip 国内镜像源（清华）")
        elif 技术栈 == "Node.js":
            configure_npm_mirror("阿里云/npmmirror")
            print("[*] 已配置 npm 国内镜像源（阿里云）")
    
    # ========== 环境偏好询问 ==========
    环境变量 = {}
    if not 自动模式 and 技术栈 in 支持的技术栈:
        for 问题项 in 支持的技术栈[技术栈].get("环境问题", []):
            回答 = 询问用户(问题项["问题"], 问题项.get("选项"), 问题项.get("默认"))
            if 技术栈 == "Python" and 回答 == "venv":
                最终命令.insert(0, "python -m venv venv")
                if os.name == "nt":
                    最终命令.insert(1, "venv\\Scripts\\activate")
                else:
                    最终命令.insert(1, "source venv/bin/activate")
            elif 技术栈 == "Node.js" and 回答 != "npm":
                最终命令 = [cmd.replace("npm", 回答) for cmd in 最终命令]
    
    # ========== 确认并生成 ==========
    print("\n[*] 将执行以下命令：")
    for i, cmd in enumerate(最终命令, 1):
        print(f"    {i}. {cmd}")
    
    if not 自动模式:
        回答 = 询问用户("是否按此命令列表生成脚本？", ["是", "否", "编辑"], "是")
        if 回答 == "否":
            sys.exit(1)
        elif 回答 == "编辑":
            print("请逐行输入命令（空行结束）：")
            新命令 = []
            while True:
                行 = sys.stdin.readline().strip()
                if not 行:
                    break
                新命令.append(行)
            if 新命令:
                最终命令 = 新命令
    
    生成启动脚本(项目路径, 最终命令, 环境变量)
    print("\n[✓] 项目启动器已就绪！")
    print(f"    请运行：{项目路径}/run.bat (Windows) 或 ./run.sh (Mac/Linux)")

if __name__ == "__main__":
    main()