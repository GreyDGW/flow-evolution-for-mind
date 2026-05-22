#!/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin/.venv/bin/python3
"""生成指定日期的 Flow 报告"""

import os
import sys
import subprocess

# 自动检测并激活项目 .venv（确保依赖可用）
_VENV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv')
_VENV_PYTHON = os.path.join(_VENV_DIR, 'bin', 'python3')

# 如果当前 Python 不是 .venv 的 Python，且 .venv 存在，则重新调用
if os.path.exists(_VENV_PYTHON) and sys.executable != _VENV_PYTHON:
    print(f"🔄 检测到项目 .venv，切换到: {_VENV_PYTHON}")
    result = subprocess.run([_VENV_PYTHON, __file__] + sys.argv[1:], env=os.environ)
    sys.exit(result.returncode)

print(f"✅ 使用 Python: {sys.executable}")
print(f"✅ 工作目录: {os.getcwd()}")

from plugin.report_assembler import ReportAssembler

def main():
    assembler = ReportAssembler()

    # 生成 4月21日的报告
    print("📊 正在生成 4月21日 Flow 报告...")
    report = assembler.generate_flow_report(
        session_limit=50,
        trend_limit=30,
        start='2026-04-21 00:00:00',
        end='2026-04-21 23:59:59'
    )

    print("\n" + "=" * 60)
    print("📅 4月20日 Flow 报告")
    print("=" * 60)
    print(report)
    print("=" * 60)


if __name__ == '__main__':
    main()
