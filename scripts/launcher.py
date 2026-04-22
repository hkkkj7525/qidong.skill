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

from env_detector import (
    get_full_environment_report, format_env_report,
    check_missing_tools, detect_os
)
from installer import (
    get_github_mirror_url, get_best_available_github_mirror,
    generate_install_guide, configure_pip_mirror, configure_npm_mirror
)

# ========== 全局自动模式标志 ==========
AUTO_MODE = False

# ========== 安全命令白名单 ==========
ALLOWED_COMMAND_PREFIXES = [
    "npm", "npx", "yarn", "pnpm", "node",
    "pip", "pip3", "python", "python3", "py",
    "go", "cargo", "rustc",
    "docker", "docker-compose",
    "make", "cmake",
    "echo", "cd", "dir", "ls", "pwd"
]
# 禁止使用的危险字符
DANGEROUS_CHARS = ['&', '|', ';', '`', '$', '>', '<', '\\', '(']

def is_safe_command(cmd: str) -> bool:
    """检查命令是否安全（白名单+危险字符过滤）"""
    cmd_stripped = cmd.strip()
    if not cmd_stripped:
        return False
    # 禁止危险字符
    for ch in DANGEROUS_CHARS:
        if ch in cmd_stripped:
            return False
    # 获取命令的第一个词（忽略 sudo 等前缀）
    first_word = cmd_stripped.split()[0].lower()
    # 允许 sudo 前缀
    if first_word == "sudo":
        if len(cmd_stripped.split()) > 1:
            first_word = cmd_stripped.split()[1].lower()
        else:
            return False
    return first_word in ALLOWED_COMMAND_PREFIXES

def filter_commands(commands: List[str]) -> List[str]:
    """过滤不安全命令，只保留白名单内的"""
    safe = []
    for cmd in commands:
        if is_safe_command(cmd):
            safe.append(cmd)
        else:
            print(f"[!] 跳过不安全的命令: {cmd}")
    return safe

