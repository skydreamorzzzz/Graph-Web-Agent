"""
Browser Environment - 浏览器环境抽象层
"""
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class BrowserEnvironment(ABC):
    """浏览器环境抽象基类"""
    
    @abstractmethod
    def navigate(self, url: str) -> None:
        """导航到URL"""
        pass
    
    @abstractmethod
    def get_url(self) -> str:
        """获取当前URL"""
        pass
    
    @abstractmethod
    def get_title(self) -> str:
        """获取页面标题"""
        pass
    
    @abstractmethod
    def get_text_content(self) -> str:
        """获取页面文本内容"""
        pass
    
    @abstractmethod
    def collect_elements(self, selector: str) -> List[Any]:
        """收集元素"""
        pass
    
    @abstractmethod
    def extract_data(self, fields: List[Dict]) -> Dict[str, Any]:
        """提取数据"""
        pass
    
    @abstractmethod
    def click(self, selector: str, timeout: int = 5000) -> bool:
        """点击元素"""
        pass
    
    @abstractmethod
    def type_text(self, selector: str, text: str) -> None:
        """输入文本"""
        pass
    
    @abstractmethod
    def submit(self, selector: str) -> None:
        """提交表单"""
        pass
    
    @abstractmethod
    def wait_for_load_state(self, timeout: int = 10000) -> None:
        """等待页面加载完成"""
        pass
    
    @abstractmethod
    def wait(self, milliseconds: int) -> None:
        """等待指定时间"""
        pass
    
    @abstractmethod
    def refresh(self) -> None:
        """刷新页面"""
        pass
    
    @abstractmethod
    def press_key(self, key: str) -> None:
        """按键"""
        pass
    
    @abstractmethod
    def scroll_to_bottom(self) -> None:
        """滚动到底部"""
        pass
    
    @abstractmethod
    def get_cookies(self) -> List[Dict]:
        """获取cookies"""
        pass
    
    @abstractmethod
    def set_cookie(self, cookie: Dict) -> None:
        """设置cookie"""
        pass
    
    @abstractmethod
    def clear_cookies(self) -> None:
        """清除cookies"""
        pass
    
    @abstractmethod
    def get_local_storage(self) -> Dict:
        """获取localStorage"""
        pass
    
    @abstractmethod
    def clear_local_storage(self) -> None:
        """清除localStorage"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """关闭浏览器"""
        pass


class PlaywrightBrowser(BrowserEnvironment):
    """基于Playwright的浏览器实现"""
    
    def __init__(self, headless: bool = False):
        """
        Args:
            headless: 是否无头模式
        """
        self.headless = headless
        self.browser = None
        self.page = None
        self._init_browser()
    
    def _init_browser(self) -> None:
        """初始化浏览器"""
        try:
            from playwright.sync_api import sync_playwright
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.page = self.browser.new_page()
        except ImportError:
            print("警告: Playwright未安装，请运行: pip install playwright && playwright install")
            # 创建模拟对象用于测试
            self.page = MockPage()
    
    def navigate(self, url: str) -> None:
        if self.page:
            self.page.goto(url, wait_until="domcontentloaded")
    
    def get_url(self) -> str:
        return self.page.url if self.page else ""
    
    def get_title(self) -> str:
        return self.page.title() if self.page else ""
    
    def get_text_content(self) -> str:
        if self.page:
            return self.page.inner_text("body")
        return ""
    
    def collect_elements(self, selector: str) -> List[Any]:
        if self.page:
            elements = self.page.query_selector_all(selector)
            return elements
        return []
    
    def extract_data(self, fields: List[Dict]) -> Dict[str, Any]:
        data = {}
        if not self.page:
            return data
            
        for field in fields:
            if isinstance(field, dict):
                field_name = field.get("name")
                field_selector = field.get("selector")
                if field_selector:
                    try:
                        element = self.page.query_selector(field_selector)
                        if element:
                            data[field_name] = element.inner_text()
                    except Exception:
                        pass
        return data
    
    def click(self, selector: str, timeout: int = 5000) -> bool:
        if self.page:
            try:
                self.page.click(selector, timeout=timeout)
                return True
            except Exception:
                return False
        return False
    
    def type_text(self, selector: str, text: str) -> None:
        if self.page:
            self.page.fill(selector, text)
    
    def submit(self, selector: str) -> None:
        if self.page:
            self.page.press(selector, "Enter")
    
    def wait_for_load_state(self, timeout: int = 10000) -> None:
        if self.page:
            self.page.wait_for_load_state("networkidle", timeout=timeout)
    
    def wait(self, milliseconds: int) -> None:
        if self.page:
            self.page.wait_for_timeout(milliseconds)
    
    def refresh(self) -> None:
        if self.page:
            self.page.reload()
    
    def press_key(self, key: str) -> None:
        if self.page:
            self.page.keyboard.press(key)
    
    def scroll_to_bottom(self) -> None:
        if self.page:
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    
    def get_cookies(self) -> List[Dict]:
        if self.page:
            return self.page.context.cookies()
        return []
    
    def set_cookie(self, cookie: Dict) -> None:
        if self.page:
            self.page.context.add_cookies([cookie])
    
    def clear_cookies(self) -> None:
        if self.page:
            self.page.context.clear_cookies()
    
    def get_local_storage(self) -> Dict:
        if self.page:
            return self.page.evaluate("() => Object.assign({}, window.localStorage)")
        return {}
    
    def clear_local_storage(self) -> None:
        if self.page:
            self.page.evaluate("() => window.localStorage.clear()")
    
    def close(self) -> None:
        if self.browser:
            self.browser.close()
        if hasattr(self, 'playwright'):
            self.playwright.stop()


class MockPage:
    """模拟页面对象（用于测试）"""
    
    def __init__(self):
        self.url = "http://example.com"
        self._title = "Example Page"
        
    def goto(self, url: str, **kwargs) -> None:
        self.url = url
        
    def title(self) -> str:
        return self._title
        
    def inner_text(self, selector: str) -> str:
        return "Mock page content"
        
    def query_selector_all(self, selector: str) -> List:
        return []
        
    def query_selector(self, selector: str):
        return None
        
    def click(self, selector: str, **kwargs) -> None:
        pass
        
    def fill(self, selector: str, text: str) -> None:
        pass
        
    def press(self, selector: str, key: str) -> None:
        pass
        
    def wait_for_load_state(self, state: str, **kwargs) -> None:
        pass
        
    def wait_for_timeout(self, timeout: int) -> None:
        import time
        time.sleep(timeout / 1000)
        
    def reload(self) -> None:
        pass
        
    @property
    def keyboard(self):
        return self
        
    def press(self, key: str) -> None:
        pass
        
    def evaluate(self, script: str):
        return {}
        
    @property
    def context(self):
        return self
        
    def cookies(self) -> List:
        return []
        
    def add_cookies(self, cookies: List) -> None:
        pass
        
    def clear_cookies(self) -> None:
        pass


