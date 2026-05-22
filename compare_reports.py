#!/usr/bin/env python3
"""对比 4月20日 和 4月21日的报告"""

import sys
sys.path.insert(0, '.')

from plugin.report_assembler import ReportAssembler

def main():
    assembler = ReportAssembler()

    # 生成 4月20日的报告
    print("=" * 70)
    print("📅 4月20日 Flow 报告")
    print("=" * 70)
    report_20 = assembler.generate_flow_report(
        session_limit=50,
        trend_limit=30,
        start='2026-04-20 00:00:00',
        end='2026-04-20 23:59:59'
    )
    print(report_20)

    print("\n" + "=" * 70)
    print("📅 4月21日 Flow 报告")
    print("=" * 70)
    report_21 = assembler.generate_flow_report(
        session_limit=50,
        trend_limit=30,
        start='2026-04-21 00:00:00',
        end='2026-04-21 23:59:59'
    )
    print(report_21)


if __name__ == '__main__':
    main()
