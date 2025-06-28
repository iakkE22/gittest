import os
import json
import time
from openai import OpenAI
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# OpenAI客户端配置
client = OpenAI(
    api_key="0ff078a2-54d2-46e1-8a21-8fe612fb82a7", 
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    timeout=1800,
)

# API调用间隔（秒）
API_DELAY = 3

# 提示词模板
FILTER_PROMPT = '''
请判断以下文案是否是景点相关的宣传文案。

景点相关的文案包括：
- 旅游景点介绍和推荐
- 旅游攻略和路线分享  
- 旅游住宿和美食推荐
- 旅游体验和感受分享
- 景区门票、交通等信息

非景点相关的文案包括：
- 纯粹的生活分享（没有旅游内容）
- 商品广告（不是旅游相关）
- 情感抒发（不涉及具体景点）
- 纯理论或教程文章

文案内容：
{text}

请回答：是景点相关（回答"是"）或不是景点相关（回答"否"）
'''

EXTRACT_PROMPT = '''
请从以下景点宣传文案中提取关键信息，并按照指定格式返回JSON：

文案内容：
{text}

请提取以下信息：
1. 适用人群（从现有文案中识别：亲子家庭、情侣蜜月、商务出行、文化体验、户外运动、老年群体、学生群体等）
2. 写作风格（从以下选择：默认、诙谐幽默、犀利锐评、通俗易懂、专业写作、童趣）
3. 文案字数（直接统计字数）
4. 商品信息关键词（包括：商户名称、商品名称、景点名称、地点信息、价格信息、服务内容等，必须和文案内容完全一致，不能遗漏重要信息）

返回格式：
{{
    "适用人群": "xxx",
    "写作风格": "xxx", 
    "文案字数": 数字,
    "商户": "xxx（如果有）",
    "商品名称": "xxx（如果有）",
    "景点名称": ["景点1", "景点2"],
    "地点信息": ["地点1", "地点2"],
    "价格信息": ["价格1", "价格2"],
    "服务内容": ["服务1", "服务2"],
    "其他关键词": ["关键词1", "关键词2"]
}}

注意：所有信息必须从原文案中提取，不能添加文案中没有的内容。
'''

def call_llm(prompt, max_retries=3):
    """调用大模型接口"""
    for attempt in range(max_retries):
        try:
            logger.info(f"正在调用API (尝试 {attempt + 1}/{max_retries})...")
            
            # 添加请求间隔
            time.sleep(API_DELAY)
            
            response = client.chat.completions.create(
                model="ep-20250411161304-4sdzf",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            logger.info("API调用成功")
            return result
            
        except Exception as e:
            logger.warning(f"API调用失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                logger.error("所有重试都失败，跳过此条数据")
                return None
            # 失败时增加更长的等待时间
            wait_time = 10 * (attempt + 1)
            logger.info(f"等待 {wait_time} 秒后重试...")
            time.sleep(wait_time)
    return None

def test_single_text():
    """测试处理单条文案"""
    # 测试文案
    test_text = "这里是一个美丽的景点，适合情侣约会，门票价格50元，包含导游服务。"
    
    print("=== 测试单条文案处理 ===")
    print(f"测试文案: {test_text}")
    
    # 步骤1：过滤测试
    print("\n1. 过滤测试...")
    filter_prompt = FILTER_PROMPT.format(text=test_text)
    filter_result = call_llm(filter_prompt)
    
    if filter_result:
        print(f"过滤结果: {filter_result}")
        is_scenic = "是" in filter_result
        print(f"是否景点相关: {is_scenic}")
        
        if is_scenic:
            # 步骤2：关键词提取测试
            print("\n2. 关键词提取测试...")
            extract_prompt = EXTRACT_PROMPT.format(text=test_text)
            extract_result = call_llm(extract_prompt)
            
            if extract_result:
                print(f"提取结果: {extract_result}")
                
                try:
                    # 清理返回结果中的markdown标记
                    clean_result = extract_result.strip()
                    if clean_result.startswith('```json'):
                        clean_result = clean_result[7:]  # 移除开头的```json
                    if clean_result.endswith('```'):
                        clean_result = clean_result[:-3]  # 移除结尾的```
                    clean_result = clean_result.strip()
                    
                    keywords = json.loads(clean_result)
                    print("\n解析后的关键词:")
                    for key, value in keywords.items():
                        print(f"  {key}: {value}")
                except json.JSONDecodeError as e:
                    print(f"JSON解析失败: {e}")
                    print(f"原始结果: {extract_result}")
            else:
                print("关键词提取失败")
        else:
            print("文案被过滤（非景点相关）")
    else:
        print("过滤步骤失败")

def test_file_processing():
    """测试处理文件中的前几条数据"""
    print("\n=== 测试文件处理 ===")
    
    # 查找第一个JSON文件
    import glob
    json_files = glob.glob("data/**/*.json", recursive=True)
    
    if not json_files:
        print("未找到JSON文件")
        return
    
    test_file = json_files[0]
    print(f"测试文件: {test_file}")
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"文件包含 {len(data)} 条数据")
        
        # 只处理前3条数据
        test_data = data[:3]
        print(f"测试处理前 {len(test_data)} 条数据")
        
        results = []
        for i, item in enumerate(test_data):
            print(f"\n--- 处理第 {i+1} 条数据 ---")
            text = item.get('text', '')
            if not text.strip():
                print("文案为空，跳过")
                continue
            
            print(f"文案ID: {item.get('id')}")
            print(f"文案长度: {len(text)} 字符")
            print(f"文案预览: {text[:100]}...")
            
            # 过滤
            filter_prompt = FILTER_PROMPT.format(text=text[:1000])  # 限制长度
            filter_result = call_llm(filter_prompt)
            
            if not filter_result:
                print("过滤失败，跳过")
                continue
                
            is_scenic = "是" in filter_result
            print(f"过滤结果: {filter_result} -> {is_scenic}")
            
            if not is_scenic:
                print("非景点相关，被过滤")
                continue
            
            # 提取关键词
            extract_prompt = EXTRACT_PROMPT.format(text=text[:1000])
            extract_result = call_llm(extract_prompt)
            
            if not extract_result:
                print("关键词提取失败")
                continue
            
            try:
                 # 清理返回结果中的markdown标记
                 clean_result = extract_result.strip()
                 if clean_result.startswith('```json'):
                     clean_result = clean_result[7:]  # 移除开头的```json
                 if clean_result.endswith('```'):
                     clean_result = clean_result[:-3]  # 移除结尾的```
                 clean_result = clean_result.strip()
                 
                 keywords = json.loads(clean_result)
                 result = {
                     'id': item.get('id'),
                     'original_text': text,
                     **keywords
                 }
                 results.append(result)
                 print("处理成功")
             except json.JSONDecodeError as e:
                 print(f"关键词提取结果格式错误: {e}")
                 print(f"原始结果: {extract_result[:200]}...")
        
        print(f"\n=== 测试完成 ===")
        print(f"成功处理 {len(results)} 条数据")
        
        if results:
            # 保存测试结果
            os.makedirs("test_output", exist_ok=True)
            with open("test_output/test_results.json", 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print("测试结果已保存到 test_output/test_results.json")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")

def main():
    """主函数"""
    print("数据清洗脚本测试版")
    print("=" * 50)
    
    # 选择测试模式
    choice = input("\n请选择测试模式:\n1. 测试单条文案\n2. 测试文件处理\n请输入 1 或 2: ").strip()
    
    if choice == "1":
        test_single_text()
    elif choice == "2":
        test_file_processing()
    else:
        print("无效选择")

if __name__ == "__main__":
    main() 