"""
Precedent Agent - Specialized agent for finding and analyzing case law precedents.
Searches for relevant court cases and formats them as mini-docs for legal research.
"""

import os
import sys
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util.perplexity import PerplexityAgent
from util.browseruse import BrowserUseAgent
from agents.baseAgent import BaseAgent


class CourtLevel(Enum):
    """Court hierarchy levels"""
    SUPREME_COURT = "Supreme Court"
    FEDERAL_CIRCUIT = "Federal Circuit Court"
    FEDERAL_DISTRICT = "Federal District Court"
    STATE_SUPREME = "State Supreme Court"
    STATE_APPEALS = "State Appeals Court"
    STATE_TRIAL = "State Trial Court"
    UNKNOWN = "Unknown Court"


@dataclass
class CasePrecedent:
    """Structured information about a legal precedent"""
    case_name: str
    year: str
    citation: str
    court: str
    court_level: CourtLevel
    holding: str
    rule: str
    facts: Optional[str] = None
    reasoning: Optional[str] = None
    dissent: Optional[str] = None
    relevance_plaintiff: Optional[str] = None
    relevance_defendant: Optional[str] = None
    procedural_posture: Optional[str] = None
    outcome: Optional[str] = None
    mini_doc: Optional[str] = None
    source_url: Optional[str] = None
    confidence_score: float = 0.0


@dataclass
class CaseSearchResult:
    """Collection of case precedents from a search"""
    query: str
    jurisdiction: str
    cases: List[CasePrecedent]
    search_date: str
    total_found: int


