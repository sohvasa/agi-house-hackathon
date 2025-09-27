from browser_use_sdk import BrowserUse
import os
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

class BrowserUseAgent:
    def __init__(self):
        self.client = BrowserUse(api_key=os.getenv("BROWSER_USE_API_KEY"))
    
    def run_browseruse(self, task): # task is the prompt
        task = self.client.tasks.create_task(task=task, llm="gpt-4.1")
        result = task.complete()
        return result.output
    
    def search_case_on_justia(self, 
                             case_name: Optional[str] = None,
                             legal_topic: Optional[str] = None,
                             year: Optional[str] = None,
                             court: Optional[str] = None,
                             custom_query: Optional[str] = None) -> str:
        """
        Search for case details on JUSTIA US Law.
        
        Args:
            case_name: Name of the case (e.g., "Waymo v. Uber")
            legal_topic: Legal topic or issue (e.g., "trade secret misappropriation")
            year: Year or year range
            court: Court name or level
            custom_query: Custom search query to use instead
            
        Returns:
            Extracted case information from JUSTIA
        """
        if custom_query:
            prompt = custom_query
        else:
            # Build a flexible prompt for JUSTIA
            prompt = "Go to JUSTIA US Law (justia.com/cases). "
            
            if case_name:
                prompt += f"Search for the case: {case_name}. "
            elif legal_topic:
                prompt += f"Search for cases about: {legal_topic}. "
            
            if year:
                prompt += f"Filter by year {year} if possible. "
            
            if court:
                prompt += f"Look for cases from {court}. "
            
            # Specify what information to extract
            prompt += (
                "For each relevant case found (limit to top 3 most relevant), extract and return: "
                "1) Full case citation (including reporter citation if available), "
                "2) Year decided, "
                "3) Court name, "
                "4) The holding or key legal principle (this is crucial - look for sections labeled "
                "'Holding', 'Held', or in the case summary), "
                "5) Brief facts of the case (2-3 sentences), "
                "6) The outcome (e.g., affirmed, reversed, remanded, granted/denied injunction), "
                "7) Any dissenting opinions if notable. "
                "Format each case clearly with labels for each field."
            )
        
        return self.run_browseruse(prompt)
    
    def get_case_full_opinion(self, case_name: str, specific_sections: Optional[List[str]] = None) -> str:
        """
        Get the full opinion or specific sections of a case from JUSTIA.
        
        Args:
            case_name: Name of the case
            specific_sections: Optional list of sections to focus on (e.g., ["holding", "dissent"])
            
        Returns:
            Full opinion text or requested sections
        """
        prompt = f"Go to JUSTIA US Law. Find the case: {case_name}. "
        
        if specific_sections:
            sections_str = ", ".join(specific_sections)
            prompt += f"Focus on extracting these sections: {sections_str}. "
        else:
            prompt += "Extract the full opinion text including all sections. "
        
        prompt += "Include page numbers or section headers if available."
        
        return self.run_browseruse(prompt)
    
    def search_cases_by_judge(self, judge_name: str, num_cases: int = 5) -> str:
        """
        Search for cases by a specific judge.
        
        Args:
            judge_name: Name of the judge
            num_cases: Number of cases to retrieve
            
        Returns:
            List of cases by that judge
        """
        prompt = (
            f"Go to JUSTIA US Law. Search for cases where {judge_name} was the judge. "
            f"Return the top {num_cases} most significant cases with: "
            "case name, year, court, and main holding."
        )
        
        return self.run_browseruse(prompt)
    
    def find_citing_cases(self, case_name: str, num_cases: int = 5) -> str:
        """
        Find cases that cite a particular case.
        
        Args:
            case_name: Name of the case to find citations for
            num_cases: Number of citing cases to retrieve
            
        Returns:
            Cases that cite the given case
        """
        prompt = (
            f"Go to JUSTIA US Law. Find the case: {case_name}. "
            f"Then look for cases that cite this case (citing references). "
            f"Return up to {num_cases} cases that cite it, with: "
            "case name, year, and how they use or distinguish the precedent."
        )
        
        return self.run_browseruse(prompt)

if __name__ == "__main__":
    browseruse = BrowserUseAgent()
    
    # Test the original hardcoded example
    print("Test 1: Original Waymo v. Uber search")
    print(browseruse.search_case_on_justia(case_name="Waymo v. Uber"))
    print("\n" + "="*60 + "\n")
    
    # Test with a legal topic search
    print("Test 2: Search by legal topic")
    print(browseruse.search_case_on_justia(
        legal_topic="trade secret misappropriation by former employee",
        year="2015-2020"
    ))
    print("\n" + "="*60 + "\n")
    
    # Test with custom query
    print("Test 3: Custom query")
    custom = (
        "Go to JUSTIA US Law. Search for landmark intellectual property cases "
        "involving technology companies. Focus on cases about trade secrets or "
        "patents from the last 10 years. Return the top 3 most significant cases."
    )
    print(browseruse.search_case_on_justia(custom_query=custom))
    