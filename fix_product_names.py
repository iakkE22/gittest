#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os

def read_original_file(file_path):
    """读取原始txt文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except:
        return ""

def extract_product_name_from_content(content, file_id):
    """根据内容提取商品名称"""
    content_lower = content.lower()
    
    # 根据文件内容特征提取商品名称
    if "多玛乐园" in content:
        return "多玛乐园水上度假套餐"
    elif "三亚" in content and "度假" in content:
        return "三亚情侣度假套餐"
    elif "巴厘岛" in content and "旅游" in content:
        return "巴厘岛6天5晚情侣旅游套餐"
    elif "求推荐" in content and "情侣" in content:
        return "情侣旅游咨询服务"
    elif "寻找旅游搭子" in content:
        return "旅游搭子服务"
    elif "毕业旅行" in content:
        return "毕业旅行攻略"
    elif "避暑" in content and "马尔代夫" in content:
        return "避暑度假套餐"
    elif "情侣旅游" in content or "情侣出游" in content:
        return "情侣旅游套餐"
    elif "旅游攻略" in content:
        return "旅游攻略服务"
    elif "度假酒店" in content:
        return "度假酒店套餐"
    elif "民宿" in content:
        return "民宿预订服务"
    elif "酒店" in content:
        return "酒店预订服务"
    elif "机票" in content:
        return "机票预订服务"
    elif "包车" in content:
        return "包车旅游服务"
    elif "门票" in content:
        return "景点门票"
    elif "自由行" in content:
        return "自由行套餐"
    elif "跟团" in content:
        return "跟团旅游套餐"
    else:
        # 如果没有明确的商品信息，根据标题或内容关键词生成
        if "攻略" in content:
            return "旅游攻略"
        elif "推荐" in content:
            return "旅游推荐服务"
        else:
            return "旅游服务"

def main():
    # 读取清洗后的JSON文件
    with open('cleaned_data/couples_cleaned.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    updated_count = 0
    
    for item in data:
        if item.get("商品名称") == "":
            file_id = item["id"]
            original_file_path = f"data/couples/{file_id}"
            
            # 读取原始文件内容
            original_content = read_original_file(original_file_path)
            
            if original_content:
                # 从原始内容中提取商品名称
                product_name = extract_product_name_from_content(original_content, file_id)
                item["商品名称"] = product_name
                updated_count += 1
                print(f"更新 {file_id}: {product_name}")
            else:
                # 如果无法读取原始文件，从已清洗的内容中提取
                product_name = extract_product_name_from_content(item["original_text"], file_id)
                item["商品名称"] = product_name
                updated_count += 1
                print(f"从清洗文本更新 {file_id}: {product_name}")
    
    # 保存更新后的文件
    with open('cleaned_data/couples_cleaned.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n总共更新了 {updated_count} 个商品名称")

if __name__ == "__main__":
    main() 