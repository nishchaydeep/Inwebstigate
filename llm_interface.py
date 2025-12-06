"""LLM interface supporting both Ollama and Groq."""

import json
import requests
from typing import Dict, List, Optional
from groq import Groq
from config import Config
from logger import setup_logger

logger = setup_logger('llm')


class LLMInterface:
    """Interface for interacting with LLMs (Ollama or Groq)."""
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM interface.
        
        Args:
            provider: LLM provider ('ollama' or 'groq'). Defaults to config value.
        """
        self.provider = provider or Config.LLM_PROVIDER
        logger.info(f"Initializing LLM interface with provider: {self.provider}")
        
        if self.provider == "groq":
            if not Config.GROQ_API_KEY:
                logger.error("Groq API key not found in environment variables")
                raise ValueError("Groq API key not found in environment variables")
            self.groq_client = Groq(api_key=Config.GROQ_API_KEY)
            self.model = Config.GROQ_MODEL
            logger.info(f"Groq client initialized with model: {self.model}")
        elif self.provider == "ollama":
            self.ollama_base_url = Config.OLLAMA_BASE_URL
            self.model = Config.OLLAMA_MODEL
            logger.info(f"Ollama configured at {self.ollama_base_url} with model: {self.model}")
        else:
            logger.error(f"Unknown LLM provider: {self.provider}")
            raise ValueError(f"Unknown LLM provider: {self.provider}")
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            
        Returns:
            LLM response as string
        """
        if self.provider == "groq":
            return self._generate_groq(prompt, system_prompt)
        else:
            return self._generate_ollama(prompt, system_prompt)
    
    def _generate_groq(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response using Groq API."""
        logger.debug(f"Generating response with Groq ({self.model})...")
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        try:
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            result = response.choices[0].message.content
            logger.debug(f"Groq response length: {len(result)} characters")
            return result
        except Exception as e:
            logger.error(f"Groq API error: {e}", exc_info=True)
            return f"Error generating response from Groq: {str(e)}"
    
    def _generate_ollama(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response using Ollama API."""
        logger.debug(f"Generating response with Ollama ({self.model})...")
        url = f"{self.ollama_base_url}/api/generate"
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 2000
            }
        }
        
        try:
            logger.debug(f"Sending request to Ollama at {url}")
            response = requests.post(url, json=payload, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            result = response.json()
            answer = result.get("response", "No response generated")
            logger.debug(f"Ollama response length: {len(answer)} characters")
            return answer
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to Ollama at {url}: {e}")
            return "Error: Cannot connect to Ollama. Make sure Ollama is running (run 'ollama serve' in terminal)"
        except Exception as e:
            logger.error(f"Ollama API error: {e}", exc_info=True)
            return f"Error generating response from Ollama: {str(e)}"
    
    def extract_info(self, query: str, page_content: str, page_url: str) -> str:
        """
        Extract relevant information from page content based on query.
        
        Args:
            query: User's search query
            page_content: Text content of the page
            page_url: URL of the page
            
        Returns:
            Extracted information as string
        """
        system_prompt = """You are an AI assistant helping to extract relevant information from web pages.
Your task is to analyze the page content and extract ONLY the information relevant to the user's query.
Be concise but thorough. 

IMPORTANT: If the page provides a COMPLETE ANSWER to the query, start your response with "SUFFICIENT:" 
If the page doesn't contain relevant information or only partial information, start with "PARTIAL:" or "NOT RELEVANT:"
This helps determine if we need to visit more pages."""
        
        prompt = f"""Query: {query}

Page URL: {page_url}

Page Content (first 8000 chars):
{page_content[:8000]}

Analyze the page content and:
1. Start with SUFFICIENT: if this page fully answers the query
2. Start with PARTIAL: if it has some relevant info but incomplete  
3. Start with NOT RELEVANT: if it's not related to the query
4. Then provide the extracted information or summary

Your response:"""
        
        return self.generate(prompt, system_prompt)
    
    def select_next_link(self, query: str, current_findings: str, links: List[Dict[str, str]], visited_urls: List[str], url_visit_count: Dict[str, int] = None) -> Dict[str, str]:
        """
        Select the most relevant link to visit next.
        
        Args:
            query: User's search query
            current_findings: Summary of findings so far
            links: List of available links with their text
            visited_urls: List of already visited URLs
            url_visit_count: Dictionary tracking how many times each URL was attempted
            
        Returns:
            Dictionary with 'url', 'reason', and 'should_stop' keys
        """
        logger.debug(f"Selecting next link from {len(links)} available links")
        logger.debug(f"Already visited {len(visited_urls)} URLs")
        
        # Filter out visited links and URLs we've tried multiple times
        unvisited_links = []
        for link in links:
            if link['url'] not in visited_urls:
                # Skip if we've already tried this URL twice
                if url_visit_count and link['url'] in url_visit_count and url_visit_count[link['url']] >= 2:
                    logger.debug(f"Skipping {link['url']} - already tried {url_visit_count[link['url']]} times")
                    continue
                unvisited_links.append(link)
        
        if not unvisited_links:
            logger.info("No unvisited links remaining")
            return {
                "url": None,
                "reason": "No more unvisited links available",
                "should_stop": True
            }
        
        # Limit number of links to avoid token limits
        links_sample = unvisited_links[:30]
        logger.debug(f"Considering {len(links_sample)} unvisited links")
        
        links_text = "\n".join([
            f"{i+1}. {link['text'][:100]} -> {link['url']}"
            for i, link in enumerate(links_sample)
        ])
        
        system_prompt = """You are an AI web navigation assistant. Your job is to:
1. Analyze the user's query and current findings
2. Choose the most promising link to visit next that will help answer the query
3. If the query has been sufficiently answered, recommend stopping

Respond in JSON format:
{
    "link_number": <number of the link to visit, or 0 to stop>,
    "reason": "<brief explanation of your choice>",
    "should_stop": <true or false>
}"""
        
        prompt = f"""Original Query: {query}

Current Findings:
{current_findings if current_findings else "No findings yet"}

Available Links:
{links_text}

Which link should we visit next to help answer the query? Or should we stop because we have enough information?
Respond ONLY with valid JSON."""
        
        response = self.generate(prompt, system_prompt)
        
        try:
            # Try to parse JSON from response
            # Sometimes LLM adds extra text, so extract JSON
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                decision = json.loads(json_str)
            else:
                decision = json.loads(response)
            
            link_num = decision.get("link_number", 0)
            reason = decision.get("reason", "No reason provided")
            should_stop = decision.get("should_stop", False)
            
            if should_stop or link_num == 0 or link_num > len(links_sample):
                return {
                    "url": None,
                    "reason": reason,
                    "should_stop": True
                }
            
            selected_link = links_sample[link_num - 1]
            return {
                "url": selected_link["url"],
                "reason": reason,
                "should_stop": False
            }
            
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            # Fallback: select first link if parsing fails
            if unvisited_links:
                return {
                    "url": unvisited_links[0]["url"],
                    "reason": f"Fallback selection due to parsing error: {str(e)}",
                    "should_stop": False
                }
            return {
                "url": None,
                "reason": "Failed to parse LLM decision and no fallback available",
                "should_stop": True
            }
    
    def generate_final_answer(self, query: str, investigation_log: List[Dict]) -> str:
        """
        Generate final answer based on all collected information.
        
        Args:
            query: Original user query
            investigation_log: List of visited pages and findings
            
        Returns:
            Final comprehensive answer
        """
        system_prompt = """You are an AI research assistant. You have investigated multiple web pages to answer a user's query.
Now provide a comprehensive, well-structured answer based on all the information gathered.
Include relevant details and cite the sources (URLs) where appropriate."""
        
        # Build investigation summary
        investigation_summary = "\n\n".join([
            f"Page {i+1}: {page['url']}\nTitle: {page.get('title', 'N/A')}\nFindings: {page.get('findings', 'N/A')}"
            for i, page in enumerate(investigation_log)
        ])
        
        prompt = f"""Original Query: {query}

Investigation Results:
{investigation_summary}

Based on all the information gathered from the above sources, provide a comprehensive answer to the query.
Structure your answer clearly and cite sources where appropriate."""
        
        return self.generate(prompt, system_prompt)

