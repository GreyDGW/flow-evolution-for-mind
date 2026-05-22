"""
项目路径初始化模块。
所有测试脚本和入口文件应在首行 import path_setup
"""
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)