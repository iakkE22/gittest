import os
import re
import json
import glob
import time
from openai import OpenAI
from tqdm import tqdm
import concurrent.futures
from pathlib import Path
import logging

# 设置日志B3B3
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# OpenAI客户端配置
client = OpenAI(
    api_key="0ff078a2-54d2-46e1-8a21-8fe612fb82a7", 
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    timeout=1800,
)

# API调用间隔（秒）
API_DELAY = 2

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

class DataCleaner:
    def __init__(self):
        self.client = client
        
    def call_llm(self, prompt, max_retries=3):
        """调用大模型接口"""
        for attempt in range(max_retries):
            try:
                # 添加请求间隔
                time.sleep(API_DELAY)
                
                response = self.client.chat.completions.create(
                    model="ep-20250411161304-4sdzf",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"API调用失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    raise e
                # 失败时增加更长的等待时间
                time.sleep(5 * (attempt + 1))
        return None
    
    def filter_scenic_content(self, text):
        """过滤非景点相关的文案"""
        prompt = FILTER_PROMPT.format(text=text[:2000])  # 限制长度避免token超限
        
        try:
            result = self.call_llm(prompt)
            return "是" in result
        except Exception as e:
            logger.error(f"过滤文案时出错: {str(e)}")
            return True  # 出错时默认保留
    
    def extract_keywords(self, text):
        """提取关键词信息"""
        prompt = EXTRACT_PROMPT.format(text=text[:2000])  # 限制长度
        
        try:
            result = self.call_llm(prompt)
            # 尝试解析JSON
            try:
                # 清理返回结果中的markdown标记
                clean_result = result.strip()
                if clean_result.startswith('```json'):
                    clean_result = clean_result[7:]  # 移除开头的```json
                if clean_result.endswith('```'):
                    clean_result = clean_result[:-3]  # 移除结尾的```
                clean_result = clean_result.strip()
                
                return json.loads(clean_result)
            except json.JSONDecodeError:
                # 如果不是标准JSON，尝试提取信息
                logger.warning("返回结果不是标准JSON格式，使用默认解析")
                logger.debug(f"原始结果: {result}")
                return self.parse_non_json_result(result, text)
                
        except Exception as e:
            logger.error(f"提取关键词时出错: {str(e)}")
            return self.get_default_keywords(text)
    
    def parse_non_json_result(self, result, original_text):
        """解析非JSON格式的结果"""
        return {
            "适用人群": "通用",
            "写作风格": "默认",
            "文案字数": len(original_text),
            "商户": "",
            "商品名称": "",
            "景点名称": [],
            "地点信息": [],
            "价格信息": [],
            "服务内容": [],
            "其他关键词": []
        }
    
    def get_default_keywords(self, text):
        """获取默认关键词信息"""
        return {
            "适用人群": "通用",
            "写作风格": "默认", 
            "文案字数": len(text),
            "商户": "",
            "商品名称": "",
            "景点名称": [],
            "地点信息": [],
            "价格信息": [],
            "服务内容": [],
            "其他关键词": []
        }
    
    def process_single_text(self, item):
        """处理单个文案"""
        try:
            text = item.get('text', '')
            if not text.strip():
                return None
                
            # 步骤1：过滤非景点文案
            if not self.filter_scenic_content(text):
                logger.info(f"文案ID {item.get('id', 'unknown')} 被过滤（非景点相关）")
                return None
            
            # 步骤2：提取关键词
            keywords = self.extract_keywords(text)
            
            # 合并原始数据和提取的关键词
            result = {
                'id': item.get('id'),
                'original_text': text,
                **keywords
            }
            
            logger.info(f"成功处理文案ID {item.get('id', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"处理文案ID {item.get('id', 'unknown')} 时出错: {str(e)}")
            return None
    
    def process_file(self, file_path, max_workers=1):  # 降低默认并发数
        """处理单个文件"""
        logger.info(f"开始处理文件: {file_path}")
        
        # 读取文件
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif file_path.endswith('.txt'):
                # 处理debug_post_*.txt文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 提取主要内容（跳过URL和标题行）
                    lines = content.split('\n')
                    text_lines = []
                    skip_next = False
                    for line in lines:
                        line = line.strip()
                        if line.startswith('URL:') or line.startswith('Title:') or line == '=' * 50:
                            skip_next = True
                            continue
                        if skip_next and line:
                            skip_next = False
                        if line and not skip_next:
                            text_lines.append(line)
                    
                    if text_lines:
                        data = [{'id': os.path.basename(file_path), 'text': '\n'.join(text_lines)}]
                    else:
                        return []
            else:
                logger.warning(f"不支持的文件格式: {file_path}")
                return []
                
        except Exception as e:
            logger.error(f"读取文件 {file_path} 时出错: {str(e)}")
            return []
        
        if not data:
            return []
        
        # 使用线程池处理文案（降低并发数）
        results = []
        if max_workers == 1:
            # 串行处理，避免API限制
            for item in tqdm(data, desc=f"处理 {os.path.basename(file_path)}"):
                try:
                    result = self.process_single_text(item)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.error(f"处理文案时出错: {str(e)}")
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(self.process_single_text, item) for item in data]
                
                for future in tqdm(concurrent.futures.as_completed(futures), 
                                 total=len(futures), 
                                 desc=f"处理 {os.path.basename(file_path)}"):
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                    except Exception as e:
                        logger.error(f"处理文案时出错: {str(e)}")
        
        logger.info(f"文件 {file_path} 处理完成，保留 {len(results)}/{len(data)} 条文案")
        return results
    
    def clean_all_data(self, data_dir="data", output_dir="cleaned_data", max_workers=1):  # 降低默认并发数
        """清洗所有数据"""
        logger.info("开始数据清洗...")
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取所有需要处理的文件
        json_files = glob.glob(os.path.join(data_dir, "**", "*.json"), recursive=True)
        txt_files = glob.glob(os.path.join(data_dir, "**", "debug_post_*.txt"), recursive=True)
        
        all_files = json_files + txt_files
        logger.info(f"找到 {len(all_files)} 个文件需要处理")
        
        # 按类别组织结果
        category_results = {}
        
        for file_path in all_files:
            # 确定类别
            relative_path = os.path.relpath(file_path, data_dir)
            category = relative_path.split(os.sep)[0] if os.sep in relative_path else "general"
            
            if category not in category_results:
                category_results[category] = []
            
            # 处理文件
            results = self.process_file(file_path, max_workers)
            category_results[category].extend(results)
        
        # 保存结果
        total_cleaned = 0
        for category, results in category_results.items():
            if results:
                output_file = os.path.join(output_dir, f"{category}_cleaned.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                logger.info(f"类别 {category}: 保存 {len(results)} 条清洗后的文案到 {output_file}")
                total_cleaned += len(results)
        
        # 生成总结报告
        summary = {
            "总处理文件数": len(all_files),
            "总清洗文案数": total_cleaned,
            "各类别统计": {category: len(results) for category, results in category_results.items()},
            "处理时间": "数据清洗完成"
        }
        
        summary_file = os.path.join(output_dir, "cleaning_summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据清洗完成！总共清洗 {total_cleaned} 条文案")
        logger.info(f"结果保存在 {output_dir} 目录")
        
        return category_results

def main():
    """主函数"""
    cleaner = DataCleaner()
    
    # 清洗所有数据（使用串行处理避免API限制）
    results = cleaner.clean_all_data(
        data_dir="data",
        output_dir="cleaned_data", 
        max_workers=1  # 串行处理，避免API频率限制
    )
    
    print("数据清洗完成！")
    for category, data in results.items():
        print(f"类别 {category}: {len(data)} 条文案")

if __name__ == "__main__":
    main() 