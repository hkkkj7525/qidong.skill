#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能环境检测模块 - 自动检测 Node.js、Python、Git 等环境
"""

import os
import sys
import subprocess
import re
import json
from typing import Dict, List, Tuple, Optional

# ========== 环境检测函数 ==========

def detect_os() -> str:
    """检测操作系统"""
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "macos"
    else:
        return "linux"

def detect_docker() -> Tuple[bool, str]:
    """检测 Docker"""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            match = re.search(r"Docker version ([\d\.]+)", version)
            if match:
                return True, match.group(1)
            return True, version
    except:
        pass
    return False, ""

def detect_rust() -> Tuple[bool, str]:
    """检测 Rust"""
    try:
        result = subprocess.run(["rustc", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            match = re.search(r"rustc ([\d\.]+)", version)
            if match:
                return True, match.group(1)
            return True, version
    except:
        pass
    return False, ""

def detect_go() -> Tuple[bool, str]:
    """检测 Go"""
    try:
        result = subprocess.run(["go", "version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            match = re.search(r"go([\d\.]+)", version)
            if match:
                return True, match.group(1)
            return True, version
    except:
        pass
    return False, ""

def detect_yarn() -> Tuple[bool, str]:
    """检测 Yarn"""
    try:
        result = subprocess.run(["yarn", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return True, result.stdout.strip()
    except:
        pass
    return False, ""

def detect_pnpm() -> Tuple[bool, str]:
    """检测 pnpm"""
    try:
        result = subprocess.run(["pnpm", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return True, result.stdout.strip()
    except:
        pass
    return False, ""

def detect_conda() -> Tuple[bool, str]:
    """检测 Conda"""
    try:
        result = subprocess.run(["conda", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return True, result.stdout.strip()
    except:
        pass
    return False, "" -> Tuple[bool, str, str]:
    """
    检测 Python 环境
    返回: (是否安装, 版本号, 可执行文件路径)
    """
    for cmd in ["python3", "python", "py"]:
        try:
            result = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip() or result.stderr.strip()
                # 提取版本号
                match = re.search(r"Python\s+([\d\.]+)", version)
                if match:
                    version = match.group(1)
                # 获取完整路径
                path_result = subprocess.run([cmd, "-c", "import sys; print(sys.executable)"], 
                                            capture_output=True, text=True, timeout=5)
                path = path_result.stdout.strip() if path_result.returncode == 0 else cmd
                return True, version, path
        except:
            continue
    return False, "", ""

def detect_nodejs() -> Tuple[bool, str, str]:
    """
    检测 Node.js 环境
    返回: (是否安装, 版本号, 可执行文件路径)
    """
    for cmd in ["node"]:
        try:
            result = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip().lstrip('v')
                # 获取路径
                path_result = subprocess.run(["where" if os.name == "nt" else "which", cmd],
                                            capture_output=True, text=True, timeout=5)
                path = path_result.stdout.strip().split('\n')[0] if path_result.returncode == 0 else cmd
                return True, version, path
        except:
            continue
    return False, "", ""

def detect_npm() -> Tuple[bool, str]:
    """检测 npm"""
    try:
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return True, result.stdout.strip()
    except:
        pass
    return False, ""

def detect_git() -> Tuple[bool, str]:
    """检测 Git"""
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            match = re.search(r"git version ([\d\.]+)", version)
            if match:
                return True, match.group(1)
            return True, version
    except:
        pass
    return False, ""

def detect_pip() -> Tuple[bool, str]:
    """检测 pip"""
    for cmd in ["pip3", "pip"]:
        try:
            result = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return True, result.stdout.strip()
        except:
            continue
    return False, ""

def get_full_environment_report() -> Dict:
    """获取完整环境报告"""
    os_type = detect_os()
    python_ok, python_ver, python_path = detect_python()
    node_ok, node_ver, node_path = detect_nodejs()
    npm_ok, npm_ver = detect_npm()
    git_ok, git_ver = detect_git()
    pip_ok, pip_ver = detect_pip()
    docker_ok, docker_ver = detect_docker()
    rust_ok, rust_ver = detect_rust()
    go_ok, go_ver = detect_go()
    yarn_ok, yarn_ver = detect_yarn()
    pnpm_ok, pnpm_ver = detect_pnpm()
    conda_ok, conda_ver = detect_conda()

    return {
        "os": os_type,
        "python": {"installed": python_ok, "version": python_ver, "path": python_path},
        "nodejs": {"installed": node_ok, "version": node_ver, "path": node_path},
        "npm": {"installed": npm_ok, "version": npm_ver},
        "yarn": {"installed": yarn_ok, "version": yarn_ver},
        "pnpm": {"installed": pnpm_ok, "version": pnpm_ver},
        "git": {"installed": git_ok, "version": git_ver},
        "pip": {"installed": pip_ok, "version": pip_ver},
        "docker": {"installed": docker_ok, "version": docker_ver},
        "rust": {"installed": rust_ok, "version": rust_ver},
        "go": {"installed": go_ok, "version": go_ver},
        "conda": {"installed": conda_ok, "version": conda_ver},
    }

def check_missing_tools(required: List[str] = None) -> List[str]:
    """检查缺失的工具"""
    if required is None:
        required = ["git", "python", "nodejs"]

    missing = []
    env = get_full_environment_report()

    for tool in required:
        if tool == "git" and not env["git"]["installed"]:
            missing.append("git")
        elif tool == "python" and not env["python"]["installed"]:
            missing.append("python")
        elif tool == "nodejs" and not env["nodejs"]["installed"]:
            missing.append("nodejs")
        elif tool == "go" and not env["go"]["installed"]:
            missing.append("go")
        elif tool == "rust" and not env["rust"]["installed"]:
            missing.append("rust")
        elif tool == "docker" and not env["docker"]["installed"]:
            missing.append("docker")

    return missing

def format_env_report() -> str:
    """格式化环境报告"""
    env = get_full_environment_report()
    lines = []
    lines.append("【环境检测结果】")
    lines.append(f"  操作系统: {env['os']}")
    lines.append(f"  Python: {'✓ ' + env['python']['version'] if env['python']['installed'] else '✗ 未安装'}")
    if env['conda']['installed']:
        lines.append(f"  Conda: {'✓ ' + env['conda']['version']}")
    lines.append(f"  Node.js: {'✓ v' + env['nodejs']['version'] if env['nodejs']['installed'] else '✗ 未安装'}")
    lines.append(f"  npm: {'✓ ' + env['npm']['version'] if env['npm']['installed'] else '✗ 未安装'}")
    if env['yarn']['installed']:
        lines.append(f"  Yarn: {'✓ ' + env['yarn']['version']}")
    if env['pnpm']['installed']:
        lines.append(f"  pnpm: {'✓ ' + env['pnpm']['version']}")
    if env['go']['installed']:
        lines.append(f"  Go: {'✓ ' + env['go']['version']}")
    if env['rust']['installed']:
        lines.append(f"  Rust: {'✓ ' + env['rust']['version']}")
    if env['docker']['installed']:
        lines.append(f"  Docker: {'✓ ' + env['docker']['version']}")
    lines.append(f"  Git: {'✓ ' + env['git']['version'] if env['git']['installed'] else '✗ 未安装'}")
    return "\n".join(lines)

# ========== 命令行入口 ==========
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        print(json.dumps(get_full_environment_report(), ensure_ascii=False, indent=2))
    else:
        print(format_env_report())