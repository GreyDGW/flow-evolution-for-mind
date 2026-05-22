#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化 batch_session_cutter.py 的模型加载性能
- batch_cut() 增加 embedder 参数（可选，兼容旧调用）
- batch_cut_by_date() 提前创建 embedder，传入循环
"""

path = 'batch_session_cutter.py'
with open(path, 'r') as f:
    content = f.read()

# 修改 1: batch_cut 函数签名增加 embedder 参数
old_batch_cut_def = 'def batch_cut(session_id: str, db_path: str = \'data/flow_ecosystem.db\'):'
new_batch_cut_def = 'def batch_cut(session_id: str, db_path: str = \'data/flow_ecosystem.db\', embedder=None):'

if old_batch_cut_def in content:
    content = content.replace(old_batch_cut_def, new_batch_cut_def)
    print("✅ 修改 1/3: batch_cut 增加 embedder 参数")
else:
    print("⚠️ 修改 1: 未找到 batch_cut 定义")

# 修改 2: batch_cut 内部，如果 embedder 已传入则跳过创建
old_embedder_create = '''    try:
        from plugin.session.embedding import create_embedder
        embedder = create_embedder()
        print("  ✅ 嵌入模型已加载（VectorLayer 可用）")
    except Exception as e:
        embedder = None
        print(f"  ⚠️ 嵌入模型未加载（VectorLayer 降级为硬规则）: {e}")'''

new_embedder_create = '''    if embedder is None:
        try:
            from plugin.session.embedding import create_embedder
            embedder = create_embedder()
            print("  ✅ 嵌入模型已加载（VectorLayer 可用）")
        except Exception as e:
            embedder = None
            print(f"  ⚠️ 嵌入模型未加载（VectorLayer 降级为硬规则）: {e}")
    else:
        print("  ✅ 使用传入的嵌入模型（全局复用）")'''

if old_embedder_create in content:
    content = content.replace(old_embedder_create, new_embedder_create)
    print("✅ 修改 2/3: batch_cut 内部支持传入 embedder")
else:
    print("⚠️ 修改 2: 未找到 embedder 创建代码")

# 修改 3: batch_cut_by_date 提前创建 embedder，传入循环
old_by_date_loop = '''    for sid in sessions:
        print(f"\\n  [{i}/{len(sessions)}] 切割 {sid}...")
        segs = batch_cut(sid, db_path)'''

new_by_date_loop = '''    # 提前创建 embedder，所有 session 复用（避免重复加载模型）
    from plugin.session.embedding import create_embedder
    try:
        shared_embedder = create_embedder()
        print(f"  ✅ 嵌入模型已全局加载（将被 {len(sessions)} 个 session 复用）")
    except Exception as e:
        shared_embedder = None
        print(f"  ⚠️ 嵌入模型未加载（VectorLayer 降级为硬规则）: {e}")
    
    for sid in sessions:
        print(f"\\n  [{i}/{len(sessions)}] 切割 {sid}...")
        segs = batch_cut(sid, db_path, embedder=shared_embedder)'''

if old_by_date_loop in content:
    content = content.replace(old_by_date_loop, new_by_date_loop)
    print("✅ 修改 3/3: batch_cut_by_date 提前创建 embedder 并复用")
else:
    print("⚠️ 修改 3: 未找到 batch_cut_by_date 循环")

with open(path, 'w') as f:
    f.write(content)

print("✅ 文件已保存")
