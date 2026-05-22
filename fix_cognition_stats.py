import re

with open('plugin/deep_report_final.py', 'r') as f:
    code = f.read()

# 1. 检查 dim() 调用
dim_calls = re.findall(r"dim\('([^']+)'\)", code)
print(f"📋 当前 dim() 调用: {dim_calls}")

fixes = []

# 2. 如果缺少 dim('cognition_growth')，添加
if 'cognition_growth' not in dim_calls:
    if "fh,fm,fl = dim('flow_depth')" in code:
        code = code.replace(
            "fh,fm,fl = dim('flow_depth')",
            "fh,fm,fl = dim('flow_depth')\n        cogh,cogm,cogl = dim('cognition_growth')"
        )
        fixes.append("✅ 添加 dim('cognition_growth')")
    else:
        fixes.append("❌ 未找到 flow_depth 锚点")
else:
    fixes.append("✅ dim('cognition_growth') 已存在")

# 3. 如果缺少 cog_avg 计算，添加
if 'cog_avg' not in code:
    if "f_avg = self._avg" in code:
        code = code.replace(
            "f_avg = self._avg(s['fh'], s['fm'], s['fl'])",
            "f_avg = self._avg(s['fh'], s['fm'], s['fl'])\n        cog_avg = self._avg(s['cogh'], s['cogm'], s['cogl'])"
        )
        fixes.append("✅ 添加 cog_avg 计算")
    else:
        fixes.append("❌ 未找到 f_avg 锚点")
else:
    fixes.append("✅ cog_avg 已存在")

# 4. 如果缺少 cognition 模板替换，添加
if '{cogh}' not in code or '{cog_avg}' not in code:
    if 'r = r.replace("{f_avg}",' in code:
        code = code.replace(
            'r = r.replace("{f_avg}", f"{f_avg:.2f}"); r = r.replace("{f_star}", self._star(f_avg))',
            'r = r.replace("{f_avg}", f"{f_avg:.2f}"); r = r.replace("{f_star}", self._star(f_avg))\n        r = r.replace("{cogh}", str(s[\'cogh\'])); r = r.replace("{cogm}", str(s[\'cogm\'])); r = r.replace("{cogl}", str(s[\'cogl\']))\n        r = r.replace("{cog_avg}", f"{cog_avg:.2f}"); r = r.replace("{cog_star}", self._star(cog_avg))'
        )
        fixes.append("✅ 添加 cognition 模板替换")
    else:
        fixes.append("❌ 未找到 f_avg 替换锚点")
else:
    fixes.append("✅ cognition 模板替换已存在")

# 5. 确保 total_avg 计算包含 cog_avg
if 'total_avg' in code and 'cog_avg' in code:
    if 'f_avg)' in code and 'cog_avg)' not in code:
        code = code.replace(
            'round((g_avg + c_avg + f_avg) / 3, 2)',
            'round((g_avg + c_avg + f_avg + cog_avg) / 4, 2)'
        )
        fixes.append("✅ 修正 total_avg 为4维平均")
    elif '(g_avg + c_avg + f_avg + cog_avg)' in code:
        fixes.append("✅ total_avg 已含4维")
    else:
        fixes.append("⚠️ 请手动确认 total_avg 计算")

for f in fixes:
    print(f)

with open('plugin/deep_report_final.py', 'w') as f:
    f.write(code)

print("\n✅ 文件已保存")
