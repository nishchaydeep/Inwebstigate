"""AI Web Investigation Agent."""

from typing import List, Dict, Optional, Callable
from scraper import WebScraper
from llm_interface import LLMInterface
from config import Config
from logger import setup_logger
import time

logger = setup_logger('agent')


class WebInvestigationAgent:
    """AI agent that navigates the web to answer queries."""
    
    def __init__(self, llm_provider: Optional[str] = None, callback: Optional[Callable] = None):
        """
        Initialize the investigation agent.
        
        Args:
            llm_provider: LLM provider to use ('ollama' or 'groq')
            callback: Optional callback function for progress updates
        """
        logger.info(f"Initializing WebInvestigationAgent with LLM provider: {llm_provider or Config.LLM_PROVIDER}")
        self.scraper = WebScraper()
        self.llm = LLMInterface(llm_provider)
        self.callback = callback
        self.investigation_log = []
        self.visited_urls = set()
        self.should_stop = False  # Flag to stop investigation
        self.url_visit_count = {}  # Track how many times we've tried each URL
        logger.info("Agent initialized successfully")
        
    def _update_progress(self, message: str, data: Optional[Dict] = None):
        """Send progress update via callback."""
        if self.callback:
            self.callback(message, data)
    
    def investigate(self, query: str, start_url: Optional[str] = None, max_depth: Optional[int] = None) -> str:
        """
        Investigate a query by navigating through web pages.
        
        Args:
            query: The user's question/query
            start_url: Optional starting URL. If not provided, will use a search engine
            max_depth: Maximum number of pages to visit
            
        Returns:
            Final answer to the query
        """
        logger.info(f"Starting investigation for query: '{query}'")
        logger.info(f"Max depth: {max_depth or Config.MAX_NAVIGATION_DEPTH}")
        
        if max_depth is None:
            max_depth = Config.MAX_NAVIGATION_DEPTH
        
        # Reset state for new investigation
        self.investigation_log = []
        self.visited_urls = set()
        self.should_stop = False
        self.url_visit_count = {}
        logger.info("Investigation state reset")
        
        # Determine starting URL
        if not start_url:
            logger.info("No starting URL provided, using DuckDuckGo search")
            # Use DuckDuckGo as default search starting point
            import urllib.parse
            search_query = urllib.parse.quote(query)
            start_url = f"https://duckduckgo.com/html/?q={search_query}"
            self._update_progress(f"🔍 Starting investigation with DuckDuckGo search: {query}")
        else:
            self._update_progress(f"🔍 Starting investigation from: {start_url}")
        
        current_url = start_url
        depth = 0
        
        while current_url and depth < max_depth and not self.should_stop:
            # Check if we've exceeded max depth
            if depth >= max_depth:
                logger.warning(f"Reached max depth ({max_depth}). Stopping investigation.")
                self._update_progress(f"🛑 Reached maximum pages limit ({max_depth}). Generating summary...", {
                    "type": "stop",
                    "reason": f"Reached maximum depth of {max_depth} pages"
                })
                break
            
            # Check if we've been stuck on this URL
            if current_url in self.url_visit_count:
                self.url_visit_count[current_url] += 1
                if self.url_visit_count[current_url] > 2:
                    logger.error(f"Stuck on URL {current_url} - attempted {self.url_visit_count[current_url]} times")
                    self._update_progress(f"⚠️ Detected loop on {current_url}, stopping to prevent infinite loop", {
                        "type": "error",
                        "url": current_url,
                        "error": f"Attempted to visit same URL {self.url_visit_count[current_url]} times"
                    })
                    break
            else:
                self.url_visit_count[current_url] = 1
            
            logger.info(f"[Depth {depth + 1}/{max_depth}] Navigating to: {current_url}")
            self._update_progress(f"\n📍 Navigating to: {current_url}", {
                "type": "navigation",
                "url": current_url,
                "depth": depth + 1,
                "max_depth": max_depth
            })
            
            # Scrape the page
            logger.debug("Calling scraper...")
            page_data = self.scraper.scrape_page(current_url)
            
            if not page_data["success"]:
                logger.error(f"Failed to scrape page: {page_data['error']}")
                self._update_progress(f"❌ Error scraping page: {page_data['error']}", {
                    "type": "error",
                    "url": current_url,
                    "error": page_data['error']
                })
                
                # Try to continue with next link if available
                if self.investigation_log:
                    last_page = self.investigation_log[-1]
                    if last_page.get('links'):
                        # Find next unvisited link
                        for link in last_page['links']:
                            if link['url'] not in self.visited_urls:
                                current_url = link['url']
                                break
                        else:
                            current_url = None
                    else:
                        current_url = None
                else:
                    break
                continue
            
            self.visited_urls.add(current_url)
            
            self._update_progress(f"✅ Page loaded: {page_data['title']}", {
                "type": "page_loaded",
                "url": current_url,
                "title": page_data['title'],
                "links_found": len(page_data['links'])
            })
            
            # Extract relevant information using LLM
            self._update_progress("🤖 Analyzing page content with AI...", {
                "type": "analyzing"
            })
            
            # Pass should_stop flag to LLM
            findings = self.llm.extract_info(
                query=query,
                page_content=page_data['text_content'],
                page_url=current_url
            )
            
            logger.debug(f"Findings length: {len(findings)} characters")
            self._update_progress(f"📝 Findings: {findings[:200]}...", {
                "type": "findings",
                "url": current_url,
                "findings": findings
            })
            
            # Check if the LLM indicates the answer is complete
            if findings.startswith("SUFFICIENT:"):
                logger.info("✅ LLM indicates answer is sufficient on this page")
                self._update_progress("✅ Found sufficient information to answer query", {
                    "type": "stop",
                    "reason": "Sufficient information found on current page"
                })
                # Add this page to log and break
                page_log = {
                    "url": current_url,
                    "title": page_data['title'],
                    "meta_description": page_data['meta_description'],
                    "findings": findings.replace("SUFFICIENT:", "").strip(),
                    "links": page_data['links'],
                    "depth": depth
                }
                self.investigation_log.append(page_log)
                logger.info("Stopping investigation - sufficient information found")
                break
            
            # Log this page
            page_log = {
                "url": current_url,
                "title": page_data['title'],
                "meta_description": page_data['meta_description'],
                "findings": findings,
                "links": page_data['links'],
                "depth": depth
            }
            self.investigation_log.append(page_log)
            
            # Decide next step using LLM
            self._update_progress("🤔 Deciding next navigation step...", {
                "type": "deciding"
            })
            
            current_findings = "\n\n".join([
                f"From {log['url']}: {log['findings']}"
                for log in self.investigation_log
            ])
            
            decision = self.llm.select_next_link(
                query=query,
                current_findings=current_findings,
                links=page_data['links'],
                visited_urls=list(self.visited_urls),
                url_visit_count=self.url_visit_count
            )
            
            if decision['should_stop'] or not decision['url']:
                self._update_progress(f"🛑 Stopping navigation: {decision['reason']}", {
                    "type": "stop",
                    "reason": decision['reason']
                })
                break
            
            self._update_progress(f"➡️  Next: {decision['url']}\n💡 Reason: {decision['reason']}", {
                "type": "next_link",
                "url": decision['url'],
                "reason": decision['reason']
            })
            
            current_url = decision['url']
            depth += 1
            
            # Small delay to be respectful to servers
            time.sleep(1)
        
        # Generate final answer
        self._update_progress("\n📊 Generating final answer...", {
            "type": "final_answer"
        })
        
        final_answer = self.llm.generate_final_answer(query, self.investigation_log)
        
        self._update_progress(f"\n✨ Investigation complete!", {
            "type": "complete",
            "pages_visited": len(self.investigation_log)
        })
        
        return final_answer
    
    def get_investigation_summary(self) -> Dict:
        """
        Get a summary of the investigation.
        
        Returns:
            Dictionary with investigation statistics and log
        """
        return {
            "total_pages_visited": len(self.investigation_log),
            "urls_visited": list(self.visited_urls),
            "investigation_log": self.investigation_log
        }
    
    def stop(self):
        """Stop the current investigation gracefully."""
        logger.warning("Stop requested - setting stop flag")
        self.should_stop = True
    
    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up agent resources")
        self.should_stop = True
        if self.scraper:
            self.scraper.close()

