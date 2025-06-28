#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
适应小红书单页帖子限制的爬取策略
基于发现小红书搜索页面只显示固定数量帖子的事实
"""

from xiaohongshu_crawler import XiaohongshuCrawler
import time

class LimitedPostsStrategy:
    def __init__(self):
        self.crawler = XiaohongshuCrawler(headless=False, wait_login=True)
    
    def get_posts_with_multiple_strategies(self, base_keyword, target_count=100):
        """使用多种策略获取更多帖子"""
        print(f"=== 目标: 获取 {target_count} 个关于 '{base_keyword}' 的帖子 ===")
        
        all_texts = []
        processed_urls = set()  # 避免重复
        
        # 策略1: 使用相关关键词
        related_keywords = self.generate_related_keywords(base_keyword)
        
        for keyword in related_keywords:
            if len(all_texts) >= target_count:
                break
                
            print(f"\n--- 搜索关键词: '{keyword}' ---")
            try:
                # 每个关键词获取所有可用帖子（大约28个）
                keyword_texts = self.crawler.search_by_keyword(keyword, 50)  # 设置50，实际可能只得到28个
                
                # 去重处理
                new_texts = []
                for text in keyword_texts:
                    # 简单的去重：检查文本前100字符
                    text_hash = text[:100] if text else ""
                    if text_hash not in processed_urls and text.strip():
                        processed_urls.add(text_hash)
                        new_texts.append(text)
                        all_texts.append(text)
                
                print(f"✓ 从 '{keyword}' 获取到 {len(new_texts)} 个新帖子 (总计: {len(all_texts)})")
                
                # 短暂休息避免被限制
                time.sleep(2)
                
            except Exception as e:
                print(f"✗ 关键词 '{keyword}' 失败: {str(e)}")
                continue
        
        # 保存结果
        self.save_combined_results(base_keyword, all_texts)
        
        print(f"\n=== 完成! 总共获取 {len(all_texts)} 个帖子 ===")
        return all_texts
    
    def generate_related_keywords(self, base_keyword):
        """生成相关关键词"""
        print(f"生成 '{base_keyword}' 的相关关键词...")
        
        # 根据不同的基础关键词生成相关搜索词
        keyword_variants = {
            "亲子旅游": [
                "亲子旅游",
                "亲子游", 
                "家庭旅游",
                "带娃旅行",
                "亲子出游",
                "一家人旅行",
                "儿童旅游",
                "亲子度假",
                "家庭出行",
                "亲子自驾游"
            ],
            "潜水": [
                "潜水",
                "自由潜水",
                "深潜",
                "水肺潜水",
                "潜水旅游",
                "潜水装备",
                "潜水胜地",
                "海底世界",
                "潜水体验",
                "潜水教学"
            ],
            "美食": [
                "美食",
                "美食推荐", 
                "好吃的",
                "餐厅推荐",
                "小吃",
                "网红美食",
                "美食攻略",
                "地方美食",
                "美食探店",
                "家常菜"
            ]
        }
        
        # 查找匹配的关键词组
        for key, variants in keyword_variants.items():
            if key in base_keyword or base_keyword in key:
                print(f"找到匹配组: {variants}")
                return variants
        
        # 如果没有预定义的，生成通用变体
        generic_variants = [
            base_keyword,
            f"{base_keyword}推荐",
            f"{base_keyword}攻略", 
            f"{base_keyword}分享",
            f"{base_keyword}体验"
        ]
        
        print(f"使用通用变体: {generic_variants}")
        return generic_variants
    
    def save_combined_results(self, base_keyword, all_texts):
        """保存合并的结果"""
        if not all_texts:
            return
            
        import os
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 保存文本文件
        txt_filename = f"{output_dir}/{base_keyword}_多策略合集_texts.txt"
        with open(txt_filename, 'w', encoding='utf-8') as f:
            for i, text in enumerate(all_texts, 1):
                f.write(f"=== 帖子 {i} ===\n")
                f.write(text)
                f.write(f"\n{'='*50}\n\n")
        
        # 保存JSON文件
        import json
        json_filename = f"{output_dir}/{base_keyword}_多策略合集_texts.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(all_texts, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 结果已保存:")
        print(f"  文本文件: {txt_filename}")
        print(f"  JSON文件: {json_filename}")
    
    def close(self):
        """关闭爬虫"""
        self.crawler.close()

def main():
    """主函数"""
    print("=== 小红书限制帖子数量的解决策略 ===")
    print("策略: 使用多个相关关键词获取更多帖子")
    
    strategy = LimitedPostsStrategy()
    
    try:
        # 配置参数
        base_keyword = "亲子旅游"  # 主关键词
        target_count = 100        # 目标帖子数量
        
        # 执行多策略获取
        all_texts = strategy.get_posts_with_multiple_strategies(base_keyword, target_count)
        
        # 显示结果统计
        if all_texts:
            total_chars = sum(len(text) for text in all_texts)
            avg_length = total_chars / len(all_texts)
            
            print(f"\n=== 最终统计 ===")
            print(f"获取帖子数量: {len(all_texts)}")
            print(f"总字符数: {total_chars:,}")
            print(f"平均长度: {avg_length:.0f} 字符/帖子")
            
            print(f"\n示例帖子内容:")
            print("-" * 50)
            print(all_texts[0][:200] + "..." if len(all_texts[0]) > 200 else all_texts[0])
            print("-" * 50)
        
    except Exception as e:
        print(f"执行过程中出现错误: {str(e)}")
    
    finally:
        strategy.close()

if __name__ == "__main__":
    main() 