"""
Statute Agent - Specialized agent for finding and analyzing legal statutes.
Uses Perplexity search for accessing legal databases and sources.
"""

import os
import sys
import re
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util.perplexity import PerplexityAgent
from agents.baseAgent import BaseAgent, MessageRole


@dataclass
class StatuteInfo:
    """Structured information about a statute"""
    title: str
    citation: str
    definitions: Dict[str, str]
    key_provisions: List[str]
    remedies: List[str]
    snippet: str
    full_text: Optional[str] = None  # Full statutory text
    sections: Optional[Dict[str, str]] = None  # Individual sections
    legislative_history: Optional[str] = None  # Legislative background
    interpretive_notes: Optional[str] = None  # Legal interpretations
    source_url: Optional[str] = None
    last_updated: Optional[str] = None


class StatuteAgent:
    """
    Specialized agent for finding and analyzing legal statutes.
    Optimized for U.S. federal and state law research.
    """
    
    # Legal source domains for focused searches
    LEGAL_SOURCES = [
        "law.cornell.edu",      # Cornell Legal Information Institute
        "www.law.cornell.edu",
        "justia.com",          # Justia
        "www.justia.com",
        "uscode.house.gov",    # U.S. Code
        "www.govinfo.gov",     # Government Publishing Office
        "supremecourt.gov",    # Supreme Court
        "regulations.gov",     # Federal Regulations
        "congress.gov"         # Congress.gov
    ]
    
    def __init__(self, 
                 name: str = "StatuteAgent",
                 use_base_agent: bool = False,
                 enable_caching: bool = True):
        """
        Initialize the Statute Agent.
        
        Args:
            name: Agent name
            use_base_agent: Whether to also use a BaseAgent for complex reasoning
            enable_caching: Cache search results to avoid redundant API calls
        """
        self.name = name
        self.perplexity = PerplexityAgent()
        
        # Optional: Use BaseAgent for more complex reasoning
        self.base_agent = None
        if use_base_agent:
            self.base_agent = BaseAgent(
                name=f"{name}_Assistant",
                system_prompt="""You are a legal research assistant specializing in U.S. statutes and regulations.
                Your role is to analyze legal text and provide clear, accurate summaries.
                Always cite specific sections and provide exact legal language when relevant.""",
                enable_tools=True,
                temperature=0.2  # Low temperature for accuracy
            )
        
        # Cache for search results
        self.cache = {} if enable_caching else None
        self.search_history = []
    
    def _format_search_query(self, query: str, include_sources: bool = True) -> str:
        """
        Format a search query for optimal legal research results.
        
        Args:
            query: The user's query
            include_sources: Whether to specify legal sources
            
        Returns:
            Formatted search query
        """
        # Add legal context if not present
        legal_keywords = ["statute", "law", "code", "USC", "CFR", "act", "regulation"]
        has_legal_context = any(keyword.lower() in query.lower() for keyword in legal_keywords)
        
        if not has_legal_context:
            query = f"U.S. law statute {query}"
        
        # Add source specification if desired
        if include_sources:
            query += " site:law.cornell.edu OR site:justia.com OR site:uscode.house.gov"
        
        return query
    
    def find_statute(self, 
                     query: str,
                     jurisdiction: str = "federal",
                     include_history: bool = False,
                     detailed: bool = False) -> StatuteInfo:
        """
        Find a specific statute based on the query.
        
        Args:
            query: Description of the law/statute to find
            jurisdiction: "federal" or state name (e.g., "California")
            include_history: Include legislative history
            detailed: Get full statutory text and sections
            
        Returns:
            StatuteInfo object with structured statute information
        """
        # Check cache first
        cache_key = f"{query}_{jurisdiction}_{include_history}_{detailed}"
        if self.cache is not None and cache_key in self.cache:
            return self.cache[cache_key]
        
        # Build search query - request full text if detailed
        if detailed:
            search_query = f"Full text statutory language provisions sections subsections {self._format_search_query(query)}"
        else:
            search_query = self._format_search_query(query)
        
        if jurisdiction != "federal":
            search_query = f"{jurisdiction} state {search_query}"
        
        if include_history:
            search_query += " legislative history amendments congressional intent"
        
        # Search with Perplexity - use more tokens for detailed requests
        max_tokens = 4096 if detailed else 2048
        
        try:
            # Try with default model first, fall back if needed
            search_result = self.perplexity.search_with_sources(
                search_query,
                temperature=0.1,  # Very low for accuracy
                max_tokens=max_tokens
            )
        except Exception as e:
            # If default model fails, try with basic sonar model
            try:
                search_result = self.perplexity.search_with_sources(
                    search_query,
                    model="sonar",
                    temperature=0.1,
                    max_tokens=1024
                )
            except Exception as e2:
                print(f"Error calling Perplexity API: {e2}")
                # Return a basic result if API fails
                return StatuteInfo(
                    title="Error retrieving statute",
                    citation="N/A",
                    definitions={},
                    key_provisions=[],
                    remedies=[],
                    snippet=f"Error: Unable to retrieve statute information. {str(e2)}",
                    source_url=None,
                    last_updated=datetime.now().isoformat()
                )
        
        # Parse the result
        statute_info = self._parse_statute_response(
            search_result.get("answer", ""),
            search_result.get("citations", []),
            detailed=detailed
        )
        
        # Cache the result
        if self.cache is not None:
            self.cache[cache_key] = statute_info
        
        # Log to history
        self.search_history.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "jurisdiction": jurisdiction,
            "result": statute_info.citation
        })
        
        return statute_info
    
    def _parse_statute_response(self, 
                                response_text: str, 
                                citations: List[Any],
                                detailed: bool = False) -> StatuteInfo:
        """
        Parse Perplexity response into structured StatuteInfo using LLM-based extraction.
        
        Args:
            response_text: The text response from Perplexity
            citations: List of citation sources (URLs as strings)
            detailed: Whether to extract additional detailed information
            
        Returns:
            Structured StatuteInfo object
        """
        # Handle empty response
        if not response_text:
            response_text = ""
        
        # Use LLM to extract structured information
        extracted_info = self._extract_statute_info_with_llm(response_text, detailed)
        
        # Create concise snippet
        snippet = self._create_snippet(
            extracted_info.get('title', 'Unknown Statute'),
            extracted_info.get('citation', 'Citation not found'),
            extracted_info.get('definitions', {}),
            extracted_info.get('remedies', [])
        )
        
        # Get source URL if available
        source_url = citations[0] if citations and len(citations) > 0 else None
        
        return StatuteInfo(
            title=extracted_info.get('title', 'Unknown Statute'),
            citation=extracted_info.get('citation', 'Citation not found'),
            definitions=extracted_info.get('definitions', {}),
            key_provisions=extracted_info.get('key_provisions', []),
            remedies=extracted_info.get('remedies', []),
            snippet=snippet,
            full_text=extracted_info.get('full_text', None) if detailed else None,
            sections=extracted_info.get('sections', None) if detailed else None,
            legislative_history=extracted_info.get('legislative_history', None) if detailed else None,
            interpretive_notes=extracted_info.get('interpretive_notes', None) if detailed else None,
            source_url=source_url,
            last_updated=datetime.now().isoformat()
        )
    
    def _extract_statute_info_with_llm(self, text: str, detailed: bool = False) -> Dict[str, Any]:
        """
        Use an LLM to extract structured statute information from text.
        
        Args:
            text: The text to extract information from
            detailed: Whether to extract additional detailed fields
            
        Returns:
            Dictionary with extracted information
        """
        # Initialize a simple LLM client (using the existing base agent infrastructure)
        from agents.baseAgent import BaseAgent
        import json
        
        extractor = BaseAgent(
            name="StatuteExtractor",
            system_prompt="You are a legal information extractor. Extract structured legal information from text and return it as JSON.",
            temperature=0.1,
            enable_tools=False,
            response_format='json'  # Enable JSON output mode
        )
        
        # Prepare the extraction prompt
        if detailed:
            prompt = f"""Extract the following information from this legal text:

{text}

Return a JSON object with these fields:
{{
    "title": "Full name of the Act or statute",
    "citation": "Legal citation (e.g., '18 U.S.C. § 1836')",
    "definitions": {{
        "term1": "definition1",
        "term2": "definition2"
    }},
    "key_provisions": ["provision1", "provision2", ...],
    "remedies": ["remedy1", "remedy2", ...],
    "full_text": "Complete statutory text if available",
    "sections": {{
        "Section 1": "text of section 1",
        "Section 2": "text of section 2"
    }},
    "legislative_history": "Legislative background and amendments",
    "interpretive_notes": "Judicial interpretations and notes"
}}

Extract as much information as available. Use null for fields with no information."""
        else:
            prompt = f"""Extract the following information from this legal text:

{text}

Return a JSON object with these fields:
{{
    "title": "Full name of the Act or statute",
    "citation": "Legal citation (e.g., '18 U.S.C. § 1836')",
    "definitions": {{
        "term1": "definition1",
        "term2": "definition2"
    }},
    "key_provisions": ["provision1", "provision2", ...],
    "remedies": ["remedy1", "remedy2", ...]
}}

Extract as much information as available. Use empty objects/arrays for fields with no information."""
        
        # Get LLM response
        response = extractor.chat(prompt)
        
        # Parse JSON response
        try:
            # When response_format='json', Gemini returns raw JSON
            # No need to clean markdown code blocks
            if isinstance(response, str):
                # Try to parse as-is first (when using response_mime_type)
                try:
                    extracted = json.loads(response.strip())
                except json.JSONDecodeError:
                    # Fallback: clean markdown if present
                    if '```json' in response:
                        response = response.split('```json')[1].split('```')[0]
                    elif '```' in response:
                        response = response.split('```')[1].split('```')[0]
                    extracted = json.loads(response.strip())
            else:
                extracted = response  # Already parsed
            
            # Ensure all required fields exist
            defaults = {
                'title': 'Unknown Statute',
                'citation': 'Citation not found',
                'definitions': {},
                'key_provisions': [],
                'remedies': [],
                'full_text': None,
                'sections': None,
                'legislative_history': None,
                'interpretive_notes': None
            }
            
            for key, default_value in defaults.items():
                if key not in extracted:
                    extracted[key] = default_value
            
            return extracted
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"Warning: Failed to parse statute extraction JSON: {e}")
            # Fallback to legacy regex-based extraction
            return self._fallback_regex_extraction(text, detailed)
    
    def _fallback_regex_extraction(self, text: str, detailed: bool = False) -> Dict[str, Any]:
        """Fallback to regex-based extraction if LLM fails."""
        # Use the original regex-based methods
        citation_pattern = r'\b\d+\s+U\.?S\.?C\.?\s*§+\s*\d+[a-z]?|\b\d+\s+C\.?F\.?R\.?\s*§+\s*\d+\.?\d*'
        citations_found = re.findall(citation_pattern, text, re.IGNORECASE)
        main_citation = citations_found[0] if citations_found else "Citation not found"
        
        # Extract title/name of the Act
        title_patterns = [
            r'(?:the\s+)?([A-Z][A-Za-z\s]+(?:Act|Code|Law))',
            r'(?:Title\s+[IVX]+:\s+)([A-Za-z\s]+)',
            r'(?:known\s+as\s+(?:the\s+)?)([A-Z][A-Za-z\s]+)'
        ]
        
        title = "Unknown Statute"
        for pattern in title_patterns:
            match = re.search(pattern, text)
            if match:
                title = match.group(1).strip()
                break
        
        result = {
            'title': title,
            'citation': main_citation,
            'definitions': self._extract_definitions(text),
            'key_provisions': self._extract_provisions(text),
            'remedies': self._extract_remedies(text)
        }
        
        if detailed:
            result['full_text'] = self._extract_full_text(text)
            result['sections'] = self._extract_sections(text)
            result['legislative_history'] = self._extract_legislative_history(text)
            result['interpretive_notes'] = self._extract_interpretive_notes(text)
        
        return result
    
    def _extract_definitions(self, text: str) -> Dict[str, str]:
        """Extract legal definitions from text."""
        definitions = {}
        
        # Common definition patterns
        patterns = [
            r'"([^"]+)"\s+means\s+([^.]+\.)',
            r'"([^"]+)"\s+refers?\s+to\s+([^.]+\.)',
            r'([A-Za-z\s]+)\s+is\s+defined\s+as\s+([^.]+\.)',
            r'definition\s+of\s+"?([^"]+)"?\s+(?:is|includes?)\s+([^.]+\.)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                term = match.group(1).strip().lower()
                definition = match.group(2).strip()
                if term not in definitions:
                    definitions[term] = definition
        
        return definitions
    
    def _extract_provisions(self, text: str) -> List[str]:
        """Extract key provisions from text."""
        provisions = []
        
        # Look for numbered or bulleted provisions
        patterns = [
            r'(?:\d+[\).]|\([a-z]\))\s+([^.]+\.)',
            r'(?:shall|must|may|prohibits?|requires?)\s+([^.]+\.)',
            r'(?:provision|requirement|obligation)s?\s+(?:include|are):\s+([^.]+\.)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                provision = match.group(1).strip() if match.lastindex == 1 else match.group(0).strip()
                if len(provision) > 20 and provision not in provisions:
                    provisions.append(provision)
        
        return provisions[:5]  # Limit to top 5 provisions
    
    def _extract_remedies(self, text: str) -> List[str]:
        """Extract legal remedies from text."""
        remedies = []
        
        # Common remedy terms
        remedy_keywords = [
            "injunction", "injunctive relief",
            "damages", "compensatory damages", "punitive damages", "exemplary damages",
            "attorneys' fees", "attorney fees", "legal fees",
            "restitution", "disgorgement",
            "criminal penalties", "civil penalties",
            "imprisonment", "fine", "fines",
            "cease and desist",
            "equitable relief"
        ]
        
        text_lower = text.lower()
        for keyword in remedy_keywords:
            if keyword in text_lower:
                # Find context around the keyword
                pattern = rf'[^.]*\b{re.escape(keyword)}\b[^.]*\.'
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    remedy = match.group(0).strip()
                    if remedy not in remedies:
                        remedies.append(remedy)
        
        return remedies[:5]  # Limit to top 5 remedies
    
    def _extract_full_text(self, text: str) -> Optional[str]:
        """Extract full statutory text from response."""
        if not text:
            return None
        
        # Look for patterns indicating full statutory text
        patterns = [
            r'(?:full text|text of (?:the )?statute|statutory language)[:\s]+(.+)',
            r'(?:Section \d+[a-z]?[\.\)])\s+(.+)',
            r'(?:\(\d+\))\s+(.+)',
            r'(?:states?|provides?|reads?)[:\s]+["\'](.+?)["\']',
        ]
        
        full_text_parts = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                extracted = match.group(1).strip()
                if len(extracted) > 100:  # Only include substantial text
                    full_text_parts.append(extracted)
        
        # If we found statutory text, combine it
        if full_text_parts:
            return "\n\n".join(full_text_parts)
        
        # If no specific patterns found but text is long, it might be the full text
        if len(text) > 1000:
            return text
        
        return None
    
    def _extract_sections(self, text: str) -> Optional[Dict[str, str]]:
        """Extract individual sections and subsections from statutory text."""
        sections = {}
        
        # Patterns for section headers
        section_patterns = [
            r'(?:Section|Sec\.?|§)\s*(\d+[a-z]?)\s*[-–—]?\s*([^\n]+)',
            r'\(([a-z])\)\s+([^.]+\.)',
            r'(?:Subsection|Subsec\.?)\s*\((\d+)\)\s*[-–—]?\s*([^\n]+)',
        ]
        
        for pattern in section_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                section_id = match.group(1).strip()
                section_text = match.group(2).strip()
                if section_id and section_text:
                    sections[f"Section {section_id}"] = section_text[:500]  # Limit length
        
        return sections if sections else None
    
    def _extract_legislative_history(self, text: str) -> Optional[str]:
        """Extract legislative history and background information."""
        history_keywords = [
            "legislative history", "enacted", "amended", "congress", 
            "public law", "house report", "senate report", "conference report",
            "legislative intent", "congressional findings"
        ]
        
        history_parts = []
        text_lower = text.lower()
        
        for keyword in history_keywords:
            if keyword in text_lower:
                # Find sentences containing the keyword
                pattern = rf'[^.]*\b{re.escape(keyword)}\b[^.]*\.'
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    history_part = match.group(0).strip()
                    if history_part not in history_parts:
                        history_parts.append(history_part)
        
        return " ".join(history_parts[:5]) if history_parts else None
    
    def _extract_interpretive_notes(self, text: str) -> Optional[str]:
        """Extract legal interpretations and judicial notes."""
        interpretation_keywords = [
            "interpreted", "means", "construed", "held", "ruled",
            "court found", "supreme court", "circuit court",
            "case law", "precedent", "holding"
        ]
        
        interpretations = []
        text_lower = text.lower()
        
        for keyword in interpretation_keywords:
            if keyword in text_lower:
                pattern = rf'[^.]*\b{re.escape(keyword)}\b[^.]*\.'
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    interpretation = match.group(0).strip()
                    if interpretation not in interpretations and len(interpretation) > 50:
                        interpretations.append(interpretation)
        
        return " ".join(interpretations[:5]) if interpretations else None
    
    def _create_snippet(self,
                       title: str,
                       citation: str,
                       definitions: Dict[str, str],
                       remedies: List[str]) -> str:
        """
        Create a concise 2-3 sentence snippet summarizing the statute.
        
        Args:
            title: Statute title
            citation: Legal citation
            definitions: Key definitions
            remedies: Available remedies
            
        Returns:
            Concise snippet
        """
        snippet_parts = []
        
        # First sentence: Citation and title
        if title and title != "Unknown Statute":
            if citation and citation != "Citation not found":
                snippet_parts.append(f"{title} ({citation})")
            else:
                snippet_parts.append(title)
        elif citation and citation != "Citation not found":
            snippet_parts.append(f"Statute {citation}")
        else:
            snippet_parts.append("The requested statute")
        
        # Second sentence: Key definition if available
        if definitions:
            first_def = list(definitions.items())[0]
            def_text = first_def[1][:100] if len(first_def[1]) > 100 else first_def[1]
            if not def_text.endswith('.'):
                def_text += '...' if len(first_def[1]) > 100 else '.'
            snippet_parts.append(f"defines '{first_def[0]}' as {def_text}")
        
        # Third sentence: Primary remedies
        if remedies:
            remedy_list = []
            remedy_keywords = ["injunction", "injunctive relief", "damages", "attorneys' fees", 
                             "attorney fees", "penalties", "criminal penalties", "civil penalties",
                             "restitution", "disgorgement", "imprisonment", "fines"]
            
            for remedy in remedies[:3]:
                remedy_lower = remedy.lower()
                for keyword in remedy_keywords:
                    if keyword in remedy_lower:
                        # Clean up the keyword for display
                        display_keyword = keyword.replace("attorneys' fees", "attorneys' fees")
                        display_keyword = display_keyword.replace("attorney fees", "attorneys' fees")
                        if display_keyword not in remedy_list:
                            remedy_list.append(display_keyword)
                        break
            
            if remedy_list:
                snippet_parts.append(f"Remedies include {', '.join(remedy_list[:3])}.")
        
        # Join and ensure proper formatting
        result = " ".join(snippet_parts[:3])  # Limit to 2-3 sentences
        
        # Ensure it ends with a period
        if result and not result.endswith('.'):
            result += '.'
            
        return result
    
    def find_related_statutes(self, 
                            base_statute: str,
                            relationship_type: str = "similar") -> List[Dict[str, str]]:
        """
        Find statutes related to a given statute.
        
        Args:
            base_statute: Citation or description of base statute
            relationship_type: "similar", "superseded", "implementing", "conflicting"
            
        Returns:
            List of related statutes with descriptions
        """
        query = f"statutes related to {base_statute} {relationship_type} laws regulations"
        
        if relationship_type == "superseded":
            query += " replaced amended previous version"
        elif relationship_type == "implementing":
            query += " implementation regulations CFR administrative"
        elif relationship_type == "conflicting":
            query += " conflicts preemption inconsistent"
        
        result = self.perplexity.search_with_sources(query, search_domain_filter=self.LEGAL_SOURCES)
        
        # Parse related statutes
        related = []
        citations = re.findall(r'\b\d+\s+U\.?S\.?C\.?\s*§+\s*\d+[a-z]?', result.get("answer", ""))
        
        for citation in citations[:5]:  # Limit to 5 related statutes
            if citation != base_statute:
                related.append({
                    "citation": citation,
                    "relationship": relationship_type,
                    "description": f"Related statute under {relationship_type} category"
                })
        
        return related
    
    def analyze_statute(self, 
                       citation: str,
                       aspects: List[str] = None) -> Dict[str, Any]:
        """
        Perform deep analysis of a specific statute.
        
        Args:
            citation: The statute citation (e.g., "18 U.S.C. § 1836")
            aspects: Specific aspects to analyze ["definitions", "remedies", "elements", "defenses", "jurisdiction"]
            
        Returns:
            Comprehensive analysis dictionary
        """
        if aspects is None:
            aspects = ["definitions", "remedies", "elements", "defenses", "jurisdiction"]
        
        analysis = {"citation": citation, "analysis_date": datetime.now().isoformat()}
        
        for aspect in aspects:
            query = f"{citation} {aspect} legal analysis"
            
            if aspect == "elements":
                query += " prima facie case requirements proof burden"
            elif aspect == "defenses":
                query += " affirmative defenses exceptions exemptions"
            elif aspect == "jurisdiction":
                query += " federal state court jurisdiction venue"
            
            result = self.perplexity.search(
                query,
                search_domain_filter=self.LEGAL_SOURCES,
                temperature=0.1
            )
            
            analysis[aspect] = result[:500] if len(result) > 500 else result
        
        return analysis
    
    def compare_statutes(self,
                        statute1: str,
                        statute2: str,
                        comparison_points: List[str] = None) -> Dict[str, Any]:
        """
        Compare two statutes on specific points.
        
        Args:
            statute1: First statute citation or description
            statute2: Second statute citation or description  
            comparison_points: Aspects to compare ["scope", "remedies", "requirements", "penalties"]
            
        Returns:
            Comparison analysis
        """
        if comparison_points is None:
            comparison_points = ["scope", "remedies", "requirements", "penalties"]
        
        comparison = {
            "statute1": statute1,
            "statute2": statute2,
            "comparison_date": datetime.now().isoformat(),
            "differences": [],
            "similarities": []
        }
        
        # Get general comparison
        query = f"Compare {statute1} and {statute2} differences similarities legal analysis"
        result = self.perplexity.search(query, search_domain_filter=self.LEGAL_SOURCES)
        
        comparison["overview"] = result[:500]
        
        # Compare specific points
        for point in comparison_points:
            point_query = f"{statute1} vs {statute2} {point} comparison difference"
            point_result = self.perplexity.search(point_query, temperature=0.1)
            
            comparison[f"{point}_comparison"] = point_result[:300]
        
        return comparison
    
    def get_case_law(self,
                     statute: str,
                     num_cases: int = 5,
                     jurisdiction: str = "federal") -> List[Dict[str, str]]:
        """
        Find relevant case law interpreting a statute.
        
        Args:
            statute: Statute citation
            num_cases: Number of cases to return
            jurisdiction: Court jurisdiction
            
        Returns:
            List of relevant cases
        """
        query = f"{statute} case law court decisions interpretations {jurisdiction}"
        
        if jurisdiction == "supreme court":
            query += " U.S. Supreme Court SCOTUS"
        elif jurisdiction != "federal":
            query += f" {jurisdiction} state court"
        
        result = self.perplexity.search_with_sources(query)
        
        # Extract case citations
        case_pattern = r'([A-Z][A-Za-z\s]+v\.\s+[A-Z][A-Za-z\s]+),?\s*(\d{3}\s+U\.S\.\s+\d+|\d{3}\s+F\.\d+d\s+\d+)?'
        cases_found = re.findall(case_pattern, result.get("answer", ""))
        
        cases = []
        for case_name, case_cite in cases_found[:num_cases]:
            cases.append({
                "name": case_name.strip(),
                "citation": case_cite.strip() if case_cite else "Citation pending",
                "relevance": f"Interprets {statute}"
            })
        
        return cases
    
    def quick_search(self, query: str) -> str:
        """
        Quick statute search that returns a concise snippet.
        This is the main method for simple queries.
        
        Args:
            query: Natural language query about a statute
            
        Returns:
            2-3 sentence snippet with key information
        """
        # Find the statute (without detailed content)
        statute_info = self.find_statute(query, detailed=False)
        
        # Return the pre-formatted snippet
        return statute_info.snippet
    
    def comprehensive_research(self, 
                              query: str,
                              jurisdiction: str = "federal",
                              include_case_law: bool = True,
                              num_cases: int = 5) -> Dict[str, Any]:
        """
        Comprehensive legal research with full statutory text and context.
        This is the main method for detailed lawyer-level research.
        
        Args:
            query: Natural language query about a statute
            jurisdiction: "federal" or state name
            include_case_law: Whether to include relevant cases
            num_cases: Number of cases to retrieve
            
        Returns:
            Comprehensive research package with full text, analysis, and context
        """
        # Get detailed statute information
        statute_info = self.find_statute(query, jurisdiction=jurisdiction, 
                                        include_history=True, detailed=True)
        
        # Build comprehensive research package
        research = {
            "query": query,
            "jurisdiction": jurisdiction,
            "timestamp": datetime.now().isoformat(),
            "statute": {
                "title": statute_info.title,
                "citation": statute_info.citation,
                "summary": statute_info.snippet,
                "full_text": statute_info.full_text,
                "sections": statute_info.sections,
                "definitions": statute_info.definitions,
                "key_provisions": statute_info.key_provisions,
                "remedies": statute_info.remedies,
                "legislative_history": statute_info.legislative_history,
                "interpretive_notes": statute_info.interpretive_notes,
                "source_url": statute_info.source_url
            }
        }
        
        # Add case law if requested
        if include_case_law and statute_info.citation != "Citation not found":
            research["case_law"] = self.get_case_law(
                statute_info.citation, 
                num_cases=num_cases,
                jurisdiction=jurisdiction
            )
        
        # Add related statutes
        if statute_info.citation != "Citation not found":
            research["related_statutes"] = self.find_related_statutes(
                statute_info.citation, 
                "similar"
            )[:3]  # Limit to 3 related statutes
        
        # Generate analysis summary
        research["analysis_summary"] = self._generate_analysis_summary(research)
        
        return research
    
    def _generate_analysis_summary(self, research: Dict[str, Any]) -> str:
        """Generate a comprehensive analysis summary for lawyer use."""
        statute = research["statute"]
        
        summary_parts = []
        
        # Title and citation
        summary_parts.append(f"LEGAL RESEARCH SUMMARY: {statute['title']}")
        summary_parts.append(f"Citation: {statute['citation']}")
        summary_parts.append("")
        
        # Executive summary
        summary_parts.append("EXECUTIVE SUMMARY:")
        summary_parts.append(statute['summary'])
        summary_parts.append("")
        
        # Key definitions
        if statute['definitions']:
            summary_parts.append("KEY DEFINITIONS:")
            for term, definition in list(statute['definitions'].items())[:3]:
                summary_parts.append(f"• {term.title()}: {definition[:200]}...")
            summary_parts.append("")
        
        # Main provisions
        if statute['key_provisions']:
            summary_parts.append("MAIN PROVISIONS:")
            for i, provision in enumerate(statute['key_provisions'][:5], 1):
                summary_parts.append(f"{i}. {provision[:150]}...")
            summary_parts.append("")
        
        # Available remedies
        if statute['remedies']:
            summary_parts.append("AVAILABLE REMEDIES:")
            for remedy in statute['remedies'][:5]:
                summary_parts.append(f"• {remedy[:150]}...")
            summary_parts.append("")
        
        # Legislative context
        if statute['legislative_history']:
            summary_parts.append("LEGISLATIVE CONTEXT:")
            summary_parts.append(statute['legislative_history'][:500] + "...")
            summary_parts.append("")
        
        # Judicial interpretation
        if statute['interpretive_notes']:
            summary_parts.append("JUDICIAL INTERPRETATION:")
            summary_parts.append(statute['interpretive_notes'][:500] + "...")
            summary_parts.append("")
        
        # Case law summary
        if "case_law" in research and research["case_law"]:
            summary_parts.append("RELEVANT CASE LAW:")
            for case in research["case_law"][:3]:
                summary_parts.append(f"• {case['name']} - {case['citation']}")
            summary_parts.append("")
        
        # Related statutes
        if "related_statutes" in research and research["related_statutes"]:
            summary_parts.append("RELATED STATUTES:")
            for statute in research["related_statutes"]:
                summary_parts.append(f"• {statute['citation']}")
            summary_parts.append("")
        
        return "\n".join(summary_parts)
    
    def export_research(self, 
                       filename: str = None,
                       format: str = "json") -> str:
        """
        Export research history and cached results.
        
        Args:
            filename: Output filename (auto-generated if None)
            format: Export format ("json" or "markdown")
            
        Returns:
            Path to exported file
        """
        import json
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"statute_research_{timestamp}.{format}"
        
        export_data = {
            "agent": self.name,
            "export_date": datetime.now().isoformat(),
            "search_history": self.search_history,
            "cached_results": {}
        }
        
        # Include cached results if available
        if self.cache:
            for key, value in self.cache.items():
                export_data["cached_results"][key] = {
                    "title": value.title,
                    "citation": value.citation,
                    "snippet": value.snippet,
                    "source_url": value.source_url
                }
        
        if format == "json":
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
        
        elif format == "markdown":
            with open(filename, 'w') as f:
                f.write(f"# Statute Research Export\n\n")
                f.write(f"**Agent**: {export_data['agent']}\n")
                f.write(f"**Date**: {export_data['export_date']}\n\n")
                
                f.write("## Search History\n\n")
                for search in export_data['search_history']:
                    f.write(f"- **{search['timestamp']}**: {search['query']} → {search['result']}\n")
                
                f.write("\n## Cached Results\n\n")
                for key, result in export_data['cached_results'].items():
                    f.write(f"### {result['title']}\n")
                    f.write(f"- **Citation**: {result['citation']}\n")
                    f.write(f"- **Summary**: {result['snippet']}\n")
                    if result['source_url']:
                        f.write(f"- **Source**: [{result['source_url']}]({result['source_url']})\n")
                    f.write("\n")
        
        return filename


# Example usage and testing
if __name__ == "__main__":
    # Initialize the Statute Agent
    print("Initializing Statute Agent...")
    statute_agent = StatuteAgent()
    
    # Example 1: Quick search for trade secret law
    print("\n" + "="*60)
    print("Example 1: Quick Search - Trade Secret Law")
    print("="*60)
    
    query = "Find the U.S. law that governs trade secret misappropriation, its citation, definitions of trade secret and misappropriation, and remedies"
    result = statute_agent.quick_search(query)
    print(f"\nQuery: {query}")
    print(f"Quick Result: {result}\n")
    
    # Example 1b: Comprehensive research for lawyer use
    print("="*60)
    print("Example 1b: Comprehensive Research - Trade Secret Law")
    print("="*60)
    
    comprehensive = statute_agent.comprehensive_research(query, include_case_law=True)
    print(f"\n📊 COMPREHENSIVE LEGAL RESEARCH")
    print(f"Citation: {comprehensive['statute']['citation']}")
    print(f"\nAnalysis Summary:")
    print("-" * 40)
    print(comprehensive['analysis_summary'][:1500])  # Show first 1500 chars
    
    if comprehensive['statute']['full_text']:
        print(f"\n📜 Full Statutory Text Available: {len(comprehensive['statute']['full_text'])} characters")
    
    if comprehensive['statute']['sections']:
        print(f"\n📑 Sections Found: {len(comprehensive['statute']['sections'])}")
        for section_id, section_text in list(comprehensive['statute']['sections'].items())[:2]:
            print(f"  • {section_id}: {section_text[:100]}...")
    
    # Example 2: Find specific statute with detailed info
    print("="*60)
    print("Example 2: Detailed Statute Information")
    print("="*60)
    
    statute_info = statute_agent.find_statute("federal computer fraud and abuse")
    print(f"\nStatute: {statute_info.title}")
    print(f"Citation: {statute_info.citation}")
    print(f"Snippet: {statute_info.snippet}")
    
    if statute_info.definitions:
        print("\nKey Definitions:")
        for term, definition in list(statute_info.definitions.items())[:2]:
            print(f"  - {term}: {definition[:100]}...")
    
    if statute_info.remedies:
        print("\nRemedies:")
        for remedy in statute_info.remedies[:3]:
            print(f"  - {remedy[:100]}...")
    
    # Example 3: Compare statutes
    print("\n" + "="*60)
    print("Example 3: Compare Statutes")
    print("="*60)
    
    comparison = statute_agent.compare_statutes(
        "DTSA (Defend Trade Secrets Act)",
        "UTSA (Uniform Trade Secrets Act)",
        comparison_points=["scope", "remedies"]
    )
    print(f"\nComparing: {comparison['statute1']} vs {comparison['statute2']}")
    print(f"Overview: {comparison['overview'][:200]}...")
    
    # Example 4: Find related statutes
    print("\n" + "="*60)
    print("Example 4: Related Statutes")
    print("="*60)
    
    related = statute_agent.find_related_statutes("18 U.S.C. § 1836", "similar")
    print(f"\nStatutes related to 18 U.S.C. § 1836:")
    for statute in related[:3]:
        print(f"  - {statute['citation']}: {statute['relationship']}")
    
    # Example 5: Get case law
    print("\n" + "="*60)
    print("Example 5: Relevant Case Law")
    print("="*60)
    
    cases = statute_agent.get_case_law("18 U.S.C. § 1836", num_cases=3)
    print(f"\nCases interpreting 18 U.S.C. § 1836:")
    for case in cases:
        print(f"  - {case['name']} ({case['citation']})")
    
    # Example 6: Quick searches for various statutes
    print("\n" + "="*60)
    print("Example 6: Quick Statute Searches")
    print("="*60)
    
    queries = [
        "What law governs securities fraud?",
        "Find the statute for copyright infringement",
        "Federal law on money laundering",
        "Statute for RICO violations"
    ]
    
    for query in queries:
        result = statute_agent.quick_search(query)
        print(f"\nQ: {query}")
        print(f"A: {result}")
    
    # Export research history
    print("\n" + "="*60)
    print("Exporting Research History...")
    print("="*60)
    
    export_file = statute_agent.export_research(format="markdown")
    print(f"Research exported to: {export_file}")
