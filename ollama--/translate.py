
import pprint
import json

import ollama

def translate_text(text, target_lang="English", source_lang="Chinese"):
    """
    使用 Ollama 本地模型进行翻译
    
    参数:
        text (str): 需要翻译的文本
        target_lang (str): 目标语言 (默认: English)
        source_lang (str): 源语言 (默认: Chinese)
    
    返回:
        str: 翻译后的结果
    """
    
    # 构建提示词 (Prompt Engineering)
    # 对于翻译任务，清晰的指令非常重要
    system_prompt = f"""You are a professional translator. 
    Translate the following text from {source_lang} to {target_lang}. 
    Do not output any explanation, just the translation."""
    
    user_message = text

    client = ollama.Client(host="http://10.1.3.20:11434")

    try:
        # 调用 Ollama Chat API
        # model: 替换为你实际使用的模型名称，例如 'translategemma:12b', 'llama3:8b', 'qwen2:7b'
        model_name = "translategemma:12b" 
        
        print(f"🔄 正在使用模型 '{model_name}' 进行翻译...")
        
        #response = ollama.chat(
        response = client.chat(
            model=model_name,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message},
            ],
            options={
                'temperature': 0.3,  # 翻译任务通常不需要太高的创造性，设低一点更准确
                'top_p': 0.9,
            }
        )
        
        #pprint.pprint(response.model_dump())
        print(f"输入token: {response.prompt_eval_count} 输出token: {response.eval_count} 总数: {response.prompt_eval_count + response.eval_count}")
        # 提取回复内容
        translated_text = response['message']['content']
        return translated_text.strip()

    except Exception as e:
        return f"❌ 发生错误: {str(e)}\n请检查 Ollama 服务是否运行，以及模型名称是否正确。"

# --- 主程序入口 ---
if __name__ == "__main__":
    # 示例文本
    original_text = "Ollama 是一个让本地运行大语言模型变得非常简单的工具。它支持多种模型，并且可以通过 Python 轻松调用。"
    
    print("📝 原文:")
    print(original_text)
    print("-" * 30)
    
    # 执行翻译 (中文 -> 英文)
    result = translate_text(original_text, target_lang="English", source_lang="Chinese")
    
    print("🌍 译文 (English):")
    print(result)
    print("-" * 30)

    # 你也可以尝试反向翻译 (英文 -> 中文)
    english_text = "Artificial Intelligence is transforming the world."
    result_cn = translate_text(english_text, target_lang="Chinese", source_lang="English")
    print("🇨🇳 译文 (Chinese):", result_cn)
