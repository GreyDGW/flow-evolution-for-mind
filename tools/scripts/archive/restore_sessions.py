import os
import shutil
import json

data_dir = 'tests/data'
state_file = '.collect_state.json'

# 1. 恢复 checkpoint 文件为原始文件名
print("=== Restoring checkpoint files ===")
restored = []
for filename in sorted(os.listdir(data_dir)):
    if '.checkpoint.' in filename:
        # 提取原始文件名
        original_name = filename.split('.checkpoint.')[0] + '.jsonl'
        src_path = os.path.join(data_dir, filename)
        dst_path = os.path.join(data_dir, original_name)
        if not os.path.exists(dst_path):
            shutil.copy2(src_path, dst_path)
            restored.append(original_name)
            print(f"  Restored: {filename} -> {original_name}")
print(f"\nTotal restored: {len(restored)} files")

# 2. 更新 .collect_state.json 包含这些原始文件
print("\n=== Updating .collect_state.json ===")
if os.path.exists(state_file):
    with open(state_file, 'r') as f:
        state = json.load(f)
    
    # 找出所有原始 jsonl 文件（没有后缀的）
    jsonl_files = [f for f in os.listdir(data_dir) 
                   if f.endswith('.jsonl') and 
                   not any(s in f for s in ['.checkpoint.', '.reset.', '.deleted.'])]
    
    for jsonl_file in jsonl_files:
        full_path = os.path.abspath(os.path.join(data_dir, jsonl_file))
        if full_path not in state:
            # 找一个对应的 checkpoint 记录来获取 lastLineOffset
            for checkpoint_file in os.listdir(data_dir):
                if jsonl_file.replace('.jsonl', '.checkpoint.') in checkpoint_file:
                    checkpoint_path = os.path.abspath(os.path.join(data_dir, checkpoint_file))
                    if checkpoint_path in state:
                        state[full_path] = state[checkpoint_path]
                        print(f"  Added to state: {jsonl_file}")
                        break
    
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
    print(f"Updated state file with {len(jsonl_files)} session files")

# 3. 列出所有原始 session 文件
print("\n=== Session files available ===")
jsonl_files = [f for f in os.listdir(data_dir) 
               if f.endswith('.jsonl') and 
               not any(s in f for s in ['.checkpoint.', '.reset.', '.deleted.'])]
for f in sorted(jsonl_files):
    size = os.path.getsize(os.path.join(data_dir, f))
    print(f"  - {f} ({size//1024} KB)")
print(f"\nTotal session files: {len(jsonl_files)}")