class PrecedentAgent:
    """
    Specialized agent for finding and analyzing legal precedents.
    Optimized for case law research and precedent analysis.
    """
    
    # Legal case databases and sources
    CASE_LAW_SOURCES = [
        "scholar.google.com",      # Google Scholar Case Law
        "justia.com/cases",        # Justia Cases
        "courtlistener.com",       # CourtListener
        "law.cornell.edu",         # Cornell LII
        "findlaw.com",            # FindLaw
        "casetext.com",           # Casetext
        "leagle.com"              # Leagle
    ]
    
    def __init__(self, 
                 name: str = "PrecedentAgent",
                 use_reasoning_model: bool = False,
                 enable_caching: bool = True,
                 use_browser: bool = True):
        """
        Initialize the Precedent Agent.
        
        Args:
            name: Agent name
            use_reasoning_model: Use sonar-reasoning-pro for deeper analysis
            enable_caching: Cache search results
            use_browser: Enable Browser Use for detailed case retrieval from JUSTIA
        """
        self.name = name
        self.perplexity = PerplexityAgent()
        self.use_reasoning_model = use_reasoning_model
        
        # Initialize Browser Use agent if enabled
        self.browser = BrowserUseAgent() if use_browser else None
        self.use_browser = use_browser
        
        # Cache for search results
        self.cache = {} if enable_caching else None
        self.search_history = []
    
    def find_precedents(self,
                       query: str,
                       jurisdiction: str = "federal",
                       num_cases: int = 5,
                       year_range: Optional[Tuple[int, int]] = None) -> CaseSearchResult:
        """
        Find relevant case precedents based on the query.
        
        Args:
            query: Description of the legal issue or case type
            jurisdiction: "federal", "state", or specific state/circuit
            num_cases: Number of cases to return
            year_range: Optional tuple of (start_year, end_year)
            
        Returns:
            CaseSearchResult with found precedents
        """
        # Check cache
        cache_key = f"{query}_{jurisdiction}_{num_cases}_{year_range}"
        if self.cache is not None and cache_key in self.cache:
            return self.cache[cache_key]
        
        # Build search query
        search_query = self._build_case_search_query(query, jurisdiction, year_range)
        
        # Search with Perplexity
        model = "sonar-reasoning-pro" if self.use_reasoning_model else "sonar-pro"
        
        try:
            search_result = self.perplexity.search_with_sources(
                search_query,
                model=model,
                temperature=0.1,
                max_tokens=4096,
                search_domain_filter=self.CASE_LAW_SOURCES if not self.use_reasoning_model else None
            )
        except Exception as e:
            print(f"Error searching for precedents: {e}")
            return CaseSearchResult(
                query=query,
                jurisdiction=jurisdiction,
                cases=[],
                search_date=datetime.now().isoformat(),
                total_found=0
            )
        
        # Parse the results into case precedents
        cases = self._parse_case_results(
            search_result.get("answer", ""),
            search_result.get("citations", []),
            num_cases
        )
        
        # Generate mini-docs for each case
        for case in cases:
            case.mini_doc = self._generate_mini_doc(case)
        
        result = CaseSearchResult(
            query=query,
            jurisdiction=jurisdiction,
            cases=cases,
            search_date=datetime.now().isoformat(),
            total_found=len(cases)
        )
        
        # Cache the result
        if self.cache is not None:
            self.cache[cache_key] = result
        
        # Log to history
        self.search_history.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "jurisdiction": jurisdiction,
            "cases_found": len(cases)
        })
        
        return result
    
    def _build_case_search_query(self, 
                                query: str, 
                                jurisdiction: str,
                                year_range: Optional[Tuple[int, int]]) -> str:
        """Build optimized search query for case law."""
        
        # Add case law context
        search_query = f"case law precedent court decision {query}"
        
        # Add holding and rule extraction request
        search_query += " holding rule legal principle facts outcome"
        
        # Add jurisdiction
        if jurisdiction == "federal":
            search_query += " federal court U.S. circuit district Supreme Court"
        elif jurisdiction == "state":
            search_query += " state court appeals supreme"
        else:
            search_query += f" {jurisdiction} court"
        
        # Add year range if specified
        if year_range:
            search_query += f" {year_range[0]}-{year_range[1]}"
        
        # Request specific information
        search_query += " citation year court holding rule facts reasoning"
        
        return search_query
    
    def _parse_case_results(self,
                          response_text: str,
                          citations: List[str],
                          num_cases: int) -> List[CasePrecedent]:
        """Parse search results into structured case precedents."""
        
        cases = []
        
        # Extract case citations (e.g., "Waymo v. Uber", "Smith v. Jones, 123 F.3d 456")
        case_pattern = r'([A-Z][A-Za-z\s&.,]+v\.\s+[A-Z][A-Za-z\s&.,]+)(?:,?\s*(\d+\s+[A-Z]\.\d+d?\s+\d+|\d{4}\s+[A-Z][\w\s]+\d+|\([^)]+\s+\d{4}\)))?'
        case_matches = re.findall(case_pattern, response_text)
        
        for case_name_raw, citation_raw in case_matches[:num_cases]:
            case_name = case_name_raw.strip().rstrip(',')
            
            # Extract year from case name or citation
            year = self._extract_year(case_name, citation_raw, response_text)
            
            # Extract court information
            court, court_level = self._extract_court_info(citation_raw, response_text, case_name)
            
            # Extract holding
            holding = self._extract_holding(response_text, case_name)
            
            # Extract rule/principle
            rule = self._extract_rule(response_text, case_name)
            
            # Extract facts
            facts = self._extract_facts(response_text, case_name)
            
            # Extract reasoning
            reasoning = self._extract_reasoning(response_text, case_name)
            
            # Extract outcome
            outcome = self._extract_outcome(response_text, case_name)
            
            # Analyze relevance
            relevance_p, relevance_d = self._analyze_relevance(holding, rule, facts)
            
            # Create case precedent
            case = CasePrecedent(
                case_name=case_name,
                year=year,
                citation=citation_raw if citation_raw else "Citation pending",
                court=court,
                court_level=court_level,
                holding=holding,
                rule=rule,
                facts=facts,
                reasoning=reasoning,
                relevance_plaintiff=relevance_p,
                relevance_defendant=relevance_d,
                outcome=outcome,
                source_url=citations[0] if citations else None,
                confidence_score=self._calculate_confidence(holding, rule, citation_raw)
            )
            
            cases.append(case)
        
        # If no cases found via pattern, try to extract from text
        if not cases and response_text:
            case = self._extract_generic_case(response_text)
            if case:
                cases.append(case)
        
        return cases
    
    def _extract_year(self, case_name: str, citation: str, text: str) -> str:
        """Extract year from case information."""
        # Try citation first
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', citation) if citation else None
        if year_match:
            return year_match.group(1)
        
        # Try case name context
        case_context = text[max(0, text.find(case_name) - 50):text.find(case_name) + 200] if case_name in text else ""
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', case_context)
        if year_match:
            return year_match.group(1)
        
        return "Year unknown"
    
    def _extract_court_info(self, citation: str, text: str, case_name: str) -> Tuple[str, CourtLevel]:
        """Extract court name and level from citation or text."""
        
        # Check citation for court abbreviations
        if citation:
            if "S. Ct." in citation or "U.S." in citation:
                return "U.S. Supreme Court", CourtLevel.SUPREME_COURT
            elif "F.3d" in citation or "F.2d" in citation:
                return "Federal Circuit Court", CourtLevel.FEDERAL_CIRCUIT
            elif "F. Supp" in citation:
                return "Federal District Court", CourtLevel.FEDERAL_DISTRICT
            
            # Try to extract specific court from parentheses
            court_match = re.search(r'\(([^)]+)\s+\d{4}\)', citation)
            if court_match:
                court_name = court_match.group(1)
                return court_name, self._determine_court_level(court_name)
        
        # Search in text near case name
        if case_name in text:
            context = text[max(0, text.find(case_name) - 100):text.find(case_name) + 300]
            
            # Look for court mentions
            if "Supreme Court" in context:
                if "U.S." in context or "United States" in context:
                    return "U.S. Supreme Court", CourtLevel.SUPREME_COURT
                else:
                    return "State Supreme Court", CourtLevel.STATE_SUPREME
            elif "Circuit" in context:
                circuit_match = re.search(r'(\w+)\s+Circuit', context)
                if circuit_match:
                    return f"{circuit_match.group(1)} Circuit", CourtLevel.FEDERAL_CIRCUIT
            elif "District Court" in context:
                dist_match = re.search(r'([NSEW]\.D\.|[A-Z]\.\s?[A-Z]\.)\s+([A-Z][a-z]+)', context)
                if dist_match:
                    return f"{dist_match.group(0)}", CourtLevel.FEDERAL_DISTRICT
        
        return "Court not specified", CourtLevel.UNKNOWN
    
    def _determine_court_level(self, court_name: str) -> CourtLevel:
        """Determine court level from court name."""
        court_lower = court_name.lower()
        
        if "supreme" in court_lower:
            if "u.s." in court_lower or "united states" in court_lower:
                return CourtLevel.SUPREME_COURT
            return CourtLevel.STATE_SUPREME
        elif "circuit" in court_lower or "cir." in court_lower:
            return CourtLevel.FEDERAL_CIRCUIT
        elif "district" in court_lower or "d." in court_lower:
            return CourtLevel.FEDERAL_DISTRICT
        elif "appeals" in court_lower or "app." in court_lower:
            return CourtLevel.STATE_APPEALS
        
        return CourtLevel.UNKNOWN
    
    def _extract_holding(self, text: str, case_name: str) -> str:
        """Extract the court's holding from text."""
        
        holding_keywords = [
            "held that", "holding", "court held", "we hold",
            "ruled that", "court ruled", "found that",
            "concluded that", "determined that", "decided"
        ]
        
        # Find context around case name
        if case_name and case_name in text:
            case_context = text[text.find(case_name):min(len(text), text.find(case_name) + 1000)]
        else:
            case_context = text
        
        for keyword in holding_keywords:
            pattern = rf'{keyword}[:\s]+([^.]+\.)'
            match = re.search(pattern, case_context, re.IGNORECASE)
            if match:
                holding = match.group(1).strip()
                # Clean up the holding
                holding = re.sub(r'\s+', ' ', holding)
                return holding[:300] if len(holding) > 300 else holding
        
        # Fallback: look for injunction, dismissal, etc.
        outcome_patterns = [
            r'(granted\s+(?:preliminary\s+)?injunction[^.]*\.)',
            r'(dismissed\s+(?:the\s+)?(?:case|complaint|action)[^.]*\.)',
            r'(affirmed[^.]*\.)',
            r'(reversed[^.]*\.)',
            r'(remanded[^.]*\.)'
        ]
        
        for pattern in outcome_patterns:
            match = re.search(pattern, case_context, re.IGNORECASE)
            if match:
                return f"Court {match.group(1)}"
        
        return "Holding not clearly stated"
    
    def _extract_rule(self, text: str, case_name: str) -> str:
        """Extract the legal rule or principle from text."""
        
        rule_keywords = [
            "rule is", "principle is", "law is", "standard is",
            "test is", "doctrine", "establishes that", "requires",
            "must show", "elements are", "factors include"
        ]
        
        # Find context around case name or holding
        if case_name and case_name in text:
            case_context = text[text.find(case_name):min(len(text), text.find(case_name) + 1500)]
        else:
            case_context = text
        
        for keyword in rule_keywords:
            pattern = rf'{keyword}[:\s]+([^.]+\.)'
            match = re.search(pattern, case_context, re.IGNORECASE)
            if match:
                rule = match.group(1).strip()
                rule = re.sub(r'\s+', ' ', rule)
                return rule[:400] if len(rule) > 400 else rule
        
        # Look for legal tests or standards
        test_pattern = r'(?:three|four|five)[-\s](?:part|prong|factor)\s+test[^.]*\.'
        match = re.search(test_pattern, case_context, re.IGNORECASE)
        if match:
            return match.group(0)
        
        # Look for "more likely" patterns
        likelihood_pattern = r'(?:misappropriation|liability|violation)\s+(?:is\s+)?more\s+likely\s+when[^.]+\.'
        match = re.search(likelihood_pattern, case_context, re.IGNORECASE)
        if match:
            return match.group(0)
        
        return "Legal principle to be determined from full opinion"
    
    def _extract_facts(self, text: str, case_name: str) -> Optional[str]:
        """Extract key facts of the case."""
        
        fact_keywords = [
            "facts", "defendant", "plaintiff", "employee",
            "downloaded", "copied", "stole", "misappropriated",
            "confidential", "trade secret", "proprietary"
        ]
        
        facts = []
        
        # Find case context
        if case_name and case_name in text:
            case_context = text[max(0, text.find(case_name) - 200):text.find(case_name) + 800]
        else:
            case_context = text[:1000]
        
        # Look for factual statements
        for keyword in fact_keywords:
            if keyword in case_context.lower():
                # Extract sentence containing keyword
                sentences = case_context.split('.')
                for sent in sentences:
                    if keyword in sent.lower() and len(sent) > 20:
                        facts.append(sent.strip())
                        break
        
        if facts:
            return ". ".join(facts[:3])[:400]
        
        return None
    
    def _extract_reasoning(self, text: str, case_name: str) -> Optional[str]:
        """Extract the court's reasoning."""
        
        reasoning_keywords = [
            "because", "reasoned that", "reasoning", "rationale",
            "based on", "in light of", "considering", "given that"
        ]
        
        if case_name and case_name in text:
            case_context = text[text.find(case_name):min(len(text), text.find(case_name) + 1000)]
        else:
            case_context = text
        
        for keyword in reasoning_keywords:
            pattern = rf'{keyword}[:\s]+([^.]+\.)'
            match = re.search(pattern, case_context, re.IGNORECASE)
            if match:
                reasoning = match.group(1).strip()
                return reasoning[:300] if len(reasoning) > 300 else reasoning
        
        return None
    
    def _extract_outcome(self, text: str, case_name: str) -> Optional[str]:
        """Extract the case outcome."""
        
        outcome_keywords = [
            "granted", "denied", "affirmed", "reversed",
            "remanded", "dismissed", "settled", "upheld"
        ]
        
        if case_name and case_name in text:
            case_context = text[text.find(case_name):min(len(text), text.find(case_name) + 500)]
        else:
            case_context = text
        
        for keyword in outcome_keywords:
            if keyword in case_context.lower():
                # Extract the outcome phrase
                pattern = rf'\b{keyword}\b[^.]*'
                match = re.search(pattern, case_context, re.IGNORECASE)
                if match:
                    return match.group(0).strip()[:100]
        
        return None
    
    def _analyze_relevance(self, holding: str, rule: str, facts: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """Analyze relevance for plaintiff and defendant."""
        
        combined_text = f"{holding} {rule} {facts or ''}"
        
        relevance_plaintiff = None
        relevance_defendant = None
        
        # Plaintiff-favorable indicators
        plaintiff_indicators = [
            "granted injunction", "found misappropriation", "liable",
            "violated", "breached", "infringed", "wrongful"
        ]
        
        # Defendant-favorable indicators
        defendant_indicators = [
            "denied injunction", "dismissed", "no misappropriation",
            "not liable", "justified", "legitimate", "no violation"
        ]
        
        combined_lower = combined_text.lower()
        
        # Check for plaintiff-favorable outcomes
        for indicator in plaintiff_indicators:
            if indicator in combined_lower:
                relevance_plaintiff = "Supports plaintiff's position"
                break
        
        # Check for defendant-favorable outcomes
        for indicator in defendant_indicators:
            if indicator in combined_lower:
                relevance_defendant = "Supports defendant's position"
                break
        
        # More nuanced analysis based on conditions
        if "if" in combined_lower or "when" in combined_lower or "unless" in combined_lower:
            if not relevance_plaintiff:
                relevance_plaintiff = "Supports plaintiff if conditions met"
            if not relevance_defendant:
                relevance_defendant = "Supports defense if conditions differ"
        
        return relevance_plaintiff, relevance_defendant
    
    def _calculate_confidence(self, holding: str, rule: str, citation: str) -> float:
        """Calculate confidence score for the extracted case."""
        
        score = 0.0
        
        # Check completeness of information
        if holding and holding != "Holding not clearly stated":
            score += 0.3
        if rule and rule != "Legal principle to be determined from full opinion":
            score += 0.3
        if citation and citation != "Citation pending":
            score += 0.2
        if len(holding) > 50:
            score += 0.1
        if len(rule) > 50:
            score += 0.1
        
        return min(score, 1.0)
    
    def _extract_generic_case(self, text: str) -> Optional[CasePrecedent]:
        """Extract a generic case when specific pattern matching fails."""
        
        # Try to extract any case-like information
        holding = self._extract_holding(text, "")
        rule = self._extract_rule(text, "")
        
        if holding or rule:
            return CasePrecedent(
                case_name="Case name not specified",
                year="Year unknown",
                citation="Citation pending",
                court="Court not specified",
                court_level=CourtLevel.UNKNOWN,
                holding=holding or "Holding not specified",
                rule=rule or "Rule not specified",
                confidence_score=0.3
            )
        
        return None
    
    def _generate_mini_doc(self, case: CasePrecedent) -> str:
        """Generate a mini-doc summary for the case."""
        
        lines = []
        
        # Header
        lines.append(f"{'='*60}")
        lines.append(f"CASE: {case.case_name} ({case.year})")
        lines.append(f"{'='*60}")
        
        # Citation
        lines.append(f"Citation: {case.court}, {case.year if case.year != 'Year unknown' else ''}")
        if case.citation != "Citation pending":
            lines.append(f"         {case.citation}")
        
        # Holding
        lines.append(f"\nHolding: {case.holding}")
        
        # Rule
        lines.append(f"\nRule: {case.rule}")
        
        # Facts (if available)
        if case.facts:
            lines.append(f"\nKey Facts: {case.facts}")
        
        # Reasoning (if available)
        if case.reasoning:
            lines.append(f"\nReasoning: {case.reasoning}")
        
        # Relevance
        if case.relevance_plaintiff or case.relevance_defendant:
            lines.append("\nRelevance:")
            if case.relevance_plaintiff:
                lines.append(f"  • Plaintiff: {case.relevance_plaintiff}")
            if case.relevance_defendant:
                lines.append(f"  • Defendant: {case.relevance_defendant}")
        
        # Confidence
        lines.append(f"\n[Confidence: {case.confidence_score:.0%}]")
        
        return "\n".join(lines)
    
    def find_precedents_enhanced(self,
                                query: str,
                                jurisdiction: str = "federal",
                                num_cases: int = 3,
                                year_range: Optional[Tuple[int, int]] = None,
                                deep_search: bool = True) -> CaseSearchResult:
        """
        Enhanced precedent search using both Perplexity (for discovery) and Browser Use (for details).
        
        This method first uses Perplexity to identify relevant cases, then uses Browser Use
        to get detailed, accurate information from JUSTIA US Law.
        
        Args:
            query: Description of the legal issue or case type
            jurisdiction: "federal", "state", or specific state/circuit
            num_cases: Number of cases to return (max 3 for Browser Use efficiency)
            year_range: Optional tuple of (start_year, end_year)
            deep_search: If True, use Browser Use to get detailed info from JUSTIA
            
        Returns:
            CaseSearchResult with detailed precedents
        """
        # Step 1: Use Perplexity to identify relevant cases
        print(f"[Step 1] Using Perplexity to identify relevant cases...")
        initial_result = self.find_precedents(
            query=query,
            jurisdiction=jurisdiction,
            num_cases=num_cases * 2,  # Get more cases initially for better selection
            year_range=year_range
        )
        
        if not initial_result.cases or not deep_search or not self.browser:
            return initial_result
        
        # Step 2: For each identified case, get detailed info from JUSTIA
        print(f"[Step 2] Using Browser Use to get detailed information from JUSTIA...")
        enhanced_cases = []
        
        for case in initial_result.cases[:num_cases]:  # Limit to requested number
            try:
                print(f"  - Fetching details for: {case.case_name}")
                
                # Generate intelligent query for Browser Use based on Perplexity results
                browser_query = self._generate_browser_query(case, query)
                
                # Get detailed case info from JUSTIA
                detailed_info = self.browser.search_case_on_justia(
                    custom_query=browser_query
                )
                
                # Parse the Browser Use response and enhance the case object
                enhanced_case = self._enhance_case_with_browser_data(case, detailed_info)
                enhanced_cases.append(enhanced_case)
                
            except Exception as e:
                print(f"    Warning: Could not enhance {case.case_name}: {e}")
                enhanced_cases.append(case)  # Keep original if enhancement fails
        
        # Create enhanced result
        enhanced_result = CaseSearchResult(
            query=query,
            jurisdiction=jurisdiction,
            cases=enhanced_cases,
            search_date=datetime.now().isoformat(),
            total_found=len(enhanced_cases)
        )
        
        # Update cache
        cache_key = f"enhanced_{query}_{jurisdiction}_{num_cases}_{year_range}"
        if self.cache is not None:
            self.cache[cache_key] = enhanced_result
        
        return enhanced_result
    
    def _generate_browser_query(self, case: CasePrecedent, original_query: str) -> str:
        """
        Generate an optimized Browser Use query based on Perplexity results.
        
        Args:
            case: CasePrecedent from Perplexity search
            original_query: The original user query
            
        Returns:
            Optimized query string for Browser Use
        """
        # Build a specific query for JUSTIA based on what we know
        query_parts = [
            "Go to JUSTIA US Law (justia.com/cases).",
            f"Search for the case: {case.case_name}."
        ]
        
        # Add year if known
        if case.year and case.year != "Year unknown":
            query_parts.append(f"The case was decided around {case.year}.")
        
        # Add court if known
        if case.court and case.court != "Court not specified":
            query_parts.append(f"It was decided by {case.court}.")
        
        # Add context about what we're looking for
        query_parts.append(f"This case is relevant to: {original_query}.")
        
        # Specify what to extract
        query_parts.append(
            "Extract: 1) Full case citation with reporter reference, "
            "2) Year decided, 3) Court name, "
            "4) The complete holding (this is critical - look for 'Held:' or 'Holding:' sections), "
            "5) Key facts (2-3 sentences), 6) The legal rule or test established, "
            "7) The outcome (affirmed/reversed/remanded/etc), "
            "8) Any notable dissenting opinions, "
            "9) Procedural posture (how the case got to this court)."
        )
        
        return " ".join(query_parts)
    
    def _enhance_case_with_browser_data(self, original_case: CasePrecedent, browser_data: str) -> CasePrecedent:
        """
        Enhance a CasePrecedent object with detailed data from Browser Use.
        
        Args:
            original_case: The original case from Perplexity
            browser_data: Raw text response from Browser Use/JUSTIA
            
        Returns:
            Enhanced CasePrecedent object
        """
        # Create a copy of the original case
        enhanced_case = CasePrecedent(
            case_name=original_case.case_name,
            year=original_case.year,
            citation=original_case.citation,
            court=original_case.court,
            court_level=original_case.court_level,
            holding=original_case.holding,
            rule=original_case.rule,
            facts=original_case.facts,
            reasoning=original_case.reasoning,
            dissent=original_case.dissent,
            relevance_plaintiff=original_case.relevance_plaintiff,
            relevance_defendant=original_case.relevance_defendant,
            procedural_posture=original_case.procedural_posture,
            outcome=original_case.outcome,
            mini_doc=original_case.mini_doc,
            source_url="justia.com/cases",
            confidence_score=0.95  # High confidence for JUSTIA data
        )
        
        # Parse Browser Use response for better citation
        citation_pattern = r'(?:Citation:?|Case citation:?)[:\s]*([^\n]+)'
        citation_match = re.search(citation_pattern, browser_data, re.IGNORECASE)
        if citation_match:
            enhanced_case.citation = citation_match.group(1).strip()
        
        # Extract better holding
        holding_patterns = [
            r'(?:Holding:?|Held:?|The court held)[:\s]*([^\n]+(?:\n[^\n]+){0,2})',
            r'(?:HOLDING)[:\s]*([^\.]+\.(?:[^\.]+\.)?)'
        ]
        for pattern in holding_patterns:
            holding_match = re.search(pattern, browser_data, re.IGNORECASE | re.MULTILINE)
            if holding_match:
                enhanced_case.holding = holding_match.group(1).strip()
                break
        
        # Extract facts if available
        facts_pattern = r'(?:Facts:?|Key facts:?|Brief facts:?)[:\s]*([^\n]+(?:\n[^\n]+){0,2})'
        facts_match = re.search(facts_pattern, browser_data, re.IGNORECASE)
        if facts_match:
            enhanced_case.facts = facts_match.group(1).strip()
        
        # Extract procedural posture
        proc_pattern = r'(?:Procedural posture:?|Procedural history:?)[:\s]*([^\n]+)'
        proc_match = re.search(proc_pattern, browser_data, re.IGNORECASE)
        if proc_match:
            enhanced_case.procedural_posture = proc_match.group(1).strip()
        
        # Extract dissent if present
        dissent_pattern = r'(?:Dissent:?|Dissenting opinion:?)[:\s]*([^\n]+(?:\n[^\n]+){0,1})'
        dissent_match = re.search(dissent_pattern, browser_data, re.IGNORECASE)
        if dissent_match:
            enhanced_case.dissent = dissent_match.group(1).strip()
        
        # Extract outcome
        outcome_pattern = r'(?:Outcome:?|Result:?|Disposition:?)[:\s]*([^\n]+)'
        outcome_match = re.search(outcome_pattern, browser_data, re.IGNORECASE)
        if outcome_match:
            enhanced_case.outcome = outcome_match.group(1).strip()
        
        # Generate enhanced mini-doc
        enhanced_case.mini_doc = self._generate_enhanced_mini_doc(enhanced_case)
        
        return enhanced_case
    
    def _generate_enhanced_mini_doc(self, case: CasePrecedent) -> str:
        """Generate an enhanced mini-doc with JUSTIA data."""
        lines = []
        
        # Header
        lines.append(f"{'='*60}")
        lines.append(f"CASE: {case.case_name} ({case.year})")
        lines.append(f"[SOURCE: JUSTIA US Law - High Confidence]")
        lines.append(f"{'='*60}")
        
        # Citation
        lines.append(f"Citation: {case.citation}")
        lines.append(f"Court: {case.court}")
        
        # Procedural posture
        if case.procedural_posture:
            lines.append(f"\nProcedural Posture: {case.procedural_posture}")
        
        # Facts
        if case.facts:
            lines.append(f"\nKey Facts: {case.facts}")
        
        # Holding
        lines.append(f"\nHolding: {case.holding}")
        
        # Rule
        lines.append(f"\nRule of Law: {case.rule}")
        
        # Reasoning
        if case.reasoning:
            lines.append(f"\nReasoning: {case.reasoning}")
        
        # Outcome
        if case.outcome:
            lines.append(f"\nOutcome: {case.outcome}")
        
        # Dissent
        if case.dissent:
            lines.append(f"\nDissent: {case.dissent}")
        
        # Relevance
        if case.relevance_plaintiff or case.relevance_defendant:
            lines.append("\nCase Relevance:")
            if case.relevance_plaintiff:
                lines.append(f"  • For Plaintiff: {case.relevance_plaintiff}")
            if case.relevance_defendant:
                lines.append(f"  • For Defendant: {case.relevance_defendant}")
        
        # Confidence
        lines.append(f"\n[Data Quality: JUSTIA Direct - {case.confidence_score:.0%} Confidence]")
        
        return "\n".join(lines)
    
    def quick_search(self, query: str, use_browser: Optional[bool] = None) -> str:
        """
        Quick precedent search that returns a concise mini-doc.
        
        Args:
            query: Natural language query about a case or legal issue
            use_browser: Override the default browser setting for this search
            
        Returns:
            Mini-doc formatted string
        """
        # Determine whether to use browser for this search
        use_browser = use_browser if use_browser is not None else self.use_browser
        
        if use_browser and self.browser:
            # Use enhanced search for better results
            result = self.find_precedents_enhanced(query, num_cases=1, deep_search=True)
        else:
            # Use standard Perplexity search
            result = self.find_precedents(query, num_cases=1)
        
        if result.cases:
            case = result.cases[0]
            # Return condensed mini-doc
            mini_doc = f"Case: {case.case_name} ({case.year})\n"
            mini_doc += f"Citation: {case.court}, {case.year}\n"
            if case.citation != "Citation pending":
                mini_doc += f"         {case.citation}\n"
            mini_doc += f"Holding: {case.holding}\n"
            mini_doc += f"Rule: {case.rule}"
            
            if case.relevance_plaintiff:
                mini_doc += f"\nRelevance: {case.relevance_plaintiff}"
                if case.relevance_defendant:
                    mini_doc += f"; {case.relevance_defendant}"
            
            if use_browser:
                mini_doc += "\n[Source: JUSTIA US Law]"
            
            return mini_doc
        
        return "No relevant precedents found for this query."
    
    def find_similar_cases(self,
                          case_name: str,
                          num_similar: int = 5) -> List[CasePrecedent]:
        """
        Find cases similar to a given case.
        
        Args:
            case_name: Name of the case to find similar cases for
            num_similar: Number of similar cases to find
            
        Returns:
            List of similar case precedents
        """
        query = f"cases similar to {case_name} same legal issue principle"
        result = self.find_precedents(query, num_cases=num_similar)
        return result.cases
    
    def analyze_circuit_split(self,
                            legal_issue: str) -> Dict[str, List[CasePrecedent]]:
        """
        Analyze circuit splits on a legal issue.
        
        Args:
            legal_issue: The legal issue to analyze
            
        Returns:
            Dictionary mapping circuits to their precedents
        """
        circuits = ["First", "Second", "Third", "Fourth", "Fifth", 
                   "Sixth", "Seventh", "Eighth", "Ninth", "Tenth", 
                   "Eleventh", "D.C.", "Federal"]
        
        circuit_cases = {}
        
        for circuit in circuits[:3]:  # Limit to avoid too many API calls
            query = f"{circuit} Circuit {legal_issue}"
            result = self.find_precedents(query, jurisdiction=f"{circuit} Circuit", num_cases=2)
            if result.cases:
                circuit_cases[circuit] = result.cases
        
        return circuit_cases
    
    def get_landmark_cases(self,
                          area_of_law: str,
                          num_cases: int = 10) -> List[CasePrecedent]:
        """
        Get landmark cases in a specific area of law.
        
        Args:
            area_of_law: The area of law (e.g., "trade secrets", "copyright")
            num_cases: Number of landmark cases to retrieve
            
        Returns:
            List of landmark case precedents
        """
        query = f"landmark seminal important cases {area_of_law} precedent"
        result = self.find_precedents(query, num_cases=num_cases)
        
        # Sort by confidence score to get most relevant
        result.cases.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return result.cases
    
    def compare_precedents(self,
                          case1_name: str,
                          case2_name: str) -> Dict[str, Any]:
        """
        Compare two precedents.
        
        Args:
            case1_name: First case name
            case2_name: Second case name
            
        Returns:
            Comparison analysis
        """
        # Search for both cases
        case1_result = self.find_precedents(case1_name, num_cases=1)
        case2_result = self.find_precedents(case2_name, num_cases=1)
        
        case1 = case1_result.cases[0] if case1_result.cases else None
        case2 = case2_result.cases[0] if case2_result.cases else None
        
        if not case1 or not case2:
            return {"error": "Could not find one or both cases"}
        
        comparison = {
            "case1": {
                "name": case1.case_name,
                "year": case1.year,
                "holding": case1.holding,
                "rule": case1.rule
            },
            "case2": {
                "name": case2.case_name,
                "year": case2.year,
                "holding": case2.holding,
                "rule": case2.rule
            },
            "similarities": [],
            "differences": [],
            "reconciliation": ""
        }
        
        # Analyze similarities and differences
        if case1.court_level == case2.court_level:
            comparison["similarities"].append(f"Both at {case1.court_level.value} level")
        else:
            comparison["differences"].append(f"Different court levels: {case1.court_level.value} vs {case2.court_level.value}")
        
        # Compare holdings
        if any(word in case1.holding.lower() and word in case2.holding.lower() 
               for word in ["granted", "denied", "affirmed", "reversed"]):
            comparison["similarities"].append("Similar outcomes")
        
        return comparison
    
    def export_research(self,
                       filename: str = None,
                       format: str = "json") -> str:
        """
        Export precedent research to file.
        
        Args:
            filename: Output filename
            format: Export format ("json" or "markdown")
            
        Returns:
            Path to exported file
        """
        import json
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"precedent_research_{timestamp}.{format}"
        
        export_data = {
            "agent": self.name,
            "export_date": datetime.now().isoformat(),
            "search_history": self.search_history,
            "cached_cases": []
        }
        
        # Include cached results if available
        if self.cache:
            for key, result in self.cache.items():
                for case in result.cases:
                    export_data["cached_cases"].append({
                        "case_name": case.case_name,
                        "year": case.year,
                        "citation": case.citation,
                        "court": case.court,
                        "holding": case.holding,
                        "rule": case.rule,
                        "confidence": case.confidence_score
                    })
        
        if format == "json":
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
        
        elif format == "markdown":
            with open(filename, 'w') as f:
                f.write(f"# Precedent Research Export\n\n")
                f.write(f"**Agent**: {export_data['agent']}\n")
                f.write(f"**Date**: {export_data['export_date']}\n\n")
                
                f.write("## Search History\n\n")
                for search in export_data['search_history']:
                    f.write(f"- **{search['timestamp']}**: {search['query']} → {search['cases_found']} cases\n")
                
                f.write("\n## Cases Found\n\n")
                for case in export_data['cached_cases']:
                    f.write(f"### {case['case_name']} ({case['year']})\n")
                    f.write(f"- **Court**: {case['court']}\n")
                    f.write(f"- **Citation**: {case['citation']}\n")
                    f.write(f"- **Holding**: {case['holding']}\n")
                    f.write(f"- **Rule**: {case['rule']}\n")
                    f.write(f"- **Confidence**: {case['confidence']:.0%}\n\n")
        
        return filename


# Example usage and testing
if __name__ == "__main__":
    # Initialize the Precedent Agent with Browser Use enabled
    print("Initializing Precedent Agent with Browser Use...")
    print("This will use JUSTIA US Law for detailed case information")
    precedent_agent = PrecedentAgent(use_browser=True)  # Enable Browser Use
    
    # Example 1: Quick search for trade secret case (with Browser Use)
    print("\n" + "="*60)
    print("Example 1: Trade Secret Misappropriation Case (Enhanced)")
    print("="*60)
    
    query = "Find a famous case involving trade secret misappropriation"
    print(f"\nQuery: {query}")
    print("Using Browser Use to get detailed info from JUSTIA...")
    result = precedent_agent.quick_search(query, use_browser=True)
    print(f"\nResult:\n{result}\n")
    
    # Example 2: Find multiple precedents (Enhanced with Browser Use)
    print("="*60)
    print("Example 2: Multiple Precedents (Enhanced with JUSTIA)")
    print("="*60)
    
    print("\nUsing enhanced search (Perplexity + Browser Use)...")
    search_result = precedent_agent.find_precedents_enhanced(
        "employee downloaded confidential files trade secret",
        jurisdiction="federal",
        num_cases=2,  # Limit to 2 for efficiency with Browser Use
        deep_search=True  # Enable Browser Use for detailed info
    )
    
    print(f"\nFound {search_result.total_found} enhanced cases from JUSTIA:")
    for case in search_result.cases:
        print(f"\n{case.mini_doc}\n")
    
    # Example 3: Find landmark cases (Enhanced)
    print("="*60)
    print("Example 3: Landmark Trade Secret Cases (Enhanced)")
    print("="*60)
    
    print("\nSearching for landmark cases with enhanced details...")
    # Use enhanced search for landmark cases
    landmark_result = precedent_agent.find_precedents_enhanced(
        "landmark trade secret cases technology companies",
        jurisdiction="federal",
        num_cases=2,
        deep_search=True
    )
    print(f"\nLandmark cases in trade secret law (from JUSTIA):")
    for case in landmark_result.cases:
        print(f"\n• {case.case_name} ({case.year})")
        print(f"  Court: {case.court}")
        print(f"  Citation: {case.citation}")
        print(f"  {case.holding[:150]}...")
        print(f"  [Source: {case.source_url}]")
    
    # Example 4: Compare precedents (using enhanced data)
    print("\n"+"="*60)
    print("Example 4: Compare Cases (with JUSTIA data)")
    print("="*60)
    
    print("\nGetting enhanced data for case comparison...")
    # First get enhanced data for each case
    waymo_result = precedent_agent.find_precedents_enhanced("Waymo v. Uber", num_cases=1, deep_search=True)
    dupont_result = precedent_agent.find_precedents_enhanced("E.I. DuPont v. Kolon", num_cases=1, deep_search=True)
    
    comparison = precedent_agent.compare_precedents("Waymo v. Uber", "E.I. DuPont v. Kolon")
    if "error" not in comparison:
        print(f"\nComparing cases:")
        print(f"1. {comparison['case1']['name']} ({comparison['case1']['year']})")
        print(f"2. {comparison['case2']['name']} ({comparison['case2']['year']})")
        if comparison['similarities']:
            print(f"\nSimilarities: {', '.join(comparison['similarities'])}")
        if comparison['differences']:
            print(f"Differences: {', '.join(comparison['differences'])}")
    
    print("\n" + "="*60)
    print("Examples complete!")
    print("All tests now use Browser Use for enhanced JUSTIA data!")
    print("="*60)
    print("\n💡 Note: Browser Use provides more accurate citations, holdings,")
    print("   and case details directly from JUSTIA US Law.")
