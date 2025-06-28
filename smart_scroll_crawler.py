
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能滚动检测的小红书爬虫
专门用于调试和解决滚动加载问题
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class SmartScrollCrawler:
    def __init__(self):
        # Setup Chrome options
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
    
    def analyze_page_structure(self):
        """分析页面结构和滚动机制"""
        print("=== 分析页面结构 ===")
        
        # 获取初始页面信息
        initial_height = self.driver.execute_script("return document.body.scrollHeight")
        initial_cards = len(self.driver.find_elements(By.CSS_SELECTOR, "section.note-item"))
        print(f"初始页面高度: {initial_height}")
        print(f"初始卡片数量: {initial_cards}")
        
        # 检查页面是否有无限滚动
        print("\n=== 检测滚动机制 ===")
        
        for attempt in range(5):
            print(f"\n滚动尝试 {attempt + 1}/5:")
            
            # 滚动前状态
            before_height = self.driver.execute_script("return document.body.scrollHeight")
            before_cards = len(self.driver.find_elements(By.CSS_SELECTOR, "section.note-item"))
            print(f"  滚动前: 高度={before_height}, 卡片={before_cards}")
            
            # 滚动到底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # 等待加载
            
            # 滚动后状态
            after_height = self.driver.execute_script("return document.body.scrollHeight")
            after_cards = len(self.driver.find_elements(By.CSS_SELECTOR, "section.note-item"))
            print(f"  滚动后: 高度={after_height}, 卡片={after_cards}")
            
            # 分析变化
            height_changed = after_height > before_height
            cards_changed = after_cards > before_cards
            
            if height_changed or cards_changed:
                print(f"  ✓ 检测到内容更新!")
                if height_changed:
                    print(f"    页面高度增加: {after_height - before_height}px")
                if cards_changed:
                    print(f"    卡片数量增加: {after_cards - before_cards}个")
            else:
                print(f"  ✗ 无内容更新")
                break
            
            # 检查加载指示器
            loading_indicators = [
                ".loading",
                ".spinner",
                "[class*='loading']",
                "[class*='spinner']"
            ]
            
            for selector in loading_indicators:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    for elem in elements:
                        if elem.is_displayed():
                            print(f"    发现加载指示器: {selector}")
                            break
        
        # 查找加载更多按钮
        print("\n=== 检测加载更多按钮 ===")
        load_more_selectors = [
            "button[class*='load-more']",
            "div[class*='load-more']", 
            "a[class*='load-more']",
            ".load-more",
            "button:contains('加载更多')",
            "button:contains('更多')",
            "span:contains('加载更多')",
            "div:contains('加载更多')",
            "[data-testid*='load']",
            "[data-testid*='more']"
        ]
        
        found_buttons = []
        for selector in load_more_selectors:
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in buttons:
                    if btn.is_displayed():
                        text = btn.text.strip()
                        if text:
                            found_buttons.append((selector, text))
            except:
                continue
        
        if found_buttons:
            print("找到可能的加载更多按钮:")
            for selector, text in found_buttons:
                print(f"  - {selector}: '{text}'")
        else:
            print("未找到明显的加载更多按钮")
        
        # 检查页面底部元素
        print("\n=== 检查页面底部元素 ===")
        try:
            # 滚动到底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # 获取页面底部附近的元素
            bottom_elements = self.driver.find_elements(By.XPATH, "//*[position() >= last()-10]")
            print(f"页面底部附近有 {len(bottom_elements)} 个元素")
            
            for elem in bottom_elements[-5:]:  # 只看最后5个
                try:
                    tag = elem.tag_name
                    classes = elem.get_attribute("class") or ""
                    text = elem.text.strip()[:50] if elem.text else ""
                    if text or classes:
                        print(f"  {tag}.{classes}: {text}")
                except:
                    continue
                    
        except Exception as e:
            print(f"检查底部元素时出错: {str(e)}")
    
    def test_scroll_loading(self, keyword):
        """测试滚动加载功能"""
        print(f"=== 测试 '{keyword}' 的滚动加载 ===")
        
        # 访问搜索页面
        search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}"
        print(f"访问: {search_url}")
        self.driver.get(search_url)
        time.sleep(5)
        
        # 分析页面结构
        self.analyze_page_structure()
        
        print("\n=== 测试完成 ===")
    
    def close(self):
        """关闭浏览器"""
        self.driver.quit()

def main():
    """主函数"""
    print("=== 智能滚动检测工具 ===")
    
    crawler = SmartScrollCrawler()
    
    try:
        # 首先访问小红书首页
        print("访问小红书首页...")
        crawler.driver.get("https://www.xiaohongshu.com")
        
        # 等待用户登录
        input("\n请手动登录小红书，完成后按回车继续...")
        
        # 测试滚动加载
        keyword = "亲子旅游"
        crawler.test_scroll_loading(keyword)
        
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")
    
    finally:
        input("\n按回车键关闭浏览器...")
        crawler.close()

if __name__ == "__main__":
    main() 