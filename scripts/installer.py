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
import tempfile
import shutil
from typing import Dict, List, Optional, Tuple

# ========== 国内镜像源配置 ==========

# Node.js 下载镜像源
NODE_MIRRORS = {
    "阿里云/npmmirror": "https://npmmirror.com/mirrors/node/",
    "华为云": "https://mirrors.huaweicloud.com/nodejs/",
    "腾讯云": "https://mirrors.cloud.tencent.com/nodejs-release/",
    "清华": "https://mirrors.tuna.tsinghua.edu.cn/nodejs-release/",
}

# Python 下载镜像源
PYTHON_MIRRORS = {
    "华为云": "https://repo.huaweicloud.com/python/",
    "清华": "https://mirrors.tuna.tsinghua.edu.cn/python/",
    "阿里云": "https://mirrors.aliyun.com/python/",
    "腾讯云": "https://mirrors.cloud.tencent.com/python/",
}

# GitHub 加速镜像
GITHUB_MIRRORS = {
    "kgithub": "https://kgithub.com/",
    "gitclone": "https://gitclone.com/github.com/",
    "ghproxy": "https://ghproxy.com/",
    "mirrorgh": "https://mirror.ghproxy.com/",
}

# pip 镜像源
PIP_MIRRORS = {
    "清华": "https://pypi.tuna.tsinghua.edu.cn/simple/",
    "阿里云": "https://mirrors.aliyun.com/pypi/simple/",
    "华为云": "https://repo.huaweicloud.com/repository/pypi/simple/",
    "腾讯云": "https://mirrors.cloud.tencent.com/pypi/simple/",
    "中科大": "https://pypi.mirrors.ustc.edu.cn/simple/",
}

# npm 镜像源
NPM_MIRRORS = {
    "阿里云/npmmirror": "https://registry.npmmirror.com/",
    "腾讯云": "https://mirrors.cloud.tencent.com/npm/",
    "华为云": "https://mirrors.huaweicloud.com/repository/npm/",
}

# ========== 下载链接获取 ==========

def get_nodejs_download_url(version: str = "latest", os_type: str = None, arch: str = "x64") -> Optional[str]:
    """
    获取 Node.js 国内镜像下载地址
    """
    if os_type is None:
        os_type = detect_os()
    
    # 默认使用阿里云镜像
    base_url = NODE_MIRRORS["阿里云/npmmirror"]
    
    # 获取最新版本号
    if version == "latest":
        try:
            # 获取 index.json 获取最新版本
            index_url = base_url + "index.json"
            with urllib.request.urlopen(index_url, timeout=10) as response:
                data = json.loads(response.read().decode())
                version = data[0]["version"].lstrip('v')
        except:
            version = "20.18.0"  # LTS 默认版本
    
    # 构建文件名
    if os_type == "windows":
        filename = f"node-v{version}-{arch}.msi"
    elif os_type == "macos":
        filename = f"node-v{version}-darwin-{arch}.tar.gz"
    else:  # linux
        filename = f"node-v{version}-linux-{arch}.tar.xz"
    
    return base_url + f"v{version}/" + filename

def get_python_download_url(version: str = "3.12", os_type: str = None) -> Optional[str]:
    """
    获取 Python 国内镜像下载地址
    """
    if os_type is None:
        os_type = detect_os()
    
    # 默认使用华为云镜像
    base_url = PYTHON_MIRRORS["华为云"]
    
    if os_type == "windows":
        filename = f"python-{version}-amd64.exe"
        return base_url + f"{version}/" + filename
    elif os_type == "macos":
        filename = f"python-{version}-macos11.pkg"
        return base_url + f"{version}/" + filename
    else:
        filename = f"Python-{version}.tgz"
        return base_url + f"{version}/" + filename

def get_git_download_url(os_type: str = None) -> Optional[str]:
    """
    获取 Git 国内镜像下载地址
    """
    if os_type is None:
        os_type = detect_os()

    if os_type == "windows":
        # 尝试从华为云获取最新版本
        return "https://repo.huaweicloud.com/git-for-windows/v2.47.0.windows.1/Git-2.47.0-64-bit.exe"
    elif os_type == "macos":
        return "https://repo.huaweicloud.com/git-for-mac/git-latest.pkg"
    else:
        # Linux
        return "https://repo.huaweicloud.com/git/git-2.47.0.tar.gz"

def get_github_mirror_url(github_url: str, mirror: str = "kgithub") -> str:
    """
    将 GitHub URL 转换为国内镜像 URL
    """
    # 提取仓库路径
    if "github.com" in github_url:
        repo_path = github_url.split("github.com/")[-1].replace(".git", "")
    else:
        repo_path = github_url
    
    if mirror == "kgithub":
        return f"https://kgithub.com/{repo_path}"
    elif mirror == "gitclone":
        return f"https://gitclone.com/github.com/{repo_path}.git"
    elif mirror == "bgithub":
        return f"https://bgithub.xyz/{repo_path}"
    else:
        return github_url

