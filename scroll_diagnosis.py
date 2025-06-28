import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import argparse

class ScrollDiagnostic:
    def __init__(self):
        # 设置Chrome选项
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.set_window_size(1920, 1080)
        
    def analyze_page_structure(self):
        """深度分析页面结构和滚动行为"""
        print("🔬 开始深度页面结构分析...")
        
        # 记录页面的详细信息
        analysis_data = {
            'initial_state': {},
            'scroll_tests': [],
            'element_tracking': {},
            'network_activity': []
        }
        
        # 1. 记录初始状态
        initial_height = self.driver.execute_script("return document.body.scrollHeight")
        initial_cards = self.get_all_possible_cards()
        
        analysis_data['initial_state'] = {
            'page_height': initial_height,
            'card_count': len(initial_cards),
            'viewport_height': self.driver.execute_script("return window.innerHeight"),
            'scroll_position': self.driver.execute_script("return window.pageYOffset")
        }
        
        print(f"📊 初始状态:")
        print(f"  页面高度: {initial_height}px")
        print(f"  卡片数量: {len(initial_cards)}")
        print(f"  视窗高度: {analysis_data['initial_state']['viewport_height']}px")
        
        # 2. 测试不同的滚动策略
        scroll_strategies = [
            ("慢速连续滚动", self.slow_continuous_scroll),
            ("快速跳跃滚动", self.fast_jump_scroll),
            ("模拟真实用户滚动", self.realistic_user_scroll),
            ("触底回弹滚动", self.bottom_bounce_scroll),
            ("随机位置滚动", self.random_position_scroll)
        ]
        
        for strategy_name, strategy_func in scroll_strategies:
            print(f"\n🧪 测试策略: {strategy_name}")
            
            # 重置到顶部
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # 执行策略
            result = strategy_func()
            analysis_data['scroll_tests'].append({
                'strategy': strategy_name,
                'result': result
            })
            
            print(f"  结果: {result}")
        
        # 3. 分析DOM变化模式
        print(f"\n🔍 分析DOM变化模式...")
        self.analyze_dom_changes()
        
        # 4. 检测网络请求模式
        print(f"\n🌐 检测可能的网络请求...")
        self.detect_network_patterns()
        
        return analysis_data
    
    def get_all_possible_cards(self):
        """获取所有可能的卡片元素"""
        selectors = [
            "section.note-item",
            "div.note-item",
            "div[class*='note-item']",
            "div[class*='card']",
            "div[class*='item']",
            "a[href*='/explore/']",
            "[data-testid*='note']",
            "[data-testid*='card']",
            "[data-testid*='item']"
        ]
        
        all_cards = []
        for selector in selectors:
            try:
                cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for card in cards:
                    # 检查是否是有效的帖子卡片
                    if self.is_valid_post_card(card):
                        all_cards.append(card)
            except:
                continue
        
        # 去重
        unique_cards = []
        seen_elements = set()
        for card in all_cards:
            try:
                element_id = card.get_attribute('outerHTML')[:100]  # 使用HTML片段作为唯一标识
                if element_id not in seen_elements:
                    seen_elements.add(element_id)
                    unique_cards.append(card)
            except:
                continue
        
        return unique_cards
    
    def is_valid_post_card(self, element):
        """判断元素是否是有效的帖子卡片"""
        try:
            # 检查是否有文本内容
            text = element.text.strip()
            if not text or len(text) < 10:
                return False
            
            # 检查是否包含链接或可点击
            href = element.get_attribute('href')
            if href and ('explore' in href or 'discovery' in href):
                return True
            
            # 检查子元素中是否有链接
            links = element.find_elements(By.TAG_NAME, 'a')
            for link in links:
                href = link.get_attribute('href')
                if href and ('explore' in href or 'discovery' in href):
                    return True
            
            return False
        except:
            return False
    
    def slow_continuous_scroll(self):
        """慢速连续滚动"""
        initial_cards = len(self.get_all_possible_cards())
        
        # 慢速滚动，每次100px
        for i in range(50):
            self.driver.execute_script("window.scrollBy(0, 100);")
            time.sleep(0.5)
            
            # 每10次检查一下卡片数量
            if i % 10 == 0:
                current_cards = len(self.get_all_possible_cards())
                if current_cards > initial_cards:
                    return f"成功! 卡片数量: {initial_cards} -> {current_cards} (滚动{i+1}次后)"
        
        final_cards = len(self.get_all_possible_cards())
        return f"完成. 卡片数量: {initial_cards} -> {final_cards}"
    
    def fast_jump_scroll(self):
        """快速跳跃滚动"""
        initial_cards = len(self.get_all_possible_cards())
        
        # 快速跳跃到不同位置
        positions = [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
        for pos in positions:
            script = f"window.scrollTo(0, document.body.scrollHeight * {pos});"
            self.driver.execute_script(script)
            time.sleep(2)
            
            current_cards = len(self.get_all_possible_cards())
            if current_cards > initial_cards:
                return f"成功! 卡片数量: {initial_cards} -> {current_cards} (位置{pos*100:.0f}%)"
        
        final_cards = len(self.get_all_possible_cards())
        return f"完成. 卡片数量: {initial_cards} -> {final_cards}"
    
    def realistic_user_scroll(self):
        """模拟真实用户滚动行为"""
        initial_cards = len(self.get_all_possible_cards())
        
        actions = ActionChains(self.driver)
        
        # 模拟真实用户行为：滚动 + 停顿 + 鼠标移动
        for i in range(20):
            # 随机滚动距离
            scroll_distance = 200 + (i * 150)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
            
            # 模拟用户停顿阅读
            time.sleep(1.5 + (i * 0.2))
            
            # 模拟鼠标移动
            try:
                cards = self.get_all_possible_cards()
                if cards and len(cards) > i:
                    actions.move_to_element(cards[min(i, len(cards)-1)]).perform()
                    time.sleep(0.5)
            except:
                pass
            
            # 检查是否有新卡片
            current_cards = len(self.get_all_possible_cards())
            if current_cards > initial_cards:
                return f"成功! 卡片数量: {initial_cards} -> {current_cards} (第{i+1}轮真实滚动)"
        
        final_cards = len(self.get_all_possible_cards())
        return f"完成. 卡片数量: {initial_cards} -> {final_cards}"
    
    def bottom_bounce_scroll(self):
        """触底回弹滚动"""
        initial_cards = len(self.get_all_possible_cards())
        
        for i in range(10):
            # 滚动到底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # 回弹一点
            self.driver.execute_script("window.scrollBy(0, -300);")
            time.sleep(1)
            
            # 再次到底部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            current_cards = len(self.get_all_possible_cards())
            if current_cards > initial_cards:
                return f"成功! 卡片数量: {initial_cards} -> {current_cards} (第{i+1}次触底回弹)"
        
        final_cards = len(self.get_all_possible_cards())
        return f"完成. 卡片数量: {initial_cards} -> {final_cards}"
    
    def random_position_scroll(self):
        """随机位置滚动"""
        initial_cards = len(self.get_all_possible_cards())
        
        import random
        
        for i in range(15):
            # 随机滚动到某个位置
            random_pos = random.uniform(0.1, 1.0)
            script = f"window.scrollTo(0, document.body.scrollHeight * {random_pos});"
            self.driver.execute_script(script)
            time.sleep(2)
            
            # 随机小幅滚动
            for j in range(3):
                direction = random.choice([-1, 1])
                distance = random.randint(100, 500)
                self.driver.execute_script(f"window.scrollBy(0, {direction * distance});")
                time.sleep(1)
            
            current_cards = len(self.get_all_possible_cards())
            if current_cards > initial_cards:
                return f"成功! 卡片数量: {initial_cards} -> {current_cards} (第{i+1}次随机滚动)"
        
        final_cards = len(self.get_all_possible_cards())
        return f"完成. 卡片数量: {initial_cards} -> {final_cards}"
    
    def analyze_dom_changes(self):
        """分析DOM变化模式"""
        print("  监控DOM变化...")
        
        # 注入DOM监控脚本
        monitor_script = """
        window.domChanges = [];
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    window.domChanges.push({
                        type: 'childList',
                        addedNodes: mutation.addedNodes.length,
                        removedNodes: mutation.removedNodes.length,
                        target: mutation.target.tagName,
                        timestamp: Date.now()
                    });
                }
            });
        });
        observer.observe(document.body, { childList: true, subtree: true });
        """
        
        self.driver.execute_script(monitor_script)
        
        # 执行一些滚动操作
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        
        # 获取DOM变化记录
        changes = self.driver.execute_script("return window.domChanges;")
        print(f"  检测到 {len(changes)} 次DOM变化")
        
        if changes:
            print("  最近的变化:")
            for change in changes[-5:]:  # 显示最近5次变化
                print(f"    {change}")
    
    def detect_network_patterns(self):
        """检测网络请求模式"""
        print("  分析可能的AJAX请求...")
        
        # 注入网络监控脚本
        network_script = """
        window.networkRequests = [];
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            window.networkRequests.push({
                url: args[0],
                timestamp: Date.now(),
                type: 'fetch'
            });
            return originalFetch.apply(this, args);
        };
        
        const originalXHR = window.XMLHttpRequest;
        window.XMLHttpRequest = function() {
            const xhr = new originalXHR();
            const originalOpen = xhr.open;
            xhr.open = function(method, url) {
                window.networkRequests.push({
                    url: url,
                    method: method,
                    timestamp: Date.now(),
                    type: 'xhr'
                });
                return originalOpen.apply(this, arguments);
            };
            return xhr;
        };
        """
        
        self.driver.execute_script(network_script)
        
        # 执行滚动并监控网络请求
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        
        # 获取网络请求记录
        requests = self.driver.execute_script("return window.networkRequests;")
        print(f"  检测到 {len(requests)} 个网络请求")
        
        if requests:
            print("  相关请求:")
            for req in requests[-3:]:  # 显示最近3个请求
                print(f"    {req}")
    
    def run_diagnosis(self, keyword):
        """运行完整诊断"""
        print(f"🚀 开始诊断小红书滚动机制 - 关键词: {keyword}")
        
        # 访问搜索页面
        search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}&type=51"
        print(f"访问: {search_url}")
        self.driver.get(search_url)
        
        # 等待页面加载
        time.sleep(8)
        
        print("请手动登录小红书，然后按回车继续...")
        input("登录完成后按回车...")
        
        # 开始分析
        analysis_data = self.analyze_page_structure()
        
        # 保存分析结果
        with open(f'scroll_diagnosis_{keyword}.json', 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📋 诊断完成！结果已保存到 scroll_diagnosis_{keyword}.json")
        
        return analysis_data
    
    def close(self):
        """关闭浏览器"""
        self.driver.quit()

def main():
    parser = argparse.ArgumentParser(description='小红书滚动机制诊断工具')
    parser.add_argument('--keyword', type=str, default='亲子旅游', help='搜索关键词')
    
    args = parser.parse_args()
    
    diagnostic = ScrollDiagnostic()
    
    try:
        result = diagnostic.run_diagnosis(args.keyword)
        print("\n🎯 诊断总结:")
        print(f"初始卡片数: {result['initial_state']['card_count']}")
        print("滚动策略测试结果:")
        for test in result['scroll_tests']:
            print(f"  {test['strategy']}: {test['result']}")
            
    except KeyboardInterrupt:
        print("\n用户中断诊断")
    except Exception as e:
        print(f"诊断过程中出错: {e}")
    finally:
        diagnostic.close()

if __name__ == "__main__":
    main() 