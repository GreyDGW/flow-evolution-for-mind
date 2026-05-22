import sys
sys.path.insert(0, "/Users/duguowei/Desktop/skill相关文档/openclaw_flow_plugin")

def run_regression():
    from plugin.report_assembler import ReportAssembler
    asm = ReportAssembler()
    errors = []
    
    print("=" * 70)
    print("🧪 Flow Ecosystem 回归测试（带重试）")
    print("=" * 70)
    
    def check(name, date):
        print(f"\n【{name}】")
        print("-" * 70)
        report = asm.generate_flow_report(start=f"{date} 00:00:00", end=f"{date} 23:59:59")
        
        if len(report) < 100:
            print(f"  ❌ 报告异常短: {len(report)}字符")
            return False
        
        checks = [
            ("日期正确", "2026-" + date[5:] in report),
            ("核心状态存在", "核心状态：" in report),
            ("表格4列", "趋势分布" in report),
            ("累计时长", "累计" in report and "小时" in report),
            ("无数据不足", "数据不足" not in report),
            ("引语有内容", ">" in report and len(report.split(">")[1].split("\n")[0]) > 5),
            ("场景>=2", report.count("• ") >= 2),
            ("👉建议有内容", "👉 建议" in report),
            ("📋整体建议", "📋 整体建议" in report),
            ("破局指南", "💡 破局指南" in report),
            ("收益时间", "时间维度：" in report),
            ("收益价值", "价值维度：" in report),
            ("行动", "最大回报：" in report),
        ]
        
        failed = []
        for k, v in checks:
            status = "✅" if v else "❌"
            if not v:
                failed.append(k)
                errors.append(f"{name}: {k}")
            print(f"  {status} {k}")
        
        return len(failed) == 0
    
    check("4月20日", "2026-04-20")
    check("4月21日", "2026-04-21")
    
    print("\n" + "=" * 70)
    if not errors:
        print("🎉 全部测试通过")
    else:
        unique = list(set(errors))
        print(f"⚠️ {len(unique)} 项失败:")
        for e in unique:
            print(f"  ❌ {e}")
    print("=" * 70)
    
    return len(errors) == 0

if __name__ == "__main__":
    success = run_regression()
    sys.exit(0 if success else 1)