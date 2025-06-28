#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试小红书滚动加载功能
用于验证新的爬虫能否获取更多帖子
"""

from xiaohongshu_crawler import XiaohongshuCrawler

def test_scroll_crawler():
    """测试滚动加载功能"""
    print("=== 测试小红书滚动加载功能 ===")
    
    # 配置参数
    keyword = "亲子旅游"  # 搜索关键词
    target_posts = 50    # 目标帖子数量（设置较小的数量便于测试）
    
    print(f"搜索关键词: {keyword}")
    print(f"目标帖子数: {target_posts}")
    print("=" * 40)
    
    # 创建爬虫实例B3oiefhsdfjl;/sfjsl
    crawler = XiaohongshuCrawler(
        headless=False,        # 不使用无头模式，便于观察
        output_dir="test_output",
        wait_login=True
    )
    
    try:
        # 开始爬取
        posts_data = crawler.search_by_keyword(keyword, target_posts)
        
        # 显示结果
        print("\n" + "=" * 40)
        print(f"✓ 测试完成！")
        print(f"目标数量: {target_posts}")
        print(f"实际获取: {len(posts_data)}")
        print(f"完成率: {len(posts_data)/target_posts*100:.1f}%")
        
        if len(posts_data) > 0:
            print(f"\n示例文本（前100字符）:")
            print(posts_data[0][:100] + "..." if len(posts_data[0]) > 100 else posts_data[0])
        
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")
    
    finally:
        # 等待用户确认后关闭
        input("\n按回车键关闭浏览器...")
        crawler.close()

if __name__ == "__main__":
    test_scroll_crawler() 