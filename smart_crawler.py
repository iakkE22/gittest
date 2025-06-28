import time
import hashlib
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import argparse

class SmartXiaohongshuCrawler:
    def __init__(self, headless=False, output_dir="output", wait_login=True):
        self.output_dir = output_dir
        self.wait_login = wait_login
        self.global_post_counter = 0
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 设置Chrome选项
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # 初始化WebDriver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.set_window_size(1920, 1080)
        
        print("✓ Chrome浏览器已启动")

    def wait_for_manual_login(self):
        """等待用户手动登录"""
        print("\n" + "="*50)
        print("🔐 需要登录小红书")
        print("请在浏览器中手动完成登录，然后按回车键继续...")
        print("="*50)
        input("登录完成后，按回车键继续...")
        print("✓ 继续执行爬虫程序")

    def check_login_status(self):
        """检查登录状态"""
        print("正在检测登录状态...")
        
        # 检查多个可能的登录标识
        login_indicators = [
            ".avatar",
            ".username", 
            ".user-info",
            "[data-testid='avatar']",
            ".login-avatar"
        ]
        
        for indicator in login_indicators:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                if elements and any(elem.is_displayed() for elem in elements):
                    print(f"检测到已登录标识: {indicator}")
                    return True
            except:
                continue
        
        # 检查URL是否包含登录相关信息
        current_url = self.driver.current_url
        if any(keyword in current_url.lower() for keyword in ["login", "signin", "登录"]):
            print("当前页面为登录页面")
            return False
        
        print("未检测到明确的登录状态")
        return False

    def smart_search_and_collect(self, keyword, target_posts=100):
        """智能搜索和收集策略 - 避免卡片丢失"""
        print(f"🎯 开始智能搜索: '{keyword}'，目标帖子数: {target_posts}")
        
        try:
            # 访问小红书搜索页面
            search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}&type=51"
            print(f"访问搜索页面: {search_url}")
            self.driver.get(search_url)
            time.sleep(5)
            
            # 检查登录状态
            if self.wait_login and not self.check_login_status():
                self.wait_for_manual_login()
            
            # 收集所有帖子数据
            all_posts_data = []
            processed_urls = set()
            scroll_round = 0
            max_scroll_rounds = 20
            
            while len(all_posts_data) < target_posts and scroll_round < max_scroll_rounds:
                scroll_round += 1
                print(f"\n🔄 第 {scroll_round} 轮收集 (已收集: {len(all_posts_data)}/{target_posts})")
                
                # 获取当前页面的所有卡片信息
                cards_info = self._extract_all_cards_info()
                print(f"当前页面发现 {len(cards_info)} 个卡片")
                
                # 过滤掉已处理的卡片
                new_cards = [card for card in cards_info if card['url'] not in processed_urls]
                print(f"其中 {len(new_cards)} 个是新卡片")
                
                if not new_cards:
                    print("没有发现新卡片，尝试滚动获取更多内容...")
                    success = self._smart_scroll_for_more_content()
                    if not success:
                        print("滚动未获取到新内容，可能已到达底部")
                        break
                    continue
                
                # 批量处理新卡片
                for card_info in new_cards:
                    if len(all_posts_data) >= target_posts:
                        break
                    
                    print(f"\n📝 处理卡片: {card_info['preview'][:50]}...")
                    
                    # 获取完整内容
                    full_content = self._get_full_content_by_url(card_info['url'])
                    if full_content:
                        post_data = {
                            'index': len(all_posts_data) + 1,
                            'url': card_info['url'],
                            'preview': card_info['preview'],
                            'full_content': full_content,
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        all_posts_data.append(post_data)
                        processed_urls.add(card_info['url'])
                        print(f"✅ 成功收集第 {len(all_posts_data)} 个帖子")
                        
                        # 保存调试信息
                        self._save_debug_info(len(all_posts_data), full_content)
                    else:
                        print("❌ 获取完整内容失败")
                
                # 如果这轮收集到了新内容，继续滚动获取更多
                if new_cards:
                    print("本轮收集成功，滚动获取更多内容...")
                    self._smart_scroll_for_more_content()
                    time.sleep(2)  # 等待内容加载
            
            print(f"\n🎉 收集完成！总共获取 {len(all_posts_data)} 个帖子")
            
            # 保存结果
            if all_posts_data:
                self._save_results(all_posts_data, keyword)
                return [post['full_content'] for post in all_posts_data]
            else:
                print("未收集到任何帖子内容")
                return []
                
        except Exception as e:
            print(f"搜索过程中出现错误: {str(e)}")
            return []

    def _extract_all_cards_info(self):
        """提取当前页面所有卡片的基本信息"""
        cards_info = []
        
        # 尝试多种卡片选择器
        selectors = [
            "section.note-item",
            ".note-item", 
            ".feed-item",
            ".search-item"
        ]
        
        cards = []
        for selector in selectors:
            cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
            if cards:
                print(f"使用选择器 {selector} 找到 {len(cards)} 个卡片")
                break
        
        if not cards:
            print("未找到任何卡片")
            return []
        
        for i, card in enumerate(cards):
            try:
                # 获取卡片预览文本
                preview_text = card.text.strip()
                if not preview_text:
                    continue
                
                # 获取卡片链接
                card_url = self._extract_card_url(card)
                if not card_url:
                    continue
                
                cards_info.append({
                    'index': i + 1,
                    'url': card_url,
                    'preview': preview_text[:200],  # 只保留前200字符作为预览
                    'element_id': f"card_{i}"
                })
                
            except Exception as e:
                print(f"提取卡片 {i+1} 信息失败: {e}")
                continue
        
        return cards_info

    def _extract_card_url(self, card_element):
        """从卡片元素中提取URL"""
        try:
            # 尝试多种方法获取链接
            methods = [
                lambda: card_element.find_element(By.TAG_NAME, "a").get_attribute("href"),
                lambda: card_element.get_attribute("href"),
                lambda: card_element.find_element(By.CSS_SELECTOR, "[href]").get_attribute("href")
            ]
            
            for method in methods:
                try:
                    url = method()
                    if url and "xiaohongshu.com" in url:
                        return url
                except:
                    continue
            
            return None
            
        except Exception as e:
            return None

    def _get_full_content_by_url(self, post_url):
        """通过URL获取帖子的完整内容"""
        try:
            # 在新标签页打开
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            print(f"访问帖子: {post_url}")
            self.driver.get(post_url)
            time.sleep(3)
            
            # 检查是否需要登录
            if self.wait_login and not self.check_login_status():
                print("帖子页面需要登录")
                self.wait_for_manual_login()
            
            # 提取内容
            content = self._extract_post_content()
            
            # 关闭当前标签页，返回主页面
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            return content
            
        except Exception as e:
            print(f"获取帖子内容失败: {e}")
            # 确保返回主页面
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return None

    def _extract_post_content(self):
        """从当前页面提取帖子内容"""
        content_selectors = [
            ".note-content",
            ".content",
            ".note-detail", 
            ".desc",
            ".note-text",
            ".post-content",
            "[class*='content']",
            "[class*='desc']"
        ]
        
        for selector in content_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    if text and len(text) > 20:  # 过滤太短的文本
                        print(f"使用选择器 {selector} 获取到文本")
                        return text
            except:
                continue
        
        # 如果上述方法都失败，尝试获取页面主要文本
        try:
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            # 简单过滤，提取可能的内容部分
            lines = body_text.split('\n')
            content_lines = [line.strip() for line in lines if len(line.strip()) > 10]
            if content_lines:
                return '\n'.join(content_lines[:20])  # 取前20行
        except:
            pass
        
        return None

    def _smart_scroll_for_more_content(self):
        """智能滚动获取更多内容"""
        try:
            # 记录滚动前状态
            initial_height = self.driver.execute_script("return document.body.scrollHeight")
            initial_cards = self.driver.find_elements(By.CSS_SELECTOR, "section.note-item")
            initial_count = len(initial_cards)
            
            print(f"滚动前: 页面高度={initial_height}px, 卡片数={initial_count}")
            
            # 渐进式滚动策略
            scroll_steps = [
                ("小幅滚动", "window.scrollBy(0, 800);", 2),
                ("中幅滚动", "window.scrollBy(0, 1200);", 3),
                ("滚动到底部", "window.scrollTo(0, document.body.scrollHeight);", 4),
                ("回滚一点", "window.scrollBy(0, -400);", 2),
            ]
            
            for step_name, script, wait_time in scroll_steps:
                print(f"执行: {step_name}")
                self.driver.execute_script(script)
                time.sleep(wait_time)
                
                # 检查是否有新内容
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                current_cards = self.driver.find_elements(By.CSS_SELECTOR, "section.note-item")
                current_count = len(current_cards)
                
                height_change = current_height - initial_height
                count_change = current_count - initial_count
                
                print(f"  变化: 高度+{height_change}px, 卡片{count_change:+d}")
                
                # 如果检测到显著变化，说明有新内容
                if height_change > 1000:
                    print("✅ 检测到新内容加载")
                    return True
            
            print("❌ 滚动未产生新内容")
            return False
            
        except Exception as e:
            print(f"滚动出错: {e}")
            return False

    def _save_debug_info(self, post_index, content):
        """保存调试信息"""
        try:
            debug_file = os.path.join(self.output_dir, f"smart_debug_post_{post_index}.txt")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(f"帖子 {post_index} 调试信息\n")
                f.write("="*50 + "\n")
                f.write(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"内容长度: {len(content)} 字符\n")
                f.write("="*50 + "\n")
                f.write(content)
            print(f"调试信息已保存到 {debug_file}")
        except Exception as e:
            print(f"保存调试信息失败: {e}")

    def _save_results(self, posts_data, keyword):
        """保存收集结果"""
        try:
            # 保存为文本文件
            text_file = os.path.join(self.output_dir, f"{keyword}_smart_texts.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(f"小红书 '{keyword}' 搜索结果\n")
                f.write("="*50 + "\n")
                f.write(f"收集时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"总帖子数: {len(posts_data)}\n")
                f.write("="*50 + "\n\n")
                
                for post in posts_data:
                    f.write(f"帖子 {post['index']}\n")
                    f.write(f"URL: {post['url']}\n")
                    f.write(f"时间: {post['timestamp']}\n")
                    f.write("-" * 30 + "\n")
                    f.write(post['full_content'])
                    f.write("\n" + "="*50 + "\n\n")
            
            # 保存为JSON文件
            json_file = os.path.join(self.output_dir, f"{keyword}_smart_texts.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(posts_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 结果已保存:")
            print(f"   文本文件: {text_file}")
            print(f"   JSON文件: {json_file}")
            
        except Exception as e:
            print(f"保存结果失败: {e}")

    def close(self):
        """关闭浏览器"""
        try:
            self.driver.quit()
            print("✓ 浏览器已关闭")
        except:
            pass

def main():
    parser = argparse.ArgumentParser(description='智能小红书爬虫 - 避免卡片丢失')
    parser.add_argument('--keyword', type=str, required=True, help='搜索关键词')
    parser.add_argument('--num_posts', type=int, default=100, help='目标帖子数量')
    parser.add_argument('--headless', action='store_true', help='无头模式运行')
    
    args = parser.parse_args()
    
    crawler = SmartXiaohongshuCrawler(headless=args.headless)
    
    try:
        texts = crawler.smart_search_and_collect(args.keyword, args.num_posts)
        print(f"\n🎉 爬取完成！成功获取 {len(texts)} 个帖子")
        
    except KeyboardInterrupt:
        print("\n用户中断程序")
    except Exception as e:
        print(f"程序执行出错: {e}")
    finally:
        crawler.close()

if __name__ == "__main__":
    main() 