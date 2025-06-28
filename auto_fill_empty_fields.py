#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
from openai import OpenAI
from tqdm import tqdm
import concurrent.futures
import time

# 配置API客户端
client = OpenAI(
    api_key="0ff078a2-54d2-46e1-8a21-8fe612fb82a7", 
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    timeout=1800,
)

def read_original_file(file_path):
    """读取原始文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"读取文件失败 {file_path}: {e}")
        return None

def clean_json_response(response_text):
    """清理API返回的JSON字符串"""
    # 移除markdown代码块标记
    response_text = re.sub(r'```json\s*', '', response_text)
    response_text = re.sub(r'```\s*$', '', response_text)
    response_text = response_text.strip()
    return response_text

def fill_with_defaults(current_data, empty_fields):
    """使用默认值填补空字段"""
    filled_data = current_data.copy()
    
    for field in empty_fields:
        if field == "适用人群":
            filled_data["适用人群"] = "通用"
        elif field == "写作风格":
            filled_data["写作风格"] = "通俗易懂"
        elif field == "商户":
            filled_data["商户"] = "旅游服务商"
        elif field == "商品名称":
            filled_data["商品名称"] = "旅游套餐"
        elif field == "景点名称":
            filled_data["景点名称"] = ["待补充"]
        elif field == "地点信息":
            filled_data["地点信息"] = ["待补充"]
        elif field == "价格信息":
            filled_data["价格信息"] = []  # 价格信息可以为空
        elif field == "服务内容":
            filled_data["服务内容"] = ["旅游服务"]
        elif field == "其他关键词":
            filled_data["其他关键词"] = ["旅游", "体验"]
    
    return filled_data

def fill_empty_fields_with_ai(original_text, current_data):
    """使用AI填补空缺字段"""
    
    # 检查哪些字段需要填补
    empty_fields = []
    
    # 更严格的空值检查
    if (not current_data.get("适用人群") or 
        current_data.get("适用人群") == "" or 
        current_data.get("适用人群") == "通用" or
        isinstance(current_data.get("适用人群"), list) and len(current_data.get("适用人群")) == 0):
        empty_fields.append("适用人群")
        
    if (not current_data.get("写作风格") or 
        current_data.get("写作风格") == "" or 
        current_data.get("写作风格") == "默认"):
        empty_fields.append("写作风格")
        
    if (not current_data.get("商户") or 
        current_data.get("商户") == ""):
        empty_fields.append("商户")
        
    if (not current_data.get("商品名称") or 
        current_data.get("商品名称") == ""):
        empty_fields.append("商品名称")
        
    if (not current_data.get("景点名称") or 
        len(current_data.get("景点名称", [])) == 0):
        empty_fields.append("景点名称")
        
    if (not current_data.get("地点信息") or 
        len(current_data.get("地点信息", [])) == 0):
        empty_fields.append("地点信息")
        
    if (not current_data.get("价格信息") or 
        len(current_data.get("价格信息", [])) == 0):
        empty_fields.append("价格信息")
        
    if (not current_data.get("服务内容") or 
        len(current_data.get("服务内容", [])) == 0):
        empty_fields.append("服务内容")
        
    if (not current_data.get("其他关键词") or 
        len(current_data.get("其他关键词", [])) == 0):
        empty_fields.append("其他关键词")
    
    # 如果没有空字段，仍然检查是否需要优化现有内容
    if not empty_fields:
        # 检查是否有明显需要改进的字段
        needs_improvement = False
        if current_data.get("适用人群") == "通用":
            needs_improvement = True
        if current_data.get("写作风格") == "默认":
            needs_improvement = True
        
        if not needs_improvement:
            return current_data
        else:
            empty_fields = ["适用人群", "写作风格"]  # 至少改进这两个字段
    
    prompt = f"""
请根据以下小红书旅游文案内容，填补缺失的字段信息。请仔细阅读文案内容，准确提取相关信息。

原始文案内容：
{original_text}

当前已有数据：
{json.dumps(current_data, ensure_ascii=False, indent=2)}

需要填补的字段：{', '.join(empty_fields)}

请按照以下要求填补信息：

1. **适用人群**：根据文案内容判断主要面向的人群（如：亲子家庭、情侣蜜月、学生群体、年轻群体、老年群体、通用等）

