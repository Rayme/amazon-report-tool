#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Amazon Sales Report Analyzer - 启动器
在任何目录下运行此文件即可
"""

import os
import sys

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))

# 查找 amazon 目录（可能在脚本同目录、上级目录、或同级的amazon文件夹）
possible_paths = [
    script_dir,                      # 脚本同目录
    os.path.join(script_dir, '..'), # 上级目录
    os.path.join(script_dir, 'amazon'), # 脚本同目录的amazon
]

# 优先使用脚本同目录的amazon文件夹
amazon_path = None
for p in possible_paths:
    test_path = os.path.join(p, 'amazon')
    if os.path.isdir(test_path):
        amazon_path = p
        break

if amazon_path:
    os.chdir(amazon_path)

# 添加脚本目录到路径
sys.path.insert(0, script_dir)

# 运行主程序
from amazon_report_analyzer import main

if __name__ == "__main__":
    main()
