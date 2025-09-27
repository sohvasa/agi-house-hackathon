import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
import requests
import json

load_dotenv()

class PerplexityAgent:
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def chat(self, 
             query: str, 
             model: str = "sonar-pro", 
             search_domain_filter: Optional[List[str]] = None,
             return_citations: bool = True,
             return_related_questions: bool = False,
             temperature: float = 0.2,
             top_p: float = 0.9,
             max_tokens: int = 1024) -> Dict[str, Any]:
        """
        Send a chat completion request to Perplexity API with online search capabilities.
        
        Args:
            query: The user's question or prompt
            model: Model to use (default: sonar-pro, options: sonar, sonar-pro)
            search_domain_filter: List of domains to search within
            return_citations: Whether to return source citations
            return_related_questions: Whether to return related questions
            temperature: Sampling temperature (0-2)
            top_p: Top-p sampling parameter
            max_tokens: Maximum tokens in response
            
        Returns:
            Response from Perplexity API including answer and citations
        """
        endpoint = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ],
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "return_citations": return_citations,
            "return_related_questions": return_related_questions
        }
        
        if search_domain_filter:
            payload["search_domain_filter"] = search_domain_filter
            
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def search(self, query: str, **kwargs) -> str:
        """
        Simplified search method that returns just the answer text.
        This is the main method an agent would call for simple queries.
        
        Args:
            query: The search query or question
            **kwargs: Additional parameters to pass to chat method
            
        Returns:
            The answer text from Perplexity
        """
        result = self.chat(query, **kwargs)
        
        if "error" in result:
            return f"Error: {result['error']}"
        
        try:
            # Extract the content from the response
            return result['choices'][0]['message']['content']
        except (KeyError, IndexError):
            return "Could not extract answer from response"
    
    def search_with_sources(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Search with full response including sources and citations.
        
        Args:
            query: The search query or question
            **kwargs: Additional parameters to pass to chat method
            
        Returns:
            Full response with answer, citations, and metadata
        """
        kwargs['return_citations'] = True
        result = self.chat(query, **kwargs)
        
        if "error" in result:
            return result
        
        try:
            response_data = {
                "answer": result['choices'][0]['message']['content'],
                "citations": result.get('citations', []),
                "usage": result.get('usage', {}),
                "model": result.get('model', '')
            }
            
            # Add related questions if they exist
            if 'related_questions' in result:
                response_data['related_questions'] = result['related_questions']
                
            return response_data
        except (KeyError, IndexError) as e:
            return {"error": f"Failed to parse response: {str(e)}"}
    
    def fact_check(self, statement: str) -> Dict[str, Any]:
        """
        Fact-check a statement using Perplexity's search capabilities.
        
        Args:
            statement: The statement to fact-check
            
        Returns:
            Fact-checking results with verdict and supporting evidence
        """
        prompt = f"""
        Fact-check the following statement and provide:
        1. Whether it's TRUE, FALSE, or PARTIALLY TRUE
        2. Supporting evidence with sources
        3. Any important context or nuances
        
        Statement: {statement}
        """
        
        result = self.search_with_sources(prompt, temperature=0.1)
        
        if "error" in result:
            return result
            
        return {
            "statement": statement,
            "analysis": result.get("answer", ""),
            "sources": result.get("citations", []),
            "usage": result.get("usage", {})
        }
    
    def research(self, 
                 topic: str, 
                 depth: str = "balanced",
                 domains: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Conduct research on a topic with configurable depth.
        
        Args:
            topic: The topic to research
            depth: Research depth - "quick", "balanced", or "comprehensive"
            domains: Optional list of domains to search within
            
        Returns:
            Research findings with sources
        """
        depth_configs = {
            "quick": {"max_tokens": 512, "model": "sonar-pro"},
            "balanced": {"max_tokens": 1024, "model": "sonar-pro"},
            "comprehensive": {"max_tokens": 2048, "model": "sonar-pro"}
        }
        
        config = depth_configs.get(depth, depth_configs["balanced"])
        
        prompt = f"Provide a comprehensive overview of: {topic}"
        
        return self.search_with_sources(
            prompt, 
            model=config["model"],
            max_tokens=config["max_tokens"],
            search_domain_filter=domains,
            return_related_questions=True
        )
    
    def compare(self, items: List[str], criteria: Optional[str] = None) -> str:
        """
        Compare multiple items or concepts.
        
        Args:
            items: List of items to compare
            criteria: Optional specific criteria for comparison
            
        Returns:
            Comparison analysis
        """
        items_str = ", ".join(items)
        prompt = f"Compare and contrast: {items_str}"
        
        if criteria:
            prompt += f"\nFocus on: {criteria}"
            
        return self.search(prompt, temperature=0.3)
    
    def summarize_url(self, url: str) -> str:
        """
        Summarize content from a specific URL.
        
        Args:
            url: The URL to summarize
            
        Returns:
            Summary of the content
        """
        prompt = f"Summarize the key points from this webpage: {url}"
        return self.search(prompt, search_domain_filter=[url])
    
    def get_latest(self, topic: str, time_frame: str = "past 24 hours") -> Dict[str, Any]:
        """
        Get the latest information on a topic.
        
        Args:
            topic: The topic to get updates on
            time_frame: Time frame for recency (e.g., "past 24 hours", "past week")
            
        Returns:
            Latest information with sources
        """
        prompt = f"What are the latest developments about {topic} in the {time_frame}? Focus on the most recent and important updates."
        
        return self.search_with_sources(
            prompt,
            temperature=0.2,
            return_related_questions=True
        )


# Example usage and testing
if __name__ == "__main__":
    # Initialize the agent
    agent = PerplexityAgent()
    
    # Example 1: Simple search
    print("Example 1: Simple search")
    result = agent.search("What is the capital of France?")
    print(f"Answer: {result}\n")
    
    # Example 2: Search with sources
    print("Example 2: Search with sources")
    result = agent.search_with_sources("What are the latest AI developments?")
    print(f"Answer: {result.get('answer', 'No answer')[:200]}...")
    print(f"Citations: {len(result.get('citations', []))} sources\n")
    
    # Example 3: Fact checking
    print("Example 3: Fact checking")
    result = agent.fact_check("The Earth is flat")
    print(f"Analysis: {result.get('analysis', 'No analysis')[:200]}...\n")
    
    # Example 4: Research
    print("Example 4: Research on a topic")
    result = agent.research("quantum computing", depth="quick")
    print(f"Research: {result.get('answer', 'No answer')[:200]}...\n")
    
    # Example 5: Comparison
    print("Example 5: Compare items")
    result = agent.compare(["Python", "JavaScript", "Go"], "performance and ease of use")
    print(f"Comparison: {result[:200]}...\n")
