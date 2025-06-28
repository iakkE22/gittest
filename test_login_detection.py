#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试小红书自动登录检测功能
"""

from xiaohongshu_crawler import XiaohongshuCrawler
import time

def test_login_detection():
    """测试登录检测功能"""
    print("开始测试小红书自动登录检测...")
    
    # 创建爬虫实例
    crawler = XiaohongshuCrawler(headless=False, wait_login=True)
    
    try:
        # 访问小红书首页
        print("访问小红书首页...")
        crawler.driver.get("https://www.xiaohongshu.com")
        time.sleep(3)
        
        # 测试登录状态检测
        print("\n第一次检测登录状态：")
        is_logged_in = crawler.check_login_status()
        print(f"登录状态检测结果: {'已登录' if is_logged_in else '未登录'}")
        
        # 如果未登录，等待用户登录
        if not is_logged_in:
            print("\n开始自动登录检测流程...")
            crawler.wait_for_manual_login()
        
        # 再次检测登录状态
        print("\n登录后再次检测状态：")
        is_logged_in_after = crawler.check_login_status()
        print(f"登录后状态检测结果: {'已登录' if is_logged_in_after else '未登录'}")
        
        # 测试搜索页面访问
        print("\n测试搜索页面访问...")
        search_url = "https://www.xiaohongshu.com/search_result?keyword=潜水"
        crawler.driver.get(search_url)
        time.sleep(3)
        
        # 检测搜索页面状态
        current_url = crawler.driver.current_url
        page_title = crawler.driver.title
        print(f"搜索页面URL: {current_url}")
        print(f"搜索页面标题: {page_title}")
        
        # 检测是否需要重新登录
        need_login = ("login" in current_url.lower() or "signin" in current_url.lower() or 
                     "login" in page_title.lower() or "登录" in page_title.lower())
        print(f"搜索页面是否需要登录: {'是' if need_login else '否'}")
        
        print("\n✓ 登录检测测试完成!")
        
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")
    
    finally:
        # 关闭浏览器
        input("\n按回车键关闭浏览器...")
        crawler.close()

if __name__ == "__main__":
    test_login_detection() 