# ========== 镜像源配置函数 ==========

def configure_pip_mirror(mirror: str = "清华") -> bool:
    """配置 pip 国内镜像"""
    mirror_url = PIP_MIRRORS.get(mirror, PIP_MIRRORS["清华"])
    try:
        subprocess.run(["pip", "config", "set", "global.index-url", mirror_url], 
                      capture_output=True, timeout=10)
        subprocess.run(["pip3", "config", "set", "global.index-url", mirror_url],
                      capture_output=True, timeout=10)
        return True
    except:
        return False

def configure_npm_mirror(mirror: str = "阿里云/npmmirror") -> bool:
    """配置 npm 国内镜像"""
    mirror_url = NPM_MIRRORS.get(mirror, NPM_MIRRORS["阿里云/npmmirror"])
    try:
        subprocess.run(["npm", "config", "set", "registry", mirror_url],
                      capture_output=True, timeout=10)
        return True
    except:
        return False

# ========== 辅助函数 ==========

def detect_os() -> str:
    """检测操作系统"""
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
    except:
        return False

def get_best_available_github_mirror() -> str:
    """获取当前可用的最佳 GitHub 镜像"""
    test_urls = {
        "kgithub": "https://kgithub.com/",
        "gitclone": "https://gitclone.com/",
        "ghproxy": "https://ghproxy.com/",
        "mirrorgh": "https://mirror.ghproxy.com/",
    }
    results = []
    import concurrent.futures
    import threading

    def check_mirror(name_url):
        name, url = name_url
        if test_mirror_availability(url):
            return name
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(check_mirror, item): item for item in test_urls.items()}
        for future in concurrent.futures.as_completed(futures, timeout=5):
            result = future.result()
            if result:
                return result

    return "kgithub"  # 默认

# ========== 安装指引生成 ==========

def generate_install_guide(tool: str, os_type: str = None) -> str:
    """生成安装指引（含国内镜像下载链接）"""
    if os_type is None:
        os_type = detect_os()
    
    guides = {
        "nodejs": {
            "windows": {
                "download": get_nodejs_download_url("latest", "windows"),
                "steps": [
                    "1. 下载安装包（国内镜像加速）",
                    "2. 双击运行安装程序",
                    "3. 勾选 'Automatically install necessary tools'",
                    "4. 完成安装后重启命令行"
                ]
            },
            "macos": {
                "download": get_nodejs_download_url("latest", "macos"),
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
                "download": get_python_download_url("3.12", "windows"),
                "steps": [
                    "1. 下载安装包（国内镜像加速）",
                    "2. 勾选 'Add Python to PATH'",
                    "3. 点击 Install Now",
                    "4. 完成安装"
                ]
            },
            "macos": {
                "download": get_python_download_url("3.12", "macos"),
                "steps": [
                    "1. 下载 pkg 安装包",
                    "2. 双击安装",
                    "3. 或使用 Homebrew: brew install python@3.12"
                ]
            }
        },
        "git": {
            "windows": {
                "download": get_git_download_url("windows"),
                "steps": [
                    "1. 下载 Git 安装包",
                    "2. 运行安装程序",
                    "3. 选择默认选项即可",
                    "4. 完成安装"
                ]
            }
        }
    }
    
    tool_guide = guides.get(tool, {})
    os_guide = tool_guide.get(os_type, {})
    
    lines = []
    lines.append(f"\n【{tool.upper()} 安装指引 - {os_type}】")
    
    if "download" in os_guide:
        lines.append(f"\n📥 国内镜像下载地址：")
        lines.append(f"   {os_guide['download']}")
    
    if "steps" in os_guide:
        lines.append("\n📋 安装步骤：")
        for step in os_guide["steps"]:
            lines.append(f"   {step}")
    
    return "\n".join(lines)

# ========== 命令行入口 ==========
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python installer.py <tool> [os]")
        print("  tool: nodejs, python, git")
        print("  os: windows, macos, linux")
        sys.exit(1)
    
    tool = sys.argv[1]
    os_type = sys.argv[2] if len(sys.argv) > 2 else None
    
    if tool == "nodejs":
        print(f"Node.js 国内镜像下载地址: {get_nodejs_download_url('latest', os_type)}")
    elif tool == "python":
        print(f"Python 国内镜像下载地址: {get_python_download_url('3.12', os_type)}")
    elif tool == "git":
        print(f"Git 国内镜像下载地址: {get_git_download_url(os_type)}")
    elif tool == "guide":
        for t in ["nodejs", "python", "git"]:
            print(generate_install_guide(t, os_type))
            print()
    elif tool == "mirrors":
        print("GitHub 镜像:", get_best_available_github_mirror())