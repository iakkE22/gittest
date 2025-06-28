#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
增强版小红书滚动检测工具
专门分析滚动后新增的内容类型，寻找更多帖子的获取方式
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class EnhancedScrollDetector:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        chrome_options.add_argument(f"user-agent={user_agent}")
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def analyze_all_content_types(self):
        """分析页面中所有可能的内容类型"""
        print("=== 分析所有内容类型 ===")
        
        # 多种可能的帖子选择器
        post_selectors = [
            "section.note-item",
            "div.note-item", 
            "article.note-item",
            "div[class*='note']",
            "div[class*='card']", 
            "div[class*='item']",
            "a[href*='/explore/']",
            "a[href*='/discovery/']",
            "[data-id]",
            "[data-note-id]"
        ]
        
        print("检测各种帖子选择器:")
        total_possible_posts = 0
        
        for selector in post_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                count = len(elements)
                if count > 0:
                    print(f"  {selector}: {count} 个元素")
                    total_possible_posts = max(total_possible_posts, count)
                    
                    # 分析前几个元素的属性
                    for i, elem in enumerate(elements[:3]):
                        try:
                            href = elem.get_attribute("href")
                            data_id = elem.get_attribute("data-id") or elem.get_attribute("data-note-id")
                            classes = elem.get_attribute("class") or ""
                            text_preview = elem.text[:50].replace('\n', ' ') if elem.text else ""
                            
                            info = []
                            if href and ("explore" in href or "discovery" in href):
                                info.append(f"href={href[:50]}...")
                            if data_id:
                                info.append(f"data-id={data_id}")
                            if text_preview:
                                info.append(f"text='{text_preview}...'")
                            
                            if info:
                                print(f"    [{i+1}] {' | '.join(info)}")
                        except:
                            continue
            except Exception as e:
                print(f"  {selector}: 错误 - {str(e)}")
        
        print(f"\n可能的最大帖子数量: {total_possible_posts}")
        return total_possible_posts
    
    def check_pagination_and_navigation(self):
        """检查分页和导航元素"""
        print("\n=== 检查分页和导航 ===")
        
        # 查找分页相关元素
        pagination_selectors = [
            ".pagination",
            ".page-nav", 
            ".next-page",
            ".load-more",
            "button[class*='next']",
            "button[class*='more']",
            "a[class*='next']",
            "a[class*='more']",
            "[data-testid*='page']",
            "[data-testid*='next']",
            "[data-testid*='load']"
        ]
        
        found_navigation = []
        for selector in pagination_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed():
                        text = elem.text.strip()
                        tag = elem.tag_name
                        classes = elem.get_attribute("class") or ""
                        onclick = elem.get_attribute("onclick") or ""
                        
                        found_navigation.append({
                            'selector': selector,
                            'tag': tag,
                            'text': text,
                            'classes': classes,
                            'onclick': onclick
                        })
            except:
                continue
        
        if found_navigation:
            print("找到导航元素:")
            for nav in found_navigation:
                print(f"  {nav['tag']}.{nav['classes']}: '{nav['text']}'")
                if nav['onclick']:
                    print(f"    onclick: {nav['onclick']}")
        else:
            print("未找到明显的分页/导航元素")
    
    def analyze_scroll_behavior(self, keyword):
        """深度分析滚动行为和内容变化"""
        print(f"\n=== 深度分析滚动行为 ===")
        
        # 访问搜索页面
        search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}"
        print(f"访问: {search_url}")
        self.driver.get(search_url)
        time.sleep(5)
        
        # 初始状态分析
        print("\n--- 初始状态 ---")
        initial_posts = self.analyze_all_content_types()
        self.check_pagination_and_navigation()
        
        # 滚动测试
        print("\n--- 滚动测试 ---")
        for i in range(3):
            print(f"\n第 {i+1} 次滚动:")
            
            # 滚动前
            before_height = self.driver.execute_script("return document.body.scrollHeight")
            before_posts = len(self.driver.find_elements(By.CSS_SELECTOR, "section.note-item"))
            
            # 滚动到底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(4)  # 等待加载
            
            # 滚动后
            after_height = self.driver.execute_script("return document.body.scrollHeight")
            after_posts = len(self.driver.find_elements(By.CSS_SELECTOR, "section.note-item"))
            
            print(f"  高度变化: {before_height} -> {after_height} ({after_height - before_height}px)")
            print(f"  帖子数量: {before_posts} -> {after_posts}")
            
            # 重新检查所有内容类型
            print("  重新分析内容类型:")
            new_total = self.analyze_all_content_types()
            
            # 检查是否有新的导航元素
            self.check_pagination_and_navigation()
            
            if after_height == before_height:
                print("  页面高度无变化，可能已到底部")
                break
    
    def check_alternative_urls(self, keyword):
        """检查其他可能的URL格式"""
        print(f"\n=== 检查其他URL格式 ===")
        
        alternative_urls = [
            f"https://www.xiaohongshu.com/search_result?keyword={keyword}&type=51&page=2",
            f"https://www.xiaohongshu.com/search_result?keyword={keyword}&sort=time",
            f"https://www.xiaohongshu.com/search_result?keyword={keyword}&sort=popular", 
            f"https://www.xiaohongshu.com/search?keyword={keyword}",
            f"https://www.xiaohongshu.com/explore?keyword={keyword}",
        ]
        
        for url in alternative_urls:
            try:
                print(f"\n测试URL: {url}")
                self.driver.get(url)
                time.sleep(3)
                
                # 检查帖子数量
                posts = len(self.driver.find_elements(By.CSS_SELECTOR, "section.note-item"))
                print(f"  帖子数量: {posts}")
                
                # 检查URL是否有效（没有重定向到错误页面）
                current_url = self.driver.current_url
                if "search" in current_url:
                    print(f"  ✓ URL有效: {current_url}")
                else:
                    print(f"  ✗ URL重定向: {current_url}")
                    
            except Exception as e:
                print(f"  错误: {str(e)}")
    
    def test_comprehensive_analysis(self, keyword):
        """综合分析测试"""
        print(f"=== 综合分析: '{keyword}' ===")
        
        # 首先访问小红书首页
        print("访问小红书首页...")
        self.driver.get("https://www.xiaohongshu.com")
        input("\n请手动登录小红书，完成后按回车继续...")
        
        # 执行各项分析
        self.analyze_scroll_behavior(keyword)
        self.check_alternative_urls(keyword)
        
        print("\n=== 综合分析完成 ===")
    
    def close(self):
        self.driver.quit()

def main():
    print("=== 增强版滚动检测工具 ===")
    
    detector = EnhancedScrollDetector()
    
    try:
        keyword = "亲子旅游"
        detector.test_comprehensive_analysis(keyword)
        
    except Exception as e:
        print(f"分析过程中出现错误: {str(e)}")
    
    finally:
        input("\n按回车键关闭浏览器...")
        detector.close()

if __name__ == "__main__":
    main() 