# ========== 支持的技术栈 ==========
SUPPORTED_STACKS = {
    "Node.js": {
        "特征文件": ["package.json"],
        "安装命令": ["npm install --registry=https://registry.npmmirror.com/"],
        "启动命令": ["npm start", "npm run dev", "npm run serve"],
        "环境问题": [{"问题": "请选择包管理器？", "选项": ["npm", "yarn", "pnpm"], "默认": "npm"}]
    },
    "Python": {
        "特征文件": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"],
        "安装命令": ["pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/"],
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

def ask_user(question: str, options: List[str] = None, default: str = None) -> str:
    """交互式询问用户，自动模式下直接返回默认值"""
    global AUTO_MODE
    if AUTO_MODE:
        if default is not None:
            return default
        if options and len(options) > 0:
            return options[0]
        return ""
    if options:
        options_str = "/".join(options)
        prompt = f"[?] {question} ({options_str})"
        if default:
            prompt += f" [默认: {default}]"
    else:
        prompt = f"[?] {question}"
    print(prompt)
    sys.stdout.flush()
    answer = sys.stdin.readline().strip()
    if not answer and default:
        return default
    return answer

def run_command(cmd_list: List[str], cwd: str = None, timeout: int = 60) -> Tuple[int, str, str]:
    """执行命令，返回 (返回码, stdout, stderr)"""
    try:
        result = subprocess.run(cmd_list, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "命令执行超时"
    except Exception as e:
        return -1, "", str(e)

def clone_repo(repo_url: str, target_dir: str, use_mirror: bool = True, depth: int = 0) -> bool:
    """克隆仓库，支持国内镜像加速，限制递归深度防止无限循环"""
    if depth > 2:
        print("[!] 克隆重试次数过多，放弃")
        return False
    if use_mirror and "github.com" in repo_url:
        mirror_name = get_best_available_github_mirror()
        mirror_url = get_github_mirror_url(repo_url, mirror_name)
        print(f"[*] 使用国内镜像 ({mirror_name}) 加速克隆...")
        clone_url = mirror_url
    else:
        clone_url = repo_url
    print(f"[*] 正在克隆 {clone_url} ...")
    ret, out, err = run_command(["git", "clone", "--depth", "1", clone_url, target_dir])
    if ret != 0:
        print(f"[!] 克隆失败: {err}")
        if use_mirror:
            print("[*] 尝试使用原始地址...")
            return clone_repo(repo_url, target_dir, use_mirror=False, depth=depth+1)
        return False
    print("[✓] 克隆成功")
    return True

def find_readme(project_path: str) -> Optional[str]:
    for name in ["README.md", "readme.md", "README", "readme"]:
        path = os.path.join(project_path, name)
        if os.path.isfile(path):
            return path
    return None

def extract_commands_from_text(content: str) -> List[str]:
    """从 Markdown 或纯文本中提取命令（更严格，只提取代码块中的 bash/sh/shell）"""
    commands = []
    # 只提取代码块中的命令
    pattern = r"```(?:bash|sh|shell|cmd|bat|powershell)\s*\n(.*?)```"
    for match in re.finditer(pattern, content, re.DOTALL):
        for line in match.group(1).splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("//"):
                continue
            if line.startswith("$ "):
                line = line[2:]
            if line and is_safe_command(line):
                commands.append(line)
    # 去重保持顺序
    seen = set()
    unique = []
    for cmd in commands:
        if cmd not in seen:
            seen.add(cmd)
            unique.append(cmd)
    return unique

def extract_commands_from_file(file_path: str) -> List[str]:
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return extract_commands_from_text(content)
    except Exception as e:
        print(f"[!] 读取文件失败: {e}")
        return []

def detect_stack(project_path: str) -> Tuple[str, List[str], List[str]]:
    """检测技术栈，返回 (技术栈名称, 安装命令列表, 启动命令列表)"""
    files = set(os.listdir(project_path))
    for stack, config in SUPPORTED_STACKS.items():
        for marker in config["特征文件"]:
            if marker in files:
                install_cmds = config["安装命令"].copy()
                start_cmds = config["启动命令"].copy()
                if stack == "Python":
                    for entry in ["app.py", "main.py", "run.py", "manage.py", "server.py"]:
                        if entry in files:
                            start_cmds = [f"python {entry}"]
                            break
                elif stack == "Node.js":
                    pkg_json = os.path.join(project_path, "package.json")
                    if os.path.isfile(pkg_json):
                        try:
                            with open(pkg_json, encoding="utf-8") as f:
                                pkg = json.load(f)
                            scripts = pkg.get("scripts", {})
                            if "dev" in scripts:
                                start_cmds = ["npm run dev"]
                            elif "start" in scripts:
                                start_cmds = ["npm start"]
                            elif "serve" in scripts:
                                start_cmds = ["npm run serve"]
                        except Exception:
                            pass
                # 过滤不安全命令
                install_cmds = filter_commands(install_cmds)
                start_cmds = filter_commands(start_cmds)
                return stack, install_cmds, start_cmds
    return "未知", [], []

def generate_script(project_path: str, commands: List[str], env_vars: Dict[str, str] = None):
    """生成启动脚本，只包含安全命令"""
    if not commands:
        print("[!] 没有可用的安全命令，不生成脚本")
        return
    bat_path = os.path.join(project_path, "run.bat")
    sh_path = os.path.join(project_path, "run.sh")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        f.write("chcp 65001 >nul\n")
        f.write("echo 正在启动项目...\n")
        f.write("echo.\n")
        if env_vars:
            for k, v in env_vars.items():
                f.write(f"set {k}={v}\n")
        for cmd in commands:
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
    with open(sh_path, "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\n")
        f.write("set -e\n")
        f.write("echo '正在启动项目...'\n")
        f.write("echo\n")
        if env_vars:
            for k, v in env_vars.items():
                f.write(f"export {k}='{v}'\n")
        for cmd in commands:
            f.write(f"echo '[执行] {cmd}'\n")
            f.write(f"{cmd}\n")
        f.write("echo\n")
        f.write("echo '完成！'\n")
    os.chmod(sh_path, 0o755)
    print(f"[✓] 已生成启动脚本：{bat_path}, {sh_path}")

def check_and_handle_missing_env() -> bool:
    print("\n[*] 正在检测本地环境...")
    print(format_env_report())
    missing = check_missing_tools(["git"])
    env = get_full_environment_report()
    if not env["python"]["installed"]:
        missing.append("python")
    if not env["nodejs"]["installed"]:
        missing.append("nodejs")
    if not env["go"]["installed"]:
        missing.append("go")
    if not env["rust"]["installed"]:
        missing.append("rust")
    if not missing:
        print("[✓] 所有必要环境已就绪！")
        return True
    print(f"\n[!] 检测到缺失以下环境: {', '.join(missing)}")
    for tool in missing:
        print(generate_install_guide(tool))
    answer = ask_user("是否已安装缺失的环境？", ["是", "否", "稍后"], "是")
    return answer == "是"

def get_user_deployment_commands() -> Optional[List[str]]:
    if ask_user("是否导入外部部署说明文件（.md 或 .txt）？", ["是", "否"], "否") != "是":
        return None
    while True:
        file_path = ask_user("请输入部署说明文件的完整路径", default="")
        if not file_path:
            return None
        if not os.path.isfile(file_path):
            print(f"[!] 文件不存在: {file_path}")
            continue
        if not (file_path.endswith(".md") or file_path.endswith(".txt")):
            print("[!] 仅支持 .md 或 .txt 文件")
            continue
        commands = extract_commands_from_file(file_path)
        if not commands:
            print("[!] 未能从文件中提取到安全命令，请确认文件格式。")
            if ask_user("是否重新选择文件？", ["是", "否"], "是") == "是":
                continue
            return None
        print(f"[*] 从文件中提取到 {len(commands)} 条安全命令。")
        return commands

# ========== 主流程 ==========
def main():
    global AUTO_MODE
    if len(sys.argv) < 2:
        print("用法: python launcher.py <github地址或本地路径> [--auto]")
        sys.exit(1)
    target = sys.argv[1]
    AUTO_MODE = "--auto" in sys.argv

    if not check_and_handle_missing_env():
        print("[!] 环境未就绪，请先安装必要的工具。")
        sys.exit(1)

    # 判断来源
    if target.startswith("http") or "github.com" in target:
        source = "github"
        repo_name = target.rstrip("/").split("/")[-1].replace(".git", "")
        project_path = os.path.join(os.getcwd(), repo_name)
    else:
        source = "local"
        project_path = os.path.abspath(target)

    # 获取项目
    if source == "github":
        if os.path.exists(project_path):
            answer = ask_user(f"目录 '{project_path}' 已存在。如何处理？", ["覆盖", "使用现有", "取消"], "使用现有")
            if answer == "覆盖":
                shutil.rmtree(project_path)
            elif answer == "取消":
                sys.exit(1)
        if not os.path.exists(project_path):
            if not clone_repo(target, project_path, use_mirror=True):
                sys.exit(1)
    else:
        if not os.path.isdir(project_path):
            print(f"[!] 本地路径 '{project_path}' 不存在。")
            sys.exit(1)

    os.chdir(project_path)
    print(f"[*] 当前工作目录：{project_path}")

    readme_path = find_readme(project_path)
    if readme_path:
        print(f"[*] 项目内已有 README 文件: {os.path.basename(readme_path)}")
    else:
        print("[!] 项目内未找到 README 文件")

    external_commands = get_user_deployment_commands()
    if external_commands is not None:
        final_commands = external_commands
        stack = "用户导入"
        print(f"[*] 将使用导入文件中的 {len(final_commands)} 条安全命令。")
    else:
        stack, install_cmds, start_cmds = detect_stack(project_path)
        if stack == "未知":
            print("[!] 未能自动检测项目类型。")
            stack = ask_user("请选择项目类型", ["Node.js", "Python", "Go", "Rust", "Docker", "其他"], "Node.js")
            if stack == "其他":
                sys.exit(1)
            install_cmds = SUPPORTED_STACKS.get(stack, {}).get("安装命令", [])
            start_cmds = SUPPORTED_STACKS.get(stack, {}).get("启动命令", [])
            install_cmds = filter_commands(install_cmds)
            start_cmds = filter_commands(start_cmds)
        print(f"[*] 检测到技术栈：{stack}")

        readme_commands = []
        if readme_path:
            readme_commands = extract_commands_from_file(readme_path)
            print(f"[*] 从 README 中提取到 {len(readme_commands)} 条安全命令。")
        if readme_commands:
            final_commands = readme_commands
        else:
            final_commands = install_cmds + start_cmds

        # 配置国内镜像源
        if stack == "Python":
            configure_pip_mirror("清华")
            print("[*] 已配置 pip 国内镜像源（清华）")
        elif stack == "Node.js":
            configure_npm_mirror("阿里云/npmmirror")
            print("[*] 已配置 npm 国内镜像源（阿里云）")

    # 环境偏好询问（虚拟环境等）
    env_vars = {}
    if not AUTO_MODE and stack in SUPPORTED_STACKS:
        for q in SUPPORTED_STACKS[stack].get("环境问题", []):
            answer = ask_user(q["问题"], q.get("选项"), q.get("默认"))
            if stack == "Python" and answer == "venv":
                if os.name == "nt":
                    activate_cmd = "venv\\Scripts\\activate"
                else:
                    activate_cmd = "source venv/bin/activate"
                final_commands = ["python -m venv venv", activate_cmd] + final_commands
            elif stack == "Node.js" and answer != "npm":
                new_cmds = []
                for cmd in final_commands:
                    if cmd.startswith("npm "):
                        cmd = cmd.replace("npm", answer, 1)
                    new_cmds.append(cmd)
                final_commands = new_cmds

    # 再次过滤确保所有命令安全
    final_commands = filter_commands(final_commands)
    if not final_commands:
        print("[!] 没有可用的安全命令，无法生成启动脚本。")
        sys.exit(1)

    print("\n[*] 将执行以下安全命令：")
    for i, cmd in enumerate(final_commands, 1):
        print(f"    {i}. {cmd}")

    if not AUTO_MODE:
        answer = ask_user("是否按此命令列表生成脚本？", ["是", "否", "编辑"], "是")
        if answer == "否":
            sys.exit(1)
        elif answer == "编辑":
            print("请逐行输入命令（空行结束）：")
            new_cmds = []
            while True:
                line = sys.stdin.readline().strip()
                if not line:
                    break
                if is_safe_command(line):
                    new_cmds.append(line)
                else:
                    print(f"[!] 跳过不安全命令: {line}")
            if new_cmds:
                final_commands = new_cmds
            else:
                print("[!] 未输入有效命令，退出")
                sys.exit(1)

    generate_script(project_path, final_commands, env_vars)
    print("\n[✓] 项目启动器已就绪！")
    print(f"    请运行：{project_path}/run.bat (Windows) 或 ./run.sh (Mac/Linux)")

if __name__ == "__main__":
    main()