2. **写作风格**：分析文案的写作风格（如：默认、诙谐幽默、犀利锐评、通俗易懂、专业写作、童趣、浪漫抒情等）

3. **商户**：提取文案中提到的商家、机构、景区名称等

4. **商品名称**：根据文案内容推断合适的旅游产品名称

5. **景点名称**：提取文案中提到的所有景点、地标、建筑等名称

6. **地点信息**：提取具体的地理位置信息（城市、区域、地址等）

7. **价格信息**：提取文案中提到的所有价格、费用信息

8. **服务内容**：提取文案中提到的各种服务、活动、体验项目等

9. **其他关键词**：提取文案中的重要关键词、特色词汇、标签等

请返回完整的JSON格式数据，包含所有原有字段和新填补的字段。确保JSON格式正确，所有字符串使用双引号。

返回格式：
{{
    "id": "{current_data.get('id')}",
    "original_text": "...",
    "适用人群": "...",
    "写作风格": "...",
    "文案字数": {current_data.get('文案字数', 0)},
    "商户": "...",
    "商品名称": "...",
    "景点名称": [...],
    "地点信息": [...],
    "价格信息": [...],
    "服务内容": [...],
    "其他关键词": [...]
}}
"""

    try:
        response = client.chat.completions.create(
            model="ep-20250411161304-4sdzf",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        response_text = response.choices[0].message.content
        response_text = clean_json_response(response_text)
        
        # 解析JSON响应
        filled_data = json.loads(response_text)
        
        # 验证是否真的填补了空字段
        validation_failed = False
        for field in empty_fields:
            if field == "适用人群":
                if not filled_data.get("适用人群") or filled_data.get("适用人群") == "":
                    validation_failed = True
                    break
            elif field == "写作风格":
                if not filled_data.get("写作风格") or filled_data.get("写作风格") == "":
                    validation_failed = True
                    break
            elif field == "商户":
                if not filled_data.get("商户") or filled_data.get("商户") == "":
                    validation_failed = True
                    break
            elif field == "商品名称":
                if not filled_data.get("商品名称") or filled_data.get("商品名称") == "":
                    validation_failed = True
                    break
            elif field in ["景点名称", "地点信息", "价格信息", "服务内容", "其他关键词"]:
                if not filled_data.get(field) or len(filled_data.get(field, [])) == 0:
                    validation_failed = True
                    break
        
        if validation_failed:
            print(f"AI填补验证失败，某些字段仍为空: {empty_fields}")
            # 对于验证失败的情况，手动设置默认值
            for field in empty_fields:
                if field == "适用人群" and (not filled_data.get("适用人群") or filled_data.get("适用人群") == ""):
                    filled_data["适用人群"] = "通用"
                elif field == "写作风格" and (not filled_data.get("写作风格") or filled_data.get("写作风格") == ""):
                    filled_data["写作风格"] = "通俗易懂"
                elif field == "商户" and (not filled_data.get("商户") or filled_data.get("商户") == ""):
                    filled_data["商户"] = "旅游服务商"
                elif field == "商品名称" and (not filled_data.get("商品名称") or filled_data.get("商品名称") == ""):
                    filled_data["商品名称"] = "旅游套餐"
                elif field in ["景点名称", "地点信息", "价格信息", "服务内容", "其他关键词"]:
                    if not filled_data.get(field) or len(filled_data.get(field, [])) == 0:
                        filled_data[field] = ["待补充"]
        
        return filled_data
        
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        print(f"原始响应: {response_text}")
        # 返回带有默认值的数据，确保不留空
        return fill_with_defaults(current_data, empty_fields)
    except Exception as e:
        print(f"API调用错误: {e}")
        return fill_with_defaults(current_data, empty_fields)

def process_json_file(json_file_path, data_folder_path):
    """处理单个JSON文件"""
    print(f"\n开始处理: {json_file_path}")
    
    # 读取JSON文件
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 统计需要处理的项目
    total_items = len(data)
    processed_items = 0
    updated_items = 0
    
    # 逐个处理每个项目
    for i, item in enumerate(tqdm(data, desc=f"处理 {os.path.basename(json_file_path)}")):
        try:
            # 获取原始文件路径
            file_id = item.get('id', '')
            if not file_id:
                continue
                
            original_file_path = os.path.join(data_folder_path, file_id)
            
            # 读取原始文件
            original_content = read_original_file(original_file_path)
            if not original_content:
                continue
            
            # 使用AI填补空缺字段
            filled_item = fill_empty_fields_with_ai(original_content, item)
            
            # 检查是否有更新
            if filled_item != item:
                data[i] = filled_item
                updated_items += 1
                print(f"已更新: {file_id}")
            
            processed_items += 1
            
            # 添加延时避免API限制
            time.sleep(2)
            
        except Exception as e:
            print(f"处理项目失败 {item.get('id', 'unknown')}: {e}")
            continue
    
    # 保存更新后的文件
    if updated_items > 0:
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"已保存更新: {json_file_path}")
        print(f"总项目: {total_items}, 处理: {processed_items}, 更新: {updated_items}")
    else:
        print(f"无需更新: {json_file_path}")

def check_empty_fields(json_file_path):
    """检查文件中有多少空缺字段"""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_items = len(data)
    empty_count = {
        "适用人群": 0,
        "写作风格": 0,
        "商户": 0,
        "商品名称": 0,
        "景点名称": 0,
        "地点信息": 0,
        "价格信息": 0,
        "服务内容": 0,
        "其他关键词": 0
    }
    
    for item in data:
        if (not item.get("适用人群") or 
            item.get("适用人群") == "" or 
            item.get("适用人群") == "通用" or
            isinstance(item.get("适用人群"), list) and len(item.get("适用人群")) == 0):
            empty_count["适用人群"] += 1
            
        if (not item.get("写作风格") or 
            item.get("写作风格") == "" or 
            item.get("写作风格") == "默认"):
            empty_count["写作风格"] += 1
            
        if (not item.get("商户") or 
            item.get("商户") == ""):
            empty_count["商户"] += 1
            
        if (not item.get("商品名称") or 
            item.get("商品名称") == ""):
            empty_count["商品名称"] += 1
            
        if (not item.get("景点名称") or 
            len(item.get("景点名称", [])) == 0):
            empty_count["景点名称"] += 1
            
        if (not item.get("地点信息") or 
            len(item.get("地点信息", [])) == 0):
            empty_count["地点信息"] += 1
            
        if (not item.get("价格信息") or 
            len(item.get("价格信息", [])) == 0):
            empty_count["价格信息"] += 1
            
        if (not item.get("服务内容") or 
            len(item.get("服务内容", [])) == 0):
            empty_count["服务内容"] += 1
            
        if (not item.get("其他关键词") or 
            len(item.get("其他关键词", [])) == 0):
            empty_count["其他关键词"] += 1
    
    print(f"\n{os.path.basename(json_file_path)} 空缺统计 (总计 {total_items} 项):")
    for field, count in empty_count.items():
        if count > 0:
            print(f"  {field}: {count} 项空缺")
    
    return empty_count

def main():
    """主函数"""
    # 定义要处理的文件
    files_to_process = [
        ("cleaned_data/cultural_cleaned.json", "data/cultural"),
        ("cleaned_data/family_cleaned.json", "data/family"),
        ("cleaned_data/olds_cleaned.json", "data/olds"),
        ("cleaned_data/outdoors_cleaned.json", "data/outdoors"),
        ("cleaned_data/students_cleaned.json", "data/students")
    ]
    
    print("=== 首先检查空缺字段统计 ===")
    for json_file, data_folder in files_to_process:
        if os.path.exists(json_file):
            check_empty_fields(json_file)
    
    print("\n=== 开始自动填补空缺字段 ===")
    
    for json_file, data_folder in files_to_process:
        if os.path.exists(json_file) and os.path.exists(data_folder):
            process_json_file(json_file, data_folder)
        else:
            print(f"文件或文件夹不存在: {json_file} 或 {data_folder}")
    
    print("\n=== 填补完成后再次检查 ===")
    for json_file, data_folder in files_to_process:
        if os.path.exists(json_file):
            check_empty_fields(json_file)
    
    print("\n所有文件处理完成！")

if __name__ == "__main__":
    main() 