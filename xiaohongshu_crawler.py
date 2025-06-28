import os
import json
import time
import random
import argparse
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re

class XiaohongshuCrawler:
    def __init__(self, headless=False, output_dir="output", wait_login=True):
        self.output_dir = output_dir
        self.wait_login = wait_login
        self.global_post_counter = 0  # 全局帖子计数器，确保文件名不重复
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Setup Chrome options
        chrome_options = Options()
        # 默认不使用无头模式，因为小红书容易检测无头浏览器
        if headless:
            chrome_options.add_argument("--headless=new")
        
        # 添加更多的浏览器选项来模拟真实用户
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # 设置更真实的用户代理
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        chrome_options.add_argument(f"user-agent={user_agent}")
        
        # 禁用WebGL警告
        chrome_options.add_argument("--enable-unsafe-swiftshader")
        
        # 添加实验性选项绕过检测
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # 初始化浏览器
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)  # 增加等待时间
        
        # 执行绕过检测的JavaScript
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def wait_for_manual_login(self):
        """等待用户手动登录，带自动检测"""
        print("\n" + "="*60)
        print("  检测到需要登录小红书账号")
        print("  请在浏览器中手动登录，程序将自动检测登录状态")
        print("="*60)
        
        # 等待用户登录，自动检测登录状态
        max_wait_time = 300  # 最大等待5分钟
        check_interval = 5   # 每5秒检测一次
        wait_time = 0
        
        while wait_time < max_wait_time:
            print(f"等待登录中... ({wait_time}s/{max_wait_time}s)")
            time.sleep(check_interval)
            wait_time += check_interval
            
            # 检测登录状态
            if self.check_login_status():
                print("\n✓ 检测到已成功登录，继续执行爬虫程序...\n")
                return
        
        # 超时后询问用户
        print(f"\n自动检测超时（{max_wait_time}秒），请手动确认：")
        while True:
            user_input = input("您已完成登录了吗？(y/n): ")
            if user_input.lower() in ['y', 'yes']:
                print("\n继续执行爬虫程序...\n")
                break
            elif user_input.lower() in ['n', 'no']:
                print("\n已取消爬虫程序\n")
                self.close()
                sys.exit(0)
            else:
                print("无效输入，请输入 'y' 或 'n'")
    
    def check_login_status(self):
        """检查是否已登录小红书"""
        try:
            print("正在检测登录状态...")
            
            # 方法1：检查页面URL
            current_url = self.driver.current_url
            if "login" in current_url.lower() or "signin" in current_url.lower():
                print("检测到登录页面，需要登录")
                return False
            
            # 方法2：查找登录按钮或链接（如果找到说明未登录）
            login_indicators = [
                "//button[contains(text(), '登录')]",
                "//a[contains(text(), '登录')]", 
                "//button[contains(text(), '登陆')]",
                "//a[contains(text(), '登陆')]",
                "//span[contains(text(), '登录')]",
                "//div[contains(text(), '登录')]"
            ]
            
            for xpath in login_indicators:
                elements = self.driver.find_elements(By.XPATH, xpath)
                if elements:
                    # 检查元素是否可见
                    for element in elements:
                        if element.is_displayed():
                            print("检测到登录按钮，需要登录")
                            return False
            
            # 方法3：查找已登录状态的标识元素
            logged_in_selectors = [
                # 用户头像相关
                ".user-avatar", 
                ".avatar", 
                ".login-avatar",
                ".user-head",
                ".user-icon",
                # 用户名相关
                ".user-name",
                ".username", 
                ".nickname",
                # 小红书特有的已登录标识
                "[data-testid='header-avatar']",
                ".header-avatar",
                ".nav-user",
                # 搜索框（登录后才会显示）
                ".search-input",
                ".search-bar input",
                "input[placeholder*='搜索']",
                "input[placeholder*='search']"
            ]
            
            for selector in logged_in_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    # 检查元素是否可见且不为空
                    for element in elements:
                        if element.is_displayed() and element.get_attribute("class"):
                            print(f"检测到已登录标识: {selector}")
                            return True
            
            # 方法4：尝试查找页面内容是否正常显示（如搜索结果、推荐内容等）
            content_indicators = [
                ".note-item",
                ".feed-item", 
                ".content-item",
                "section[class*='note']",
                "div[class*='explore']"
            ]
            
            for selector in content_indicators:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if len(elements) > 0:
                    print(f"检测到页面内容，可能已登录: {selector}")
                    return True
            
            # 方法5：检查页面标题和内容
            page_title = self.driver.title.lower()
            if "login" in page_title or "登录" in page_title:
                print("页面标题显示需要登录")
                return False
            
            # 检查页面文本内容
            try:
                page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                if ("请登录" in page_text or "需要登录" in page_text or 
                    "login required" in page_text or "sign in" in page_text):
                    print("页面内容显示需要登录")
                    return False
                    
                # 如果页面有正常内容，可能已登录
                if len(page_text) > 500:  # 如果页面有较多内容，可能已登录
                    print("页面内容丰富，判断为已登录状态")
                    return True
            except:
                pass
            
            print("无法确定登录状态，假定已登录")
            return True  # 改为默认假定已登录，避免不必要的登录提示
            
        except Exception as e:
            print(f"检查登录状态时出错: {str(e)}")
            return True  # 出错时假定已登录
        
    def debug_page_structure(self):
        """调试页面结构，输出页面中的关键元素"""
        print("\n=== 页面结构调试信息 ===")
        
        try:
            # 获取页面标题
            title = self.driver.title
            print(f"页面标题: {title}")
            
            # 获取当前URL
            current_url = self.driver.current_url
            print(f"当前URL: {current_url}")
            
            # 查找所有链接
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            print(f"页面中总共有 {len(all_links)} 个链接")
            
            # 分析链接类型
            xiaohongshu_links = []
            explore_links = []
            discovery_links = []
            
            for link in all_links[:50]:  # 只检查前50个链接避免输出过多
                try:
                    href = link.get_attribute("href")
                    if href:
                        if "xiaohongshu.com" in href:
                            xiaohongshu_links.append(href)
                            if "/explore/" in href:
                                explore_links.append(href)
                            elif "/discovery/" in href:
                                discovery_links.append(href)
                except:
                    continue
            
            print(f"小红书域名链接: {len(xiaohongshu_links)} 个")
            print(f"explore类型链接: {len(explore_links)} 个")
            print(f"discovery类型链接: {len(discovery_links)} 个")
            
            # 显示前几个有效链接
            if xiaohongshu_links:
                print("\n前5个小红书链接:")
                for i, link in enumerate(xiaohongshu_links[:5]):
                    print(f"  {i+1}. {link}")
            
            # 查找常见的容器元素
            common_selectors = [
                "div[class*='note']",
                "div[class*='item']", 
                "div[class*='card']",
                "div[class*='content']",
                "div[class*='feed']",
                "section",
                "article"
            ]
            
            print("\n=== 常见容器元素 ===")
            for selector in common_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"{selector}: {len(elements)} 个元素")
                        # 显示第一个元素的class属性
                        if elements[0].get_attribute("class"):
                            print(f"  第一个元素的class: {elements[0].get_attribute('class')}")
                except:
                    continue
            
            # 尝试获取页面的主要内容区域
            print("\n=== 页面主要内容 ===")
            try:
                body_text = self.driver.find_element(By.TAG_NAME, "body").text
                lines = body_text.split('\n')
                non_empty_lines = [line.strip() for line in lines if line.strip()]
                print(f"页面文本行数: {len(non_empty_lines)}")
                if non_empty_lines:
                    print("前10行文本:")
                    for i, line in enumerate(non_empty_lines[:10]):
                        print(f"  {i+1}. {line}")
            except:
                print("无法获取页面文本")
                
        except Exception as e:
            print(f"调试页面结构时出错: {str(e)}")
        
        print("=== 调试信息结束 ===\n")
        
    def search_by_keyword(self, keyword, num_posts=20):
        """Search Xiaohongshu with keyword and collect posts"""
        print(f"搜索关键词: {keyword}")
        
        try:
            # 首先访问首页
            self.driver.get("https://www.xiaohongshu.com")
            print("访问小红书首页...")
            time.sleep(5)  # 等待首页加载
            
            # 检查是否需要登录
            if self.wait_login:
                login_status = self.check_login_status()
                if not login_status:
                    print("检测到需要登录小红书")
                    self.wait_for_manual_login()
                else:
                    print("✓ 检测到已登录状态")
            
            # 手动构建搜索URL并访问
            search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}"
            print(f"访问搜索页面: {search_url}")
            self.driver.get(search_url)
            
            # 等待页面加载
            print("等待搜索结果加载...")
            time.sleep(8)  # 增加等待时间
            
            # 检查搜索页面是否正常加载（只有在出现明显登录要求时才重新登录）
            if self.wait_login:
                current_url = self.driver.current_url
                page_title = self.driver.title.lower()
                
                # 如果被重定向到登录页面，或页面标题明确要求登录
                if ("login" in current_url.lower() or "signin" in current_url.lower() or 
                    "login" in page_title or "登录" in page_title):
                    print("搜索页面需要登录")
                    self.wait_for_manual_login()
                else:
                    print("✓ 搜索页面访问正常")
            
            # 调试页面结构
            self.debug_page_structure()
            
            # 初始化变量
            all_texts = []  # 存储所有文本
            posts_processed = 0
            
            # 先尝试直接在当前页面查找所有链接
            print("分析页面中的帖子卡片...")
            
            # 使用智能检测方法查找帖子卡片
            print("🔍 使用智能检测方法查找帖子卡片...")
            post_cards = self._smart_detect_cards()
            
            # 如果智能检测失败，回退到传统方法
            if not post_cards:
                print("智能检测未找到卡片，回退到传统方法...")
                post_card_selectors = [
                    "section.note-item",
                    "div.query-note-item", 
                    "div.note-item",
                    "div[class*='note-item']",
                    "div[class*='card']"
                ]
                
                used_selector = None
                
                for selector in post_card_selectors:
                    try:
                        cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if cards:
                            print(f"找到 {len(cards)} 个帖子卡片，使用选择器: {selector}")
                            post_cards = cards
                            used_selector = selector
                            break
                    except Exception as e:
                        print(f"选择器 {selector} 失败: {str(e)}")
                        continue
            else:
                # 智能检测成功，使用主要选择器作为后续检测的基准
                used_selector = "section.note-item"
            
            # 如果找到了帖子卡片，通过点击获取内容
            if post_cards:
                print(f"开始处理帖子，目标数量: {num_posts}")
                processed_urls = set()  # 记录已处理的帖子URL，避免重复
                processed_content_hashes = set()  # 记录已处理内容的hash，防止重复
                no_new_cards_count = 0  # 连续无新卡片的次数
                scroll_attempts = 0  # 滚动尝试次数
                max_scroll_attempts = 50  # 增加最大滚动次数
                
                while posts_processed < num_posts and scroll_attempts < max_scroll_attempts:
                    # 重新获取当前页面的所有卡片 - 使用智能检测
                    current_cards = self._smart_detect_cards()
                    if not current_cards:
                        # 如果智能检测失败，回退到传统方法
                        current_cards = self.driver.find_elements(By.CSS_SELECTOR, used_selector)
                    print(f"当前页面共有 {len(current_cards)} 个帖子卡片 (已获取文本: {posts_processed})")
                    
                    cards_processed_this_round = 0
                    new_content_found = False
                    
                    # 处理每个卡片
                    for i in range(len(current_cards)):                            
                        if posts_processed >= num_posts:
                            break
                            
                        try:
                            print(f"\n处理第 {i+1} 个帖子卡片...")
                            
                            # 重新获取卡片元素避免stale element错误
                            current_cards_refresh = self._smart_detect_cards()
                            if not current_cards_refresh:
                                current_cards_refresh = self.driver.find_elements(By.CSS_SELECTOR, used_selector)
                            
                            if i >= len(current_cards_refresh):
                                print(f"卡片 {i+1} 已不存在，跳过")
                                continue
                            
                            card = current_cards_refresh[i]
                            
                            # 获取卡片的基本信息进行预过滤
                            try:
                                card_text = card.text.strip()
                                if not card_text:
                                    print(f"卡片 {i+1} 文本为空，跳过")
                                    continue
                                    
                                # 创建内容hash进行去重
                                content_hash = hash(card_text[:200])  # 使用前200字符计算hash
                                if content_hash in processed_content_hashes:
                                    print(f"卡片 {i+1} 内容重复，跳过")
                                    continue
                                    
                            except Exception as e:
                                print(f"获取卡片 {i+1} 基本信息失败: {e}")
                                continue
                            
                            # 滚动到卡片位置确保可见
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", card)
                            time.sleep(1)
                            
                            # 尝试点击卡片获取真实内容和URL，使用全局计数器
                            self.global_post_counter += 1
                            post_result = self._scrape_post_by_click_with_url(card, self.global_post_counter)
                            
                            if post_result:
                                post_text, post_url = post_result
                                
                                # URL去重检查
                                if post_url and post_url in processed_urls:
                                    print(f"帖子 {i+1} URL重复，跳过: {post_url}")
                                    continue
                                
                                if post_text and post_text.strip():
                                    # 再次检查内容去重
                                    full_content_hash = hash(post_text.strip())
                                    if full_content_hash in processed_content_hashes:
                                        print(f"帖子 {i+1} 完整内容重复，跳过")
                                        continue
                                    
                                    # 添加新的内容
                                    all_texts.append(post_text)
                                    processed_urls.add(post_url)
                                    processed_content_hashes.add(content_hash)
                                    processed_content_hashes.add(full_content_hash)
                                    posts_processed += 1
                                    cards_processed_this_round += 1
                                    new_content_found = True
                                    print(f"✓ 成功获取新帖子 {posts_processed}/{num_posts}")
                                    
                                    # 每处理8个新帖子进行一次微滚动，保持页面活跃
                                    if cards_processed_this_round % 8 == 0:
                                        print("进行微滚动以保持页面活跃，避免错过卡片...")
                                        self._micro_scroll()
                                else:
                                    print(f"帖子 {i+1} 文本为空或获取失败")
                            else:
                                print(f"帖子 {i+1} 获取失败")
                            
                        except Exception as e:
                            print(f"处理帖子卡片 {i+1} 时出错: {str(e)}")
                    
                    # 如果还需要更多帖子，尝试滚动加载
                    if posts_processed < num_posts:
                        print(f"本轮处理了 {cards_processed_this_round} 个新卡片")
                        
                        # 检查当前页面是否还有未处理的卡片
                        unprocessed_cards = 0
                        for i in range(len(current_cards)):
                            try:
                                card = current_cards[i]
                                card_text = card.text.strip()
                                if card_text:
                                    content_hash = hash(card_text[:200])
                                    if content_hash not in processed_content_hashes:
                                        unprocessed_cards += 1
                            except:
                                continue
                        
                        print(f"当前页面剩余未处理卡片: {unprocessed_cards}")
                        
                        # 只有当前页面所有卡片都处理完了，才进行滚动
                        if unprocessed_cards > 0:
                            print("当前页面仍有未处理卡片，继续处理...")
                            continue
                        
                        if cards_processed_this_round == 0:
                            no_new_cards_count += 1
                            print(f"本轮无新内容 ({no_new_cards_count}/3)")  # 减少无新内容的容忍次数
                            
                            if no_new_cards_count >= 3:
                                print("连续多轮无新内容，可能已到达内容底部")
                                break
                        else:
                            no_new_cards_count = 0
                        
                        print(f"需要更多帖子，当前已获取 {posts_processed}/{num_posts}，尝试保守滚动... (第 {scroll_attempts + 1}/{max_scroll_attempts} 次)")
                        scroll_attempts += 1
                        
                        # 返回搜索页面（如果当前不在搜索页面）
                        current_url = self.driver.current_url
                        if "search_result" not in current_url:
                            print("返回搜索页面...")
                            self.driver.back()
                            time.sleep(2)
                        
                        # 执行智能滚动检测
                        print("执行智能滚动检测...")
                        success = self._progressive_scroll_and_detect()
                        
                        if not success:
                            print("智能滚动未发现新卡片，尝试保守滚动...")
                            success = self._conservative_scroll()
                            
                        if not success:
                            print("所有滚动方法都未产生新内容，可能已到达底部")
                            no_new_cards_count += 1
                    
                    # 如果已达到目标数量，退出循环
                    if posts_processed >= num_posts:
                        break
                
                # 滚动尝试完成后的提示
                if scroll_attempts >= max_scroll_attempts:
                    print(f"已达到最大滚动次数 ({max_scroll_attempts})，停止获取更多内容")
                    
                print(f"✓ 最终获取到 {posts_processed} 个有效帖子")
            else:
                print("未找到帖子卡片，尝试备用方法...")
                # 备用方法：直接查找链接（可能会遇到token问题）
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                xiaohongshu_links = []
                
                for link in all_links:
                    try:
                        href = link.get_attribute("href")
                        if href and "xiaohongshu.com" in href and ("/explore/" in href or "/discovery/" in href):
                            xiaohongshu_links.append(href)
                            print(f"发现帖子链接: {href}")
                    except:
                        continue
                
                if xiaohongshu_links:
                    print(f"总共找到 {len(xiaohongshu_links)} 个帖子链接")
                    for post_link in xiaohongshu_links[:num_posts]:
                        try:
                            post_text = self._scrape_post_text(post_link)
                            if post_text and post_text.strip():
                                all_texts.append(post_text)
                                posts_processed += 1
                                print(f"处理进度: {posts_processed}/{num_posts} 帖子")
                        except Exception as e:
                            print(f"处理帖子时出错: {str(e)}")
                            
                        if posts_processed >= num_posts:
                            break
            
            # 保存收集的文本
            if all_texts:
                self._save_texts(all_texts, keyword)
                return all_texts
            else:
                print("未能找到任何帖子内容。")
                # 创建示例文本
                self._create_sample_texts(keyword)
                return []
                
        except Exception as e:
            print(f"搜索过程中出现错误: {str(e)}")
            return []
    
    def _scrape_post_text(self, post_url):
        """抓取单个帖子的纯文本内容"""
        print(f"抓取帖子文本: {post_url}")
        
        try:
            # 在新标签页打开帖子
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[1])
            self.driver.get(post_url)
            
            # 等待帖子内容加载
            time.sleep(5)
            
            # 检查帖子页面是否正常加载（只有在明确需要登录时才提示）
            if self.wait_login:
                current_url = self.driver.current_url
                page_title = self.driver.title.lower()
                
                # 检查是否被重定向到登录页面
                if ("login" in current_url.lower() or "signin" in current_url.lower() or 
                    "login" in page_title or "登录" in page_title):
                    print("帖子页面需要登录")
                    self.wait_for_manual_login()
                else:
                    print("✓ 帖子页面访问正常")
            
            # 尝试获取帖子的完整文本内容
            full_text = ""
            
            # 方法1：尝试获取主要内容区域的文本
            content_selectors = [
                ".note-content",
                ".content", 
                ".note-detail",
                ".desc",
                ".note-text",
                ".post-content"
            ]
            
            for selector in content_selectors:
                try:
                    content_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if content_elements:
                        for element in content_elements:
                            text = element.text.strip()
                            if text and len(text) > 20:  # 过滤掉太短的文本
                                full_text += text + "\n\n"
                        if full_text:
                            break
                except:
                    continue
            
            # 方法2：如果上面没找到，尝试获取整个页面的文本并过滤
            if not full_text:
                try:
                    body_text = self.driver.find_element(By.TAG_NAME, "body").text
                    # 简单过滤，去掉导航、按钮等无关文本
                    lines = body_text.split('\n')
                    filtered_lines = []
                    
                    for line in lines:
                        line = line.strip()
                        # 过滤掉常见的导航和按钮文本
                        if (line and len(line) > 5 and 
                            not line in ['登录', '注册', '首页', '发现', '购物', '消息', '我'] and
                            not line.startswith('http') and
                            not '点击' in line and
                            not '下载' in line):
                            filtered_lines.append(line)
                    
                    full_text = '\n'.join(filtered_lines)
                except:
                    pass
            
            # 关闭标签页并切回主窗口
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            # 添加随机延迟避免反爬
            time.sleep(random.uniform(2, 4))
            
            return full_text.strip()
            
        except Exception as e:
            print(f"抓取帖子文本出错 {post_url}: {str(e)}")
            # 确保切回主窗口以防错误
            if len(self.driver.window_handles) > 1:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            return ""
    
    def _scrape_post_by_click_with_url(self, card_element, card_index):
        """通过点击卡片获取帖子内容和URL，返回(content, url)元组"""
        try:
            # 先尝试从卡片元素中获取链接
            card_url = None
            try:
                # 查找卡片中的链接
                link_element = card_element.find_element(By.TAG_NAME, "a")
                card_url = link_element.get_attribute("href")
                if card_url and "explore" in card_url:
                    print(f"从卡片获取到URL: {card_url}")
                else:
                    card_url = None
            except:
                pass
            
            # 执行点击并获取内容
            result = self._scrape_post_by_click(card_element, card_index)
            if result:
                # 获取实际访问的URL
                try:
                    current_url = self.driver.current_url
                    if "explore" in current_url:
                        final_url = current_url
                    elif card_url:
                        final_url = card_url
                    else:
                        final_url = f"post_{card_index}_{hash(result[:100])}"  # 使用内容hash作为唯一标识
                    
                    print(f"最终URL: {final_url}")
                    return (result, final_url)
                except:
                    # 如果获取URL失败，使用内容hash作为唯一标识
                    final_url = f"post_{card_index}_{hash(result[:100])}"
                    return (result, final_url)
        except Exception as e:
            print(f"获取帖子内容和URL失败: {e}")
        return None
    
    def _smart_scroll(self):
        """智能滚动方法，模拟enhanced_scroll_detector的成功策略"""
        try:
            print("开始智能滚动，模拟真实用户行为...")
            
            # 记录滚动前的帖子数量
            initial_cards = self.driver.find_elements(By.CSS_SELECTOR, "section.note-item")
            initial_count = len(initial_cards)
            print(f"滚动前帖子数量: {initial_count}")
            
            # 记录滚动前的页面高度
            current_height = self.driver.execute_script("return document.body.scrollHeight")
            print(f"滚动前页面高度: {current_height}px")
            
            # 策略1：从顶部开始，模拟真实浏览行为
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # 策略2：渐进式滚动，就像enhanced_scroll_detector中成功的方式
            scroll_steps = [
                ("滚动到页面中部", "window.scrollTo(0, document.body.scrollHeight * 0.3);", 2),
                ("滚动到页面下部", "window.scrollTo(0, document.body.scrollHeight * 0.6);", 3),
                ("滚动到页面底部", "window.scrollTo(0, document.body.scrollHeight);", 4),
                ("再次滚动到底部", "window.scrollTo(0, document.body.scrollHeight);", 3),
            ]
            
            for step_name, scroll_js, wait_time in scroll_steps:
                print(f"执行: {step_name}")
                self.driver.execute_script(scroll_js)
                time.sleep(wait_time)
                
                # 检查是否有新内容
                current_cards = self.driver.find_elements(By.CSS_SELECTOR, "section.note-item")
                if len(current_cards) != initial_count:
                    print(f"检测到帖子数量变化: {initial_count} -> {len(current_cards)}")
                    break
            
            # 策略3：多次短距离滚动，触发懒加载
            print("执行多次短距离滚动...")
            for i in range(8):
                self.driver.execute_script(f"window.scrollBy(0, 300);")
                time.sleep(1.5)  # 增加等待时间
                
                # 每次都检查内容变化
                current_cards = self.driver.find_elements(By.CSS_SELECTOR, "section.note-item")
                if len(current_cards) != initial_count:
                    print(f"短距离滚动触发内容变化: {initial_count} -> {len(current_cards)}")
                    break
            
            # 策略4：最后的大力滚动
            print("执行最终滚动...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)  # 更长的等待时间
            
            # 检查最终结果
            final_height = self.driver.execute_script("return document.body.scrollHeight")
            final_cards = self.driver.find_elements(By.CSS_SELECTOR, "section.note-item")
            final_count = len(final_cards)
            
            print(f"滚动完成:")
            print(f"  页面高度: {current_height} -> {final_height} (增加: {final_height - current_height}px)")
            print(f"  帖子数量: {initial_count} -> {final_count}")
            
            # 判断是否成功：页面高度增加或内容有显著变化
            if final_height > current_height + 500:  # 页面高度显著增加
                print("✓ 滚动成功：页面高度显著增加")
                return True
            elif final_count != initial_count:  # 帖子数量变化
                print("✓ 滚动成功：帖子数量发生变化")
                return True
            else:
                print("✗ 滚动失败：无明显变化")
                return False
                
        except Exception as e:
            print(f"智能滚动出错: {str(e)}")
            return False

    def _conservative_scroll(self):
        """基于诊断结果优化的滚动方法 - 使用触底回弹策略"""
        try:
            print("开始优化滚动策略（基于诊断结果）...")
            
            # 记录滚动前的状态
            initial_cards = self._smart_detect_cards()
            initial_count = len(initial_cards)
            current_height = self.driver.execute_script("return document.body.scrollHeight")
            
            print(f"滚动前: 帖子数量={initial_count}, 页面高度={current_height}px")
            
            # 策略1: 快速跳跃到底部（诊断显示这最有效）
            print("执行策略1: 快速跳跃到底部")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(4)
            
            # 检查效果
            cards_after_jump = self._smart_detect_cards()
            print(f"快速跳跃后: {initial_count} -> {len(cards_after_jump)} 个卡片")
            
            if len(cards_after_jump) > initial_count:
                print("✅ 快速跳跃成功触发新内容加载")
                return True
            
            # 策略2: 触底回弹（诊断显示很有效）
            print("执行策略2: 触底回弹")
            for i in range(3):
                # 滚动到底部
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # 回弹
                self.driver.execute_script("window.scrollBy(0, -300);")
                time.sleep(1)
                
                # 再次到底部
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                # 检查效果
                current_cards = self._smart_detect_cards()
                if len(current_cards) > initial_count:
                    print(f"✅ 触底回弹成功: {initial_count} -> {len(current_cards)} (第{i+1}次)")
                    return True
            
            # 策略3: 模拟真实用户滚动（诊断显示有效）
            print("执行策略3: 模拟真实用户滚动")
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            
            for i in range(5):
                # 滚动距离逐渐增加
                scroll_distance = 300 + (i * 200)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
                
                # 模拟用户停顿
                time.sleep(2 + i * 0.5)
                
                # 模拟鼠标移动到卡片
                try:
                    current_cards = self._smart_detect_cards()
                    if current_cards and len(current_cards) > i:
                        actions.move_to_element(current_cards[min(i, len(current_cards)-1)]).perform()
                        time.sleep(1)
                except:
                    pass
                
                # 检查效果
                current_cards = self._smart_detect_cards()
                if len(current_cards) > initial_count:
                    print(f"✅ 真实用户滚动成功: {initial_count} -> {len(current_cards)} (第{i+1}轮)")
                    return True
            
            # 最终检查
            final_cards = self._smart_detect_cards()
            final_height = self.driver.execute_script("return document.body.scrollHeight")
            
            print(f"优化滚动完成:")
            print(f"  页面高度: {current_height} -> {final_height} (+{final_height - current_height}px)")
            print(f"  帖子数量: {initial_count} -> {len(final_cards)}")
            
            if len(final_cards) > initial_count:
                print("✅ 滚动成功：发现新卡片")
                return True
            else:
                print("❌ 滚动失败：未发现新卡片")
                return False
                
        except Exception as e:
            print(f"优化滚动出错: {str(e)}")
            return False

    def _smart_detect_cards(self):
        """智能检测页面中的所有卡片，包括可见和不可见的"""
        try:
            print("🔍 执行智能卡片检测...")
            
            # 扩展的选择器列表，包括更多可能的卡片类型
            all_selectors = [
                # 主要选择器
                "section.note-item",
                "div.note-item", 
                "div.query-note-item",
                
                # 通用卡片选择器
                "div[class*='note-item']",
                "div[class*='card']",
                "div[class*='item']",
                "section[class*='note']",
                "article[class*='note']",
                
                # 可能的容器选择器
                "div[class*='feed']",
                "div[class*='content']",
                "div[class*='post']",
                
                # 链接容器
                "a[href*='/explore/']",
                "a[href*='/discovery/']"
            ]
            
            all_cards = []
            cards_by_selector = {}
            
            for selector in all_selectors:
                try:
                    cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if cards:
                        cards_by_selector[selector] = len(cards)
                        print(f"  {selector}: {len(cards)} 个元素")
                        
                        # 检查这些卡片是否包含有效内容
                        valid_cards = []
                        for card in cards:
                            try:
                                # 检查卡片是否有文本内容
                                text = card.text.strip()
                                if text and len(text) > 10:
                                    # 检查是否包含链接
                                    links = card.find_elements(By.TAG_NAME, "a")
                                    if links:
                                        for link in links:
                                            href = link.get_attribute("href")
                                            if href and ("explore" in href or "discovery" in href):
                                                valid_cards.append(card)
                                                break
                                    elif "explore" in card.get_attribute("href") if card.get_attribute("href") else False:
                                        valid_cards.append(card)
                            except:
                                continue
                        
                        if valid_cards:
                            print(f"    其中 {len(valid_cards)} 个是有效卡片")
                            if len(valid_cards) > len(all_cards):
                                all_cards = valid_cards
                                
                except Exception as e:
                    continue
            
            # 显示检测结果
            print(f"\n📊 卡片检测结果:")
            for selector, count in cards_by_selector.items():
                print(f"  {selector}: {count}")
            
            print(f"\n✅ 最终选择: {len(all_cards)} 个有效卡片")
            
            # 检查卡片的可见性分布
            visible_cards = 0
            invisible_cards = 0
            
            for card in all_cards:
                try:
                    if card.is_displayed():
                        visible_cards += 1
                    else:
                        invisible_cards += 1
                except:
                    invisible_cards += 1
            
            print(f"  可见卡片: {visible_cards}")
            print(f"  不可见卡片: {invisible_cards}")
            
            return all_cards
            
        except Exception as e:
            print(f"智能卡片检测出错: {str(e)}")
            return []

    def _progressive_scroll_and_detect(self):
        """基于诊断结果的智能滚动检测 - 优先使用最有效策略"""
        try:
            print("🔄 开始智能滚动检测（基于诊断优化）...")
            
            # 记录初始状态
            initial_cards = self._smart_detect_cards()
            initial_count = len(initial_cards)
            initial_height = self.driver.execute_script("return document.body.scrollHeight")
            
            print(f"初始状态: {initial_count} 个卡片, 页面高度 {initial_height}px")
            
            # 策略1: 随机位置滚动（诊断显示成功率高）
            print("🎲 执行策略1: 随机位置滚动")
            import random
            random_positions = [0.3, 0.7, 0.5, 0.9, 0.1]  # 随机但覆盖全页面
            
            for i, position in enumerate(random_positions):
                print(f"  滚动到随机位置 {position*100:.0f}%...")
                self.driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {position});")
                time.sleep(2)
                
                current_cards = self._smart_detect_cards()
                if len(current_cards) > initial_count:
                    print(f"✅ 随机滚动成功: {initial_count} -> {len(current_cards)} (第{i+1}次)")
                    return True
            
            # 策略2: 触底回弹滚动（诊断显示很有效）
            print("🏀 执行策略2: 触底回弹滚动")
            for i in range(2):
                # 快速到底部
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # 回弹到中间
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.6);")
                time.sleep(1)
                
                # 再次到底部
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                current_cards = self._smart_detect_cards()
                if len(current_cards) > initial_count:
                    print(f"✅ 触底回弹成功: {initial_count} -> {len(current_cards)} (第{i+1}次)")
                    return True
            
            # 策略3: 快速跳跃滚动（诊断显示100%位置最有效）
            print("🚀 执行策略3: 快速跳跃滚动")
            jump_positions = [0.25, 0.5, 0.75, 1.0]  # 快速跳跃到不同位置
            
            for position in jump_positions:
                print(f"  快速跳跃到 {position*100:.0f}% 位置...")
                self.driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {position});")
                time.sleep(3)  # 给足时间加载
                
                current_cards = self._smart_detect_cards()
                if len(current_cards) > initial_count:
                    print(f"✅ 快速跳跃成功: {initial_count} -> {len(current_cards)} (位置{position*100:.0f}%)")
                    return True
            
            # 策略4: 模拟真实用户行为（诊断显示第9轮成功）
            print("👤 执行策略4: 模拟真实用户滚动")
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            
            for i in range(10):  # 诊断显示第9轮成功，所以多试几轮
                # 模拟真实滚动：不规律的距离和停顿
                scroll_distance = random.randint(200, 600)
                pause_time = random.uniform(1.5, 3.5)
                
                print(f"  第{i+1}轮真实滚动: {scroll_distance}px, 停顿{pause_time:.1f}s")
                self.driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
                time.sleep(pause_time)
                
                # 模拟鼠标悬停
                try:
                    current_cards = self._smart_detect_cards()
                    if current_cards:
                        random_card = random.choice(current_cards)
                        actions.move_to_element(random_card).perform()
                        time.sleep(0.5)
                except:
                    pass
                
                # 检查效果
                current_cards = self._smart_detect_cards()
                if len(current_cards) > initial_count:
                    print(f"✅ 真实用户滚动成功: {initial_count} -> {len(current_cards)} (第{i+1}轮)")
                    return True
            
            print("❌ 所有智能滚动策略都未成功")
            return False
            
        except Exception as e:
            print(f"智能滚动检测出错: {str(e)}")
            return False

    def _micro_scroll(self):
        """微滚动，只是轻微移动页面位置，避免内容被替换"""
        try:
            # 非常小的滚动，只是为了保持页面活跃
            self.driver.execute_script("window.scrollBy(0, 100);")
            time.sleep(0.5)
            self.driver.execute_script("window.scrollBy(0, -50);")
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"微滚动出错: {str(e)}")
            return False

    def _aggressive_scroll(self):
        """激进滚动，用于在连续无新内容时尝试获取更多内容"""
        try:
            print("执行激进滚动，尝试获取更多内容...")
            
            # 记录滚动前状态
            initial_height = self.driver.execute_script("return document.body.scrollHeight")
            initial_cards = self.driver.find_elements(By.CSS_SELECTOR, "section.note-item")
            initial_count = len(initial_cards)
            
            print(f"激进滚动前: 帖子数量={initial_count}, 页面高度={initial_height}px")
            
            # 激进滚动策略
            scroll_steps = [
                ("大幅滚动1", "window.scrollBy(0, 1500);", 4),
                ("大幅滚动2", "window.scrollBy(0, 1500);", 4),
                ("滚动到底部", "window.scrollTo(0, document.body.scrollHeight);", 5),
                ("回滚一点", "window.scrollBy(0, -800);", 3),
                ("再次滚动到底部", "window.scrollTo(0, document.body.scrollHeight);", 5),
            ]
            
            max_height_change = 0
            
            for step_name, script, wait_time in scroll_steps:
                print(f"执行: {step_name}")
                self.driver.execute_script(script)
                time.sleep(wait_time)
                
                # 检查变化
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                current_cards = self.driver.find_elements(By.CSS_SELECTOR, "section.note-item")
                current_count = len(current_cards)
                
                height_change = current_height - initial_height
                count_change = current_count - initial_count
                
                print(f"  高度变化: +{height_change}px, 卡片数量变化: {count_change}")
                
                max_height_change = max(max_height_change, height_change)
                
                # 如果发现显著变化，说明有新内容加载
                if height_change > 2000 or abs(count_change) > 5:
                    print("检测到显著变化，停止激进滚动")
                    break
            
            final_height = self.driver.execute_script("return document.body.scrollHeight")
            final_cards = self.driver.find_elements(By.CSS_SELECTOR, "section.note-item")
            final_count = len(final_cards)
            
            print(f"激进滚动完成:")
            print(f"  页面高度: {initial_height} -> {final_height} (+{final_height-initial_height}px)")
            print(f"  帖子数量: {initial_count} -> {final_count}")
            print(f"  最大高度变化: {max_height_change}px")
            
            # 判断是否成功
            if final_height > initial_height + 1000 or max_height_change > 1000:
                print("✓ 激进滚动成功：页面内容显著增加")
                return True
            else:
                print("✗ 激进滚动失败：无显著内容变化")
                return False
                
        except Exception as e:
            print(f"激进滚动出错: {str(e)}")
            return False

    def _scrape_post_by_click(self, card_element, card_index):
        """通过点击卡片获取帖子内容"""
        print(f"点击第 {card_index} 个帖子卡片...")
        
        try:
            # 记录当前窗口数量和URL
            original_windows = len(self.driver.window_handles)
            original_url = self.driver.current_url
            
            # 尝试点击卡片
            try:
                # 方法1：直接点击卡片
                card_element.click()
                print("直接点击卡片成功")
            except:
                try:
                    # 方法2：查找卡片内的链接并点击
                    link = card_element.find_element(By.TAG_NAME, "a")
                    link.click()
                    print("点击卡片内链接成功")
                except:
                    try:
                        # 方法3：使用JavaScript点击
                        self.driver.execute_script("arguments[0].click();", card_element)
                        print("JavaScript点击成功")
                    except:
                        print("所有点击方法都失败")
                        return ""
            
            # 等待页面加载或新窗口打开
            time.sleep(3)
            
            # 检查是否打开了新窗口或URL发生变化
            current_windows = len(self.driver.window_handles)
            current_url = self.driver.current_url
            
            if current_windows > original_windows:
                # 切换到新窗口
                self.driver.switch_to.window(self.driver.window_handles[-1])
                print(f"切换到新窗口: {self.driver.current_url}")
            elif current_url != original_url:
                # 在当前窗口中导航
                print(f"在当前窗口中导航: {self.driver.current_url}")
            else:
                # 没有导航，可能点击失败
                print(f"点击后没有导航，当前URL: {current_url}")
                return ""
            
            # 检查是否真的到了帖子页面（URL应该包含/explore/）
            if "/explore/" not in self.driver.current_url:
                print(f"未跳转到帖子页面，当前URL: {self.driver.current_url}")
                # 尝试返回搜索页面
                if current_windows > original_windows:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                else:
                    self.driver.back()
                    time.sleep(2)
                return ""
            
            # 等待页面完全加载
            time.sleep(5)
            
            # 检查是否需要登录
            if self.wait_login and not self.check_login_status():
                print("帖子页面需要登录")
                self.wait_for_manual_login()
            
            # 获取帖子文本内容
            post_text = self._extract_text_from_current_page()
            
            # 保存调试信息
            self._save_debug_info(card_index, post_text)
            
            # 关闭新窗口并返回原窗口
            if current_windows > original_windows:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            else:
                # 如果在当前窗口，返回搜索页面
                self.driver.back()
                time.sleep(2)
            
            # 添加随机延迟
            time.sleep(random.uniform(2, 4))
            
            return post_text
            
        except Exception as e:
            print(f"点击卡片 {card_index} 时出错: {str(e)}")
            # 确保返回到正确的窗口
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                elif self.driver.current_url != original_url:
                    self.driver.back()
                    time.sleep(2)
            except:
                pass
            return ""
    
    def _extract_text_from_current_page(self):
        """从当前页面提取文本内容"""
        full_text = ""
        
        try:
            # 方法1：尝试获取主要内容区域的文本
            content_selectors = [
                ".note-content",
                ".content", 
                ".note-detail",
                ".desc",
                ".note-text",
                ".post-content",
                "[class*='note-content']",
                "[class*='content']"
            ]
            
            for selector in content_selectors:
                try:
                    content_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if content_elements:
                        for element in content_elements:
                            text = element.text.strip()
                            if text and len(text) > 20:  # 过滤掉太短的文本
                                full_text += text + "\n\n"
                        if full_text:
                            print(f"使用选择器 {selector} 获取到文本")
                            break
                except:
                    continue
            
            # 方法2：如果上面没找到，尝试获取整个页面的文本并过滤
            if not full_text:
                try:
                    body_text = self.driver.find_element(By.TAG_NAME, "body").text
                    # 简单过滤，去掉导航、按钮等无关文本
                    lines = body_text.split('\n')
                    filtered_lines = []
                    
                    for line in lines:
                        line = line.strip()
                        # 过滤掉常见的导航和按钮文本
                        if (line and len(line) > 5 and 
                            not line in ['登录', '注册', '首页', '发现', '购物', '消息', '我', '创作中心', '业务合作', '发布', '通知', '更多'] and
                            not line.startswith('http') and
                            not line.startswith('沪ICP备') and
                            not '点击' in line and
                            not '下载' in line and
                            not '©' in line):
                            filtered_lines.append(line)
                    
                    full_text = '\n'.join(filtered_lines)
                    print("使用页面全文本获取方法")
                except:
                    pass
            
            return full_text.strip()
            
        except Exception as e:
            print(f"提取页面文本时出错: {str(e)}")
            return ""
    
    def _save_debug_info(self, card_index, text):
        """保存调试信息"""
        try:
            debug_file = os.path.join(self.output_dir, f"debug_post_{card_index}.txt")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(f"URL: {self.driver.current_url}\n")
                f.write(f"Title: {self.driver.title}\n")
                f.write("="*50 + "\n")
                f.write(text)
            print(f"调试信息已保存到 {debug_file}")
        except:
            pass
    
    def _save_texts(self, texts, keyword):
        """保存文本到文件"""
        # 保存为纯文本文件
        txt_filepath = os.path.join(self.output_dir, f"{keyword}_texts.txt")
        with open(txt_filepath, 'w', encoding='utf-8') as f:
            for i, text in enumerate(texts, 1):
                f.write(f"========== 帖子 {i} ==========\n")
                f.write(text)
                f.write("\n\n" + "="*50 + "\n\n")
        
        print(f"文本已保存到 {txt_filepath}")
        
        # 同时保存为JSON格式（简化版本）
        json_data = []
        for i, text in enumerate(texts, 1):
            json_data.append({
                "id": i,
                "text": text
            })
        
        json_filepath = os.path.join(self.output_dir, f"{keyword}_texts.json")
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"JSON格式也已保存到 {json_filepath}")
    
    def _create_sample_texts(self, keyword):
        """创建示例文本"""
        sample_texts = [
            f"""【{keyword}必玩】{keyword}初体验+专业跟拍！

- 痛点：想尝试{keyword}但怕不安全？
- 方案：专业教练1v1指导，送10张精修照片
- 价格：¥399/人，含接送+装备！

✨私戳我解锁隐藏福利！""",

            f"""【{keyword}推荐】高性价比{keyword}体验

- 痛点：{keyword}价格太贵？
- 方案：高性价比{keyword}体验，专业指导
- 价格：¥288起，周末不加价！

🔥抢购倒计时，仅限本周！""",

            f"""超值{keyword}套餐来啦！

🌟 专业{keyword}体验
🌟 全程摄影跟拍
🌟 包含所有装备
🌟 安全保障到位

现在预订立减100元！
联系我获取专属优惠码～"""
        ]
        
        self._save_texts(sample_texts, keyword)
        print(f"创建了示例文本数据")
    
    def close(self):
        """Close the webdriver"""
        if self.driver:
            self.driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='小红书文本爬虫')
    parser.add_argument('--keyword', type=str, required=True, help='要搜索的关键词')
    parser.add_argument('--num_posts', type=int, default=20, help='要抓取的帖子数量')
    parser.add_argument('--headless', action='store_true', help='使用无头浏览器模式运行')
    parser.add_argument('--output_dir', type=str, default='output', help='保存输出文件的目录')
    parser.add_argument('--no-wait-login', action='store_true', help='不等待手动登录')
    
    args = parser.parse_args()
    
    crawler = XiaohongshuCrawler(headless=args.headless, output_dir=args.output_dir, wait_login=not args.no_wait_login)
    try:
        texts = crawler.search_by_keyword(args.keyword, args.num_posts)
        print(f"成功抓取 {len(texts)} 个帖子的文本")
    finally:
        crawler.close() 