"""
Playwright service for scanning web pages and extracting accessibility-related content.
"""
import asyncio
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from datetime import datetime
import base64


class PlaywrightScanner:
    """Service for scanning web pages using Playwright."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
    
    async def start(self):
        """Initialize Playwright browser."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 AccessibilityBot/1.0'
        )
    
    async def stop(self):
        """Close Playwright browser."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    async def scan_page(self, url: str, wait_time: int = 3000) -> Dict[str, Any]:
        """
        Scan a webpage and extract HTML, screenshots, and accessibility tree.
        
        Args:
            url: The URL to scan
            wait_time: Time to wait for dynamic content (ms)
            
        Returns:
            Dictionary with html_content, screenshots, aria_tree, metadata
        """
        if not self.context:
            await self.start()
        
        page = await self.context.new_page()
        
        try:
            # Navigate to page
            response = await page.goto(url, wait_until='networkidle', timeout=30000)
            
            if not response:
                raise Exception(f"Failed to load {url}")
            
            # Wait for dynamic content
            await page.wait_for_timeout(wait_time)
            
            # Get full HTML
            html_content = await page.content()
            
            # Take screenshot
            screenshot = await page.screenshot(full_page=True, type='png')
            screenshot_base64 = base64.b64encode(screenshot).decode('utf-8')
            
            # Extract accessibility tree
            aria_tree = await self._extract_accessibility_tree(page)
            
            # Extract ARIA labels and roles
            aria_info = await self._extract_aria_info(page)
            
            # Check for common accessibility issues
            quick_issues = await self._detect_quick_issues(page)
            
            # Get page metadata
            metadata = await page.evaluate('''() => {
                return {
                    title: document.title,
                    url: window.location.href,
                    lang: document.documentElement.lang,
                    hasSkipLink: !!document.querySelector('a[href="#main"], a[href="#content"], .skip-link'),
                    hasMainLandmark: !!document.querySelector('main, [role="main"]'),
                    hasNavLandmark: !!document.querySelector('nav, [role="navigation"]'),
                    hasHeaderLandmark: !!document.querySelector('header, [role="banner"]'),
                    hasFooterLandmark: !!document.querySelector('footer, [role="contentinfo"]'),
                    imageCount: document.images.length,
                    linkCount: document.links.length,
                    formCount: document.forms.length,
                    headingCount: document.querySelectorAll('h1, h2, h3, h4, h5, h6').length,
                    timestamp: new Date().toISOString()
                }
            }''')
            
            return {
                'url': url,
                'html_content': html_content,
                'screenshot': screenshot_base64,
                'aria_tree': aria_tree,
                'aria_info': aria_info,
                'quick_issues': quick_issues,
                'metadata': metadata,
                'status_code': response.status,
                'scanned_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'scanned_at': datetime.utcnow().isoformat()
            }
        finally:
            await page.close()
    
    async def _extract_accessibility_tree(self, page: Page) -> List[Dict[str, Any]]:
        """Extract the accessibility tree from the page."""
        return await page.evaluate('''() => {
            function getNodeInfo(node) {
                if (node.nodeType !== Node.ELEMENT_NODE) return null;
                
                const rect = node.getBoundingClientRect();
                if (rect.width === 0 && rect.height === 0) return null;
                
                return {
                    tagName: node.tagName.toLowerCase(),
                    id: node.id || null,
                    className: node.className || null,
                    role: node.getAttribute('role') || null,
                    ariaLabel: node.getAttribute('aria-label') || null,
                    ariaLabelledby: node.getAttribute('aria-labelledby') || null,
                    ariaDescribedby: node.getAttribute('aria-describedby') || null,
                    ariaHidden: node.getAttribute('aria-hidden'),
                    tabIndex: node.tabIndex,
                    text: node.innerText?.substring(0, 100) || null,
                    children: []
                };
            }
            
            function buildTree(node, maxDepth = 3, currentDepth = 0) {
                if (currentDepth >= maxDepth) return [];
                
                const result = [];
                for (const child of node.children) {
                    const info = getNodeInfo(child);
                    if (info) {
                        info.children = buildTree(child, maxDepth, currentDepth + 1);
                        result.push(info);
                    }
                }
                return result;
            }
            
            return buildTree(document.body);
        }''')
    
    async def _extract_aria_info(self, page: Page) -> Dict[str, Any]:
        """Extract detailed ARIA information from the page."""
        return await page.evaluate('''() => {
            const elementsWithAria = document.querySelectorAll('[aria-label], [aria-labelledby], [aria-describedby], [role], [aria-hidden]');
            const landmarks = document.querySelectorAll('main, nav, header, footer, aside, section[aria-label], [role="main"], [role="navigation"], [role="banner"], [role="contentinfo"], [role="complementary"]');
            const images = document.querySelectorAll('img');
            const links = document.querySelectorAll('a');
            const buttons = document.querySelectorAll('button, [role="button"]');
            const forms = document.querySelectorAll('form');
            const inputs = document.querySelectorAll('input, select, textarea');
            
            return {
                ariaElementsCount: elementsWithAria.length,
                landmarksCount: landmarks.length,
                imagesWithoutAlt: Array.from(images).filter(img => !img.alt && !img.getAttribute('aria-label') && !img.getAttribute('aria-hidden')).length,
                linksWithoutText: Array.from(links).filter(link => !link.innerText.trim() && !link.getAttribute('aria-label')).length,
                buttonsWithoutAccessibleName: Array.from(buttons).filter(btn => !btn.innerText.trim() && !btn.getAttribute('aria-label')).length,
                inputsWithoutLabels: Array.from(inputs).filter(input => {
                    if (input.type === 'hidden' || input.type === 'submit') return false;
                    const id = input.id;
                    const label = id ? document.querySelector(`label[for="${id}"]`) : input.closest('label');
                    return !label && !input.getAttribute('aria-label') && !input.getAttribute('aria-labelledby');
                }).length,
                totalImages: images.length,
                totalLinks: links.length,
                totalButtons: buttons.length,
                totalForms: forms.length,
                totalInputs: inputs.length
            };
        }''')
    
    async def _detect_quick_issues(self, page: Page) -> List[Dict[str, Any]]:
        """Detect common accessibility issues quickly."""
        issues = await page.evaluate('''() => {
            const issues = [];
            
            // Missing lang attribute
            if (!document.documentElement.lang) {
                issues.push({
                    type: 'missing_lang',
                    severity: 'serious',
                    element: 'html',
                    message: 'HTML element is missing lang attribute',
                    wcag: '3.1.1'
                });
            }
            
            // Missing or multiple h1
            const h1s = document.querySelectorAll('h1');
            if (h1s.length === 0) {
                issues.push({
                    type: 'missing_h1',
                    severity: 'serious',
                    element: 'h1',
                    message: 'Page is missing h1 heading',
                    wcag: '1.3.1'
                });
            } else if (h1s.length > 1) {
                issues.push({
                    type: 'multiple_h1',
                    severity: 'moderate',
                    element: 'h1',
                    message: `Page has ${h1s.length} h1 headings (should have only one)`,
                    wcag: '1.3.1'
                });
            }
            
            // Images without alt
            const images = document.querySelectorAll('img:not([alt])');
            images.forEach((img, index) => {
                if (index < 10) { // Limit to first 10
                    issues.push({
                        type: 'missing_alt',
                        severity: 'critical',
                        element: 'img',
                        src: img.src.substring(0, 100),
                        message: 'Image is missing alt attribute',
                        wcag: '1.1.1'
                    });
                }
            });
            
            // Links without text
            const links = document.querySelectorAll('a:not([href]), a[href=""], a[href="#"]');
            links.forEach((link, index) => {
                if (index < 10 && !link.innerText.trim() && !link.getAttribute('aria-label')) {
                    issues.push({
                        type: 'empty_link',
                        severity: 'serious',
                        element: 'a',
                        message: 'Link has no accessible name',
                        wcag: '2.4.4'
                    });
                }
            });
            
            // Form inputs without labels
            const inputs = document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"])');
            inputs.forEach((input, index) => {
                if (index < 10) {
                    const id = input.id;
                    const label = id ? document.querySelector(`label[for="${id}"]`) : input.closest('label');
                    if (!label && !input.getAttribute('aria-label') && !input.getAttribute('aria-labelledby')) {
                        issues.push({
                            type: 'unlabeled_input',
                            severity: 'critical',
                            element: `input[type="${input.type}"]`,
                            message: 'Form input is missing label',
                            wcag: '1.3.1'
                        });
                    }
                }
            });
            
            // Low contrast (basic check - would need more sophisticated analysis)
            // This is a placeholder for more advanced contrast checking
            
            return issues;
        }''')
        
        return issues
    
    async def compare_pages(self, url1: str, url2: str) -> Dict[str, Any]:
        """Compare two versions of a page for accessibility changes."""
        scan1 = await self.scan_page(url1)
        scan2 = await self.scan_page(url2)
        
        if 'error' in scan1 or 'error' in scan2:
            return {'error': 'One or both scans failed'}
        
        # Compare metadata
        changes = {
            'url1': url1,
            'url2': url2,
            'metadata_changes': {},
            'aria_changes': {},
            'issues_added': [],
            'issues_fixed': [],
            'compared_at': datetime.utcnow().isoformat()
        }
        
        # Simple comparison logic (can be enhanced)
        if scan1['metadata'] != scan2['metadata']:
            changes['metadata_changes'] = {
                'before': scan1['metadata'],
                'after': scan2['metadata']
            }
        
        return changes
