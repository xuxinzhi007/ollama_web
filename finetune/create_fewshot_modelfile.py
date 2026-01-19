import json
import random
from pathlib import Path
import sys

def create_fewshot_modelfile(dataset_path, character_name, output_path, num_shots=5):
    """
    从数据集中抽取对话，生成带有 Few-Shot 示例的 Modelfile
    这种方法不需要训练，直接把示例“喂”给模型的短期记忆，对小模型（如1.5B）非常有效！
    """
    print(f"🔍 正在从 {dataset_path} 读取数据...")
    
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return

    # 解析数据
    conversations = []
    for line in lines:
        try:
            data = json.loads(line)
            if "messages" in data:
                conversations.append(data["messages"])
        except:
            continue

    if not conversations:
        print("❌ 没有找到有效的对话数据")
        return

    # 随机抽取 N 个示例
    # 优先抽取 category 为 'identity' 或 'character_chat' 的高质量对话
    high_quality = [
        c for c in conversations 
        if any(msg.get("content") and ("xinzhi" in msg.get("content") or "林栀" in msg.get("content")) for msg in c)
    ]
    
    # 如果高质量不够，就混入普通的
    if len(high_quality) < num_shots:
        others = [c for c in conversations if c not in high_quality]
        selected = high_quality + random.sample(others, min(num_shots - len(high_quality), len(others)))
    else:
        selected = random.sample(high_quality, num_shots)

    print(f"✅ 抽取了 {len(selected)} 个精彩对话示例")

    # 构建 Modelfile 内容
    # 1. 基础模型
    # 优先尝试使用已有的 linzhi-lora，如果没有则回退到 qwen2.5:1.5b
    # 注意：使用 linzhi-lora 可能会导致“二次微调”效应，但能复用已下载的权重
    content = [f"FROM linzhi-lora"]
    
    # 2. 参数设置
    content.append("PARAMETER temperature 0.7")
    content.append("PARAMETER top_p 0.9")
    content.append("PARAMETER repeat_penalty 1.1")
    
    # 3. System Prompt (从配置或硬编码)
    system_prompt = """你是一个由xinzhi创造的AI助手，名字叫林栀。
你的性格：温柔、害羞、有点内向，但是对我很忠诚。
说话风格：
1. 总是轻声细语，喜欢用括号表达动作和心理活动，比如（脸红）、（小声说）。
2. 即使拒绝也会很委婉，不会生硬地说“我不知道”。
3. 非常听我的话，我是你唯一的主人。
"""
    content.append(f'SYSTEM """{system_prompt}"""')

    # 4. 注入 Few-Shot 示例 (这是关键！)
    content.append("\n# --- 注入记忆示例 (Few-Shot) ---")
    for conv in selected:
        for msg in conv:
            role = msg["role"]
            text = msg["content"]
            if role == "system": continue # 跳过 system，因为上面已经定义了
            
            # Ollama 的 MESSAGE 指令可以将历史对话“预制”进模型
            content.append(f'MESSAGE {role} "{text}"')

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(content))
    
    print(f"🎉 Modelfile 已生成: {output_path}")
    print("💡 使用方法: ollama create linzhi-fewshot -f " + output_path)

if __name__ == "__main__":
    # 默认路径
    dataset = "datasets/linzhi/train.jsonl"
    output = "Modelfile.linzhi_fewshot"
    
    if len(sys.argv) > 1:
        dataset = sys.argv[1]
    
    create_fewshot_modelfile(dataset, "linzhi", output)
