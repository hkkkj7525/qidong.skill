#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
国内镜像安装模块 - 通过国内加速源下载安装 Node.js、Python、Git
"""

import os
import sys
import subprocess
import urllib.request
import urllib.parse
import json
from typing import Optional, Tuple

# ========== 国内镜像源配置 ==========

NODE_MIRRORS = {
    "阿里云/npmmirror": "https://npmmirror.com/mirrors/node/",
    "华为云": "https://mirrors.huaweicloud.com/nodejs/",
    "腾讯云": "https://mirrors.cloud.tencent.com/nodejs-release/",
    "清华": "https://mirrors.tuna.tsinghua.edu.cn/nodejs-release/",
}

PYTHON_MIRRORS = {
    "华为云": "https://repo.huaweicloud.com/python/",
    "清华": "https://mirrors.tuna.tsinghua.edu.cn/python/",
    "阿里云": "https://mirrors.aliyun.com/python/",
    "腾讯云": "https://mirrors.cloud.tencent.com/python/",
}

# GitHub 加速镜像（移除已失效的）
GITHUB_MIRRORS = {
    "kgithub": "https://kgithub.com/",
    "gitclone": "https://gitclone.com/github.com/",
    "mirrorgh": "https://mirror.ghproxy.com/",
}

PIP_MIRRORS = {
    "清华": "https://pypi.tuna.tsinghua.edu.cn/simple/",
    "阿里云": "https://mirrors.aliyun.com/pypi/simple/",
    "华为云": "https://repo.huaweicloud.com/repository/pypi/simple/",
    "腾讯云": "https://mirrors.cloud.tencent.com/pypi/simple/",
    "中科大": "https://pypi.mirrors.ustc.edu.cn/simple/",
}

NPM_MIRRORS = {
    "阿里云/npmmirror": "https://registry.npmmirror.com/",
    "腾讯云": "https://mirrors.cloud.tencent.com/npm/",
    "华为云": "https://mirrors.huaweicloud.com/repository/npm/",
}

# ========== 辅助函数 ==========

def detect_os() -> str:
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "macos"
    else:
        return "linux"

def test_mirror_availability(mirror_url: str) -> bool:
    """测试镜像源是否可用"""
    try:
        req = urllib.request.Request(mirror_url, method='HEAD')
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except Exception:
        return False

def get_best_available_github_mirror() -> str:
    """获取当前可用的最佳 GitHub 镜像"""
    # 按优先级排序
    mirrors = ["kgithub", "mirrorgh", "gitclone"]
    for name in mirrors:
        url = GITHUB_MIRRORS.get(name, "")
        if url and test_mirror_availability(url):
            return name
    return "kgithub"  # 默认

def get_github_mirror_url(github_url: str, mirror: str = "kgithub") -> str:
    """将 GitHub URL 转换为国内镜像 URL"""
    if "github.com" in github_url:
        repo_path = github_url.split("github.com/")[-1].replace(".git", "")
    else:
        repo_path = github_url
    base = GITHUB_MIRRORS.get(mirror, "https://kgithub.com/")
    return base + repo_path

# ========== 下载链接获取（简化，不再自动获取最新版，避免网络依赖）==========

def get_nodejs_download_url(version: str = "20.18.0", os_type: str = None) -> Optional[str]:
    if os_type is None:
        os_type = detect_os()
    base_url = NODE_MIRRORS["阿里云/npmmirror"]
    if os_type == "windows":
        filename = f"node-v{version}-x64.msi"
    elif os_type == "macos":
        filename = f"node-v{version}-darwin-x64.tar.gz"
    else:
        filename = f"node-v{version}-linux-x64.tar.xz"
    return base_url + f"v{version}/" + filename

def get_python_download_url(version: str = "3.12.0", os_type: str = None) -> Optional[str]:
    if os_type is None:
        os_type = detect_os()
    base_url = PYTHON_MIRRORS["华为云"]
    if os_type == "windows":
        filename = f"python-{version}-amd64.exe"
    elif os_type == "macos":
        filename = f"python-{version}-macos11.pkg"
    else:
        filename = f"Python-{version}.tgz"
    return base_url + f"{version}/" + filename

def get_git_download_url(os_type: str = None) -> Optional[str]:
    if os_type is None:
        os_type = detect_os()
    if os_type == "windows":
        return "https://repo.huaweicloud.com/git-for-windows/v2.47.0.windows.1/Git-2.47.0-64-bit.exe"
    elif os_type == "macos":
        return "https://repo.huaweicloud.com/git-for-mac/git-latest.pkg"
    else:
        return "https://repo.huaweicloud.com/git/git-2.47.0.tar.gz"

# ========== 镜像源配置 ==========

def configure_pip_mirror(mirror: str = "清华") -> bool:
    mirror_url = PIP_MIRRORS.get(mirror, PIP_MIRRORS["清华"])
    try:
        subprocess.run(["pip", "config", "set", "global.index-url", mirror_url],
                       capture_output=True, timeout=10, check=False)
        subprocess.run(["pip3", "config", "set", "global.index-url", mirror_url],
                       capture_output=True, timeout=10, check=False)
        return True
    except Exception:
        return False

def configure_npm_mirror(mirror: str = "阿里云/npmmirror") -> bool:
    mirror_url = NPM_MIRRORS.get(mirror, NPM_MIRRORS["阿里云/npmmirror"])
    try:
        subprocess.run(["npm", "config", "set", "registry", mirror_url],
                       capture_output=True, timeout=10, check=False)
        return True
    except Exception:
        return False

# ========== 安装指引 ==========

def generate_install_guide(tool: str, os_type: str = None) -> str:
    if os_type is None:
        os_type = detect_os()
    guides = {
        "nodejs": {
            "windows": {
                "download": get_nodejs_download_url("20.18.0", "windows"),
                "steps": [
                    "1. 下载安装包（国内镜像加速）",
                    "2. 双击运行安装程序",
                    "3. 勾选 'Automatically install necessary tools'",
                    "4. 完成安装后重启命令行"
                ]
            },
            "macos": {
                "download": get_nodejs_download_url("20.18.0", "macos"),
                "steps": [
                    "1. 下载 pkg 安装包",
                    "2. 双击运行安装",
                    "3. 或使用 Homebrew: brew install node"
                ]
            },
            "linux": {
                "steps": [
                    "1. 使用包管理器: sudo apt install nodejs npm (Debian/Ubuntu)",
                    "2. 或下载预编译包解压到 /usr/local"
                ]
            }
        },
        "python": {
            "windows": {
                "download": get_python_download_url("3.12.0", "windows"),
                "steps": [
                    "1. 下载安装包（国内镜像加速）",
                    "2. 勾选 'Add Python to PATH'",
                    "3. 点击 Install Now",
                    "4. 完成安装"
                ]
            },
            "macos": {
                "download": get_python_download_url("3.12.0", "macos"),
                "steps": [
                    "1. 下载 pkg 安装包",
                    "2. 双击安装",
                    "3. 或使用 Homebrew: brew install python@3.12"
                ]
            },
            "linux": {
                "steps": [
                    "1. 使用包管理器: sudo apt install python3 python3-pip"
                ]
            }
        },
        "git": {
            "windows": {
                "download": get_git_download_url("windows"),
                "steps": [
                    "1. 下载 Git 安装包",
                    "2. 运行安装程序",
                    "3. 选择默认选项即可"
                ]
            },
            "macos": {
                "steps": ["1. 使用 Homebrew: brew install git"]
            },
            "linux": {
                "steps": ["1. 使用包管理器: sudo apt install git"]
            }
        }
    }
    tool_guide = guides.get(tool, {})
    os_guide = tool_guide.get(os_type, {})
    lines = [f"\n【{tool.upper()} 安装指引 - {os_type}】"]
    if "download" in os_guide:
        lines.append(f"\n📥 国内镜像下载地址：\n   {os_guide['download']}")
    if "steps" in os_guide:
        lines.append("\n📋 安装步骤：")
        lines.extend(f"   {step}" for step in os_guide["steps"])
    return "\n".join(lines)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python installer.py <tool> [os]")
        sys.exit(1)
    tool = sys.argv[1]
    os_type = sys.argv[2] if len(sys.argv) > 2 else None
    if tool == "nodejs":
        print(get_nodejs_download_url("20.18.0", os_type))
    elif tool == "python":
        print(get_python_download_url("3.12.0", os_type))
    elif tool == "git":
        print(get_git_download_url(os_type))
    elif tool == "guide":
        for t in ["nodejs", "python", "git"]:
            print(generate_install_guide(t, os_type))
            print()
    elif tool == "mirrors":
        print(get_best_available_github_mirror())
