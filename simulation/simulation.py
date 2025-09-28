"""
Legal Case Simulation Framework
================================
A multi-agent system for simulating legal proceedings with prosecution,
defense, and judicial agents. Supports Monte Carlo simulations for
strategy exploration.
"""

import os
import sys
import json
import random
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import asyncio

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.baseAgent import BaseAgent, MessageRole
from agents.precedentAgent import PrecedentAgent, CasePrecedent
from agents.statuteAgent import StatuteAgent, StatuteInfo
import google.generativeai as genai


class ArgumentType(Enum):
    """Types of legal arguments"""
    OPENING = "opening"
    REBUTTAL = "rebuttal"
    CLOSING = "closing"


class VerdictOutcome(Enum):
    """Possible verdict outcomes"""
    PLAINTIFF_WIN = 1
    DEFENSE_WIN = 0
    SETTLEMENT = 0.5


@dataclass
class CaseEvidence:
    """Evidence packet for a legal case"""
    case_description: str
    jurisdiction: str = "Federal"
    
    # Key case variables
    has_nda: bool = True
    evidence_strength: str = "strong"  # weak, moderate, strong
    venue_bias: str = "neutral"  # plaintiff-friendly, defendant-friendly, neutral
    
    # Evidence collected
    statutes: List[StatuteInfo] = field(default_factory=list)
    precedents: List[CasePrecedent] = field(default_factory=list)
    facts: List[str] = field(default_factory=list)
    documents: List[str] = field(default_factory=list)
    
    # Additional context
    plaintiff_claims: List[str] = field(default_factory=list)
    defendant_claims: List[str] = field(default_factory=list)
    disputed_facts: List[str] = field(default_factory=list)


@dataclass
class LegalArgument:
    """Structured legal argument"""
    agent_name: str
    argument_type: ArgumentType
    main_argument: str
    cited_statutes: List[str]
    cited_precedents: List[str]
    key_points: List[str]
    conclusion: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Verdict:
    """Judge's verdict with reasoning"""
    outcome: VerdictOutcome
    winner: str  # "plaintiff" or "defendant"
    rationale: str
    key_factors: List[str]
    cited_authorities: List[str]
    confidence_score: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ProsecutorAgent(BaseAgent):
    """
    Prosecutor/Plaintiff Agent - Argues for misappropriation using statute and precedent.
    """
    
    def __init__(self, 
                 name: str = "Prosecutor",
                 strategy: str = "aggressive",
                 **kwargs):
        """
        Initialize Prosecutor Agent.
        
        Args:
            name: Agent name
            strategy: Legal strategy (aggressive, moderate, conservative)
        """
        self.strategy = strategy
        
        # Define strategy-specific prompts
        strategy_prompts = {
            "aggressive": """You are an aggressive prosecutor arguing for trade secret misappropriation.
            You emphasize every piece of evidence strongly, cite maximum precedents, and push for the 
            harshest remedies. You interpret facts in the light most favorable to the plaintiff.""",
            
            "moderate": """You are a balanced prosecutor arguing for trade secret misappropriation.
            You present evidence fairly but firmly, cite relevant precedents appropriately, and seek
            reasonable remedies. You focus on the strongest aspects of your case.""",
            
            "conservative": """You are a cautious prosecutor arguing for trade secret misappropriation.
            You focus only on the most clear-cut evidence, cite only the most directly relevant precedents,
            and seek modest remedies. You acknowledge weaknesses while emphasizing strengths."""
        }
        
        system_prompt = strategy_prompts.get(strategy, strategy_prompts["moderate"])
        system_prompt += """
        
        When making arguments:
        1. Always cite specific statutes (e.g., DTSA, UTSA) and their relevant provisions
        2. Reference case precedents with full citations
        3. Connect facts directly to legal standards
        4. Address burden of proof requirements
        5. Propose specific remedies and damages
        
        Structure arguments clearly with: opening statement, legal framework, 
        application to facts, and conclusion."""
        
        super().__init__(
            name=name,
            system_prompt=system_prompt,
            temperature=0.3,  # Lower temperature for consistent legal reasoning
            enable_tools=False,  # No need for web tools during argument
            **kwargs
        )
    
    def make_opening_argument(self, evidence: CaseEvidence) -> LegalArgument:
        """
        Generate opening argument based on evidence.
        
        Args:
            evidence: Case evidence packet
            
        Returns:
            Structured legal argument
        """
        # Prepare evidence summary
        evidence_summary = self._prepare_evidence_summary(evidence)
        
        prompt = f"""Based on the following case evidence, make a strong opening argument 
        for trade secret misappropriation:

        {evidence_summary}

        Generate your opening argument in the following JSON format:
        {{
            "main_argument": "Your primary argument (max 500 characters)",
            "key_points": ["point 1", "point 2", "point 3", "point 4", "point 5"],
            "cited_statutes": ["DTSA § 1836", "UTSA § 1", ...],
            "cited_precedents": ["Case1 v. Case2", ...],
            "conclusion": "Your concluding statement (max 200 characters)"
        }}
        
        Requirements:
        1. State the plaintiff's core claims in main_argument
        2. Include relevant DTSA/UTSA provisions in cited_statutes
        3. Reference supportive case precedents in cited_precedents
        4. Highlight key evidence in key_points
        5. Preview remedies sought in conclusion
        
        Return only valid JSON, no additional text."""
        
        # Use generate_with_completion for automatic truncation handling
        response = self.generate_with_completion(prompt)
        
        # Parse JSON response into structured format
        argument = self._parse_json_argument(response, ArgumentType.OPENING)
        return argument
    
    def make_rebuttal(self, 
                     defense_argument: LegalArgument,
                     evidence: CaseEvidence) -> LegalArgument:
        """
        Generate rebuttal to defense argument.
        
        Args:
            defense_argument: The defense's argument to rebut
            evidence: Case evidence packet
            
        Returns:
            Structured rebuttal argument
        """
        prompt = f"""The defense has argued:
        {defense_argument.main_argument}

        Key points raised:
        {', '.join(defense_argument.key_points)}

        Generate your rebuttal in the following JSON format:
        {{
            "main_argument": "Your primary rebuttal argument (max 500 characters)",
            "key_points": ["rebuttal point 1", "rebuttal point 2", ...],
            "cited_statutes": ["DTSA § 1836", "UTSA § 1", ...],
            "cited_precedents": ["Case1 v. Case2", ...],
            "conclusion": "Your concluding rebuttal statement (max 200 characters)"
        }}
        
        Requirements:
        1. Directly address each defense claim in main_argument
        2. Reinforce statutory violations in cited_statutes
        3. Distinguish unfavorable precedents in cited_precedents
        4. Emphasize evidence supporting misappropriation in key_points
        5. Maintain focus on legal standards in conclusion
        
        Return only valid JSON, no additional text."""
        
        # Use generate_with_completion for automatic truncation handling
        response = self.generate_with_completion(prompt)
        
        argument = self._parse_json_argument(response, ArgumentType.REBUTTAL)
        return argument
    
    def _prepare_evidence_summary(self, evidence: CaseEvidence) -> str:
        """Prepare a summary of evidence for argument generation."""
        summary = f"""
        CASE: {evidence.case_description}
        JURISDICTION: {evidence.jurisdiction}
        
        KEY FACTORS:
        - NDA Present: {evidence.has_nda}
        - Evidence Strength: {evidence.evidence_strength}
        - Venue: {evidence.venue_bias}
        
        APPLICABLE STATUTES:
        """
        
        for statute in evidence.statutes[:3]:  # Top 3 statutes
            summary += f"\n- {statute.citation}: {statute.title}"
            if statute.key_provisions:
                summary += f"\n  Key provisions: {', '.join(statute.key_provisions[:2])}"
        
        summary += "\n\nRELEVANT PRECEDENTS:"
        for precedent in evidence.precedents[:3]:  # Top 3 precedents
            summary += f"\n- {precedent.case_name} ({precedent.year}): {precedent.holding[:150]}..."
        
        if evidence.facts:
            summary += f"\n\nKEY FACTS:\n" + "\n".join(f"- {fact}" for fact in evidence.facts[:5])
        
        if evidence.plaintiff_claims:
            summary += f"\n\nPLAINTIFF CLAIMS:\n" + "\n".join(f"- {claim}" for claim in evidence.plaintiff_claims)
        
        return summary
    
    def _parse_json_argument(self, response: str, arg_type: ArgumentType) -> LegalArgument:
        """Parse JSON AI response into structured argument using enhanced JSON repair."""
        # Use BaseAgent's repair_json method for robust parsing
        try:
            data = self.repair_json(response)
            
            return LegalArgument(
                agent_name=self.name,
                argument_type=arg_type,
                main_argument=data.get('main_argument', ''),
                cited_statutes=data.get('cited_statutes', []),
                cited_precedents=data.get('cited_precedents', []),
                key_points=data.get('key_points', [])[:5],  # Keep reasonable limit on key points
                conclusion=data.get('conclusion', '')
            )
            
        except Exception as e:
            # Fallback to basic parsing if JSON repair fails
            print(f"Warning: Failed to parse argument JSON even with repair: {e}")
            
            # Try to extract partial data
            partial_data = self.extract_partial_json(response)
            if partial_data:
                return LegalArgument(
                    agent_name=self.name,
                    argument_type=arg_type,
                    main_argument=partial_data.get('main_argument', response),
                    cited_statutes=partial_data.get('cited_statutes', []),
                    cited_precedents=partial_data.get('cited_precedents', []),
                    key_points=partial_data.get('key_points', [response])[:5],
                    conclusion=partial_data.get('conclusion', '')
                )
            
            # Last resort: use raw response
            return LegalArgument(
                agent_name=self.name,
                argument_type=arg_type,
                main_argument=response,
                cited_statutes=[],
                cited_precedents=[],
                key_points=[response],
                conclusion=""
            )
    
    def _parse_argument(self, response: str, arg_type: ArgumentType) -> LegalArgument:
        """Legacy regex-based parsing - deprecated, use _parse_json_argument instead."""
        # Extract citations using regex
        statute_pattern = r'(?:DTSA|UTSA|USC|U\.S\.C\.|CFR)[^,;.]*'
        case_pattern = r'(?:[A-Z][a-z]+ v\. [A-Z][a-z]+)[^,;.]*'
        
        cited_statutes = list(set(re.findall(statute_pattern, response)))
        cited_precedents = list(set(re.findall(case_pattern, response)))
        
        # Extract key points (sentences starting with numbers or bullets)
        point_pattern = r'(?:^|\n)(?:\d+\.|-|\*)\s*([^.\n]+\.)'
        key_points = [match.strip() for match in re.findall(point_pattern, response)][:5]
        
        # Extract conclusion (last substantial paragraph)
        paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]
        conclusion = paragraphs[-1] if paragraphs else ""
        
        return LegalArgument(
            agent_name=self.name,
            argument_type=arg_type,
            main_argument=response,
            cited_statutes=cited_statutes,
            cited_precedents=cited_precedents,
            key_points=key_points if key_points else [response],
            conclusion=conclusion
        )


class DefenseAgent(BaseAgent):
    """
    Defense Agent - Argues against misappropriation, highlighting weaknesses in plaintiff's case.
    """
    
    def __init__(self,
                 name: str = "Defense",
                 strategy: str = "moderate",
                 **kwargs):
        """
        Initialize Defense Agent.
        
        Args:
            name: Agent name
            strategy: Legal strategy (aggressive, moderate, conservative)
        """
        self.strategy = strategy
        
        strategy_prompts = {
            "aggressive": """You are an aggressive defense attorney fighting trade secret claims.
            You challenge every piece of evidence vigorously, distinguish all precedents, and argue
            for complete dismissal. You emphasize lack of proof, procedural failures, and alternative explanations.""",
            
            "moderate": """You are a balanced defense attorney defending against trade secret claims.
            You reasonably challenge weak evidence, distinguish unfavorable precedents where appropriate,
            and seek fair outcomes. You focus on genuine weaknesses in the plaintiff's case.""",
            
            "conservative": """You are a measured defense attorney handling trade secret claims.
            You acknowledge strong evidence while highlighting gaps, seek to narrow claims rather than
            dismiss entirely, and propose reasonable settlements where appropriate."""
        }
        
        system_prompt = strategy_prompts.get(strategy, strategy_prompts["moderate"])
        system_prompt += """
        
        When making defense arguments:
        1. Challenge whether information qualifies as trade secrets
        2. Question if reasonable measures were taken to protect secrets
        3. Dispute misappropriation or improper acquisition
        4. Highlight missing elements of statutory requirements
        5. Cite precedents where similar claims failed
        6. Propose alternative explanations for defendant's actions
        
        Focus on: burden of proof failures, lack of evidence, distinguishable facts."""
        
        super().__init__(
            name=name,
            system_prompt=system_prompt,
            temperature=0.3,
            enable_tools=False,
            **kwargs
        )
    
    def make_opening_argument(self, evidence: CaseEvidence) -> LegalArgument:
        """Generate defense opening argument."""
        evidence_summary = self._prepare_defense_perspective(evidence)
        
        prompt = f"""Based on the following case, make a strong defense argument 
        against trade secret misappropriation claims:

        {evidence_summary}

        Generate your defense argument in the following JSON format:
        {{
            "main_argument": "Your primary defense argument (max 500 characters)",
            "key_points": ["defense point 1", "defense point 2", ...],
            "cited_statutes": ["DTSA § 1836 requirements not met", ...],
            "cited_precedents": ["Case1 v. Case2 (dismissal)", ...],
            "conclusion": "Your concluding defense statement (max 200 characters)"
        }}
        
        Requirements:
        1. Challenge the plaintiff's ability to prove all elements in main_argument
        2. Highlight weaknesses (no NDA, weak evidence, etc.) in key_points
        3. Cite precedents where similar claims failed in cited_precedents
        4. Question if information truly qualifies as trade secrets
        5. Provide alternative explanations in key_points
        
        Return only valid JSON, no additional text."""
        
        # Use generate_with_completion for automatic truncation handling
        response = self.generate_with_completion(prompt)
        return self._parse_json_argument(response, ArgumentType.OPENING)
    
    def make_rebuttal(self,
                     prosecutor_argument: LegalArgument,
                     evidence: CaseEvidence) -> LegalArgument:
        """Generate rebuttal to prosecutor's argument."""
        prompt = f"""The prosecution has argued:
        {prosecutor_argument.main_argument}

        They cited: {', '.join(prosecutor_argument.cited_statutes + prosecutor_argument.cited_precedents)}

        Provide a targeted rebuttal that:
        1. Challenges their interpretation of statutes
        2. Distinguishes their precedents
        3. Highlights what they haven't proven
        4. Reinforces reasonable doubt
        5. Emphasizes defense's strongest points

        Generate your rebuttal in the following JSON format:
        {{
            "main_argument": "Your primary defense rebuttal (max 500 characters)",
            "key_points": ["rebuttal point 1", "rebuttal point 2", ...],
            "cited_statutes": ["DTSA § 1836 elements not proven", ...],
            "cited_precedents": ["Distinguishable: Case1 v. Case2", ...],
            "conclusion": "Your concluding rebuttal (max 200 characters)"
        }}
        
        Keep the rebuttal focused and strategic.
        Return only valid JSON, no additional text."""
        
        # Use generate_with_completion for automatic truncation handling
        response = self.generate_with_completion(prompt)
        return self._parse_json_argument(response, ArgumentType.REBUTTAL)
    
    def _prepare_defense_perspective(self, evidence: CaseEvidence) -> str:
        """Prepare evidence summary from defense perspective."""
        summary = f"""
        CASE: {evidence.case_description}
        
        FAVORABLE DEFENSE FACTORS:
        - NDA Present: {evidence.has_nda} {'(No contractual obligation!)' if not evidence.has_nda else ''}
        - Evidence: {evidence.evidence_strength} {'(Insufficient for burden of proof)' if evidence.evidence_strength != 'strong' else ''}
        - Venue: {evidence.venue_bias} {'(Favorable to defense)' if 'defendant' in evidence.venue_bias else ''}
        
        PLAINTIFF MUST PROVE:
        1. Information qualifies as trade secret
        2. Reasonable measures taken to maintain secrecy
        3. Misappropriation occurred
        4. Damages resulted
        
        DEFENSIVE PRECEDENTS TO CONSIDER:
        """
        
        # Focus on precedents that might help defense
        for precedent in evidence.precedents:
            if 'dismiss' in precedent.holding.lower() or 'fail' in precedent.holding.lower():
                summary += f"\n- {precedent.case_name}: {precedent.holding}"
        
        if evidence.defendant_claims:
            summary += f"\n\nDEFENDANT'S POSITION:\n" + "\n".join(f"- {claim}" for claim in evidence.defendant_claims)
        
        if evidence.disputed_facts:
            summary += f"\n\nDISPUTED FACTS:\n" + "\n".join(f"- {fact}" for fact in evidence.disputed_facts)
        
        return summary
    
    def _parse_json_argument(self, response: str, arg_type: ArgumentType) -> LegalArgument:
        """Parse JSON AI response into structured argument using enhanced JSON repair."""
        # Use BaseAgent's repair_json method for robust parsing
        try:
            data = self.repair_json(response)
            
            return LegalArgument(
                agent_name=self.name,
                argument_type=arg_type,
                main_argument=data.get('main_argument', ''),
                cited_statutes=data.get('cited_statutes', []),
                cited_precedents=data.get('cited_precedents', []),
                key_points=data.get('key_points', [])[:5],  # Keep reasonable limit on key points
                conclusion=data.get('conclusion', '')
            )
            
        except Exception as e:
            # Fallback to basic parsing if JSON repair fails
            print(f"Warning: Failed to parse defense argument JSON even with repair: {e}")
            
            # Try to extract partial data
            partial_data = self.extract_partial_json(response)
            if partial_data:
                return LegalArgument(
                    agent_name=self.name,
                    argument_type=arg_type,
                    main_argument=partial_data.get('main_argument', response),
                    cited_statutes=partial_data.get('cited_statutes', []),
                    cited_precedents=partial_data.get('cited_precedents', []),
                    key_points=partial_data.get('key_points', [response])[:5],
                    conclusion=partial_data.get('conclusion', '')
                )
            
            # Last resort: use raw response
            return LegalArgument(
                agent_name=self.name,
                argument_type=arg_type,
                main_argument=response,
                cited_statutes=[],
                cited_precedents=[],
                key_points=[response],
                conclusion=""
            )
    
    def _parse_argument(self, response: str, arg_type: ArgumentType) -> LegalArgument:
        """Legacy regex-based parsing - deprecated, use _parse_json_argument instead."""
        statute_pattern = r'(?:DTSA|UTSA|USC|U\.S\.C\.|CFR)[^,;.]*'
        case_pattern = r'(?:[A-Z][a-z]+ v\. [A-Z][a-z]+)[^,;.]*'
        
        cited_statutes = list(set(re.findall(statute_pattern, response)))
        cited_precedents = list(set(re.findall(case_pattern, response)))
        
        point_pattern = r'(?:^|\n)(?:\d+\.|-|\*)\s*([^.\n]+\.)'
        key_points = [match.strip() for match in re.findall(point_pattern, response)][:5]
        
        paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]
        conclusion = paragraphs[-1] if paragraphs else ""
        
        return LegalArgument(
            agent_name=self.name,
            argument_type=arg_type,
            main_argument=response,
            cited_statutes=cited_statutes,
            cited_precedents=cited_precedents,
            key_points=key_points if key_points else [response],
            conclusion=conclusion
        )


class JudgeAgent(BaseAgent):
    """
    Judge Agent - Evaluates arguments from both sides and renders verdict.
    Uses relaxed safety settings to prevent filtering of legal discussions.
    """
    
    def __init__(self,
                 name: str = "Judge",
                 temperament: str = "balanced",
                 **kwargs):
        """
        Initialize Judge Agent.
        
        Args:
            name: Agent name
            temperament: Judicial temperament (strict, balanced, lenient)
        """
        self.temperament = temperament
        
        temperament_prompts = {
            "strict": """You are a strict federal judge who applies the law rigorously.
            You require strong evidence and clear statutory violations. You rarely show leniency
            and focus heavily on precedent and statutory text.""",
            
            "balanced": """You are a fair and balanced judge who weighs all arguments carefully.
            You consider both statutory requirements and equitable factors. You apply the law
            consistently while considering the specific circumstances of each case.""",
            
            "lenient": """You are a judge who considers broader equitable factors.
            While you apply the law, you also consider fairness, good faith efforts, and
            proportionality in your decisions. You may show flexibility in close cases."""
        }
        
        system_prompt = temperament_prompts.get(temperament, temperament_prompts["balanced"])
        system_prompt += """
        
        When evaluating cases:
        1. Consider burden of proof (preponderance of evidence for civil cases)
        2. Apply relevant statutory requirements systematically
        3. Weigh precedential value appropriately
        4. Evaluate credibility and strength of evidence
        5. Consider both legal and factual arguments
        6. Provide clear reasoning for decisions
        
        Your verdict must be based on law and evidence, not speculation."""
        
        super().__init__(
            name=name,
            system_prompt=system_prompt,
            temperature=0.2,  # Very low for consistent judicial reasoning
            enable_tools=False,
            **kwargs
        )
    
    def evaluate_case(self,
                     prosecutor_args: List[LegalArgument],
                     defense_args: List[LegalArgument],
                     evidence: CaseEvidence) -> Verdict:
        """
        Evaluate all arguments and render verdict.
        
        Args:
            prosecutor_args: All prosecutor arguments
            defense_args: All defense arguments
            evidence: Case evidence
            
        Returns:
            Verdict with reasoning
        """
        # Prepare comprehensive case summary
        case_summary = self._prepare_case_summary(prosecutor_args, defense_args, evidence)
        
        prompt = f"""As a federal judge, evaluate this trade secret misappropriation case:

        {case_summary}

        Consider:
        1. Has plaintiff proven all elements by preponderance of evidence?
        2. Are the trade secrets properly identified and protected?
        3. Did misappropriation occur as alleged?
        4. What precedents control this case?
        5. Are the defense arguments persuasive?

        Provide your verdict in the following JSON format:
        {{
            "winner": "plaintiff" or "defendant" or "settlement",
            "key_factors": ["factor1", "factor2", ...],
            "cited_authorities": ["DTSA § 1836", "Case1 v. Case2", ...],
            "confidence_score": 0.0 to 1.0,
            "rationale": "Your 2-3 paragraph reasoning for the decision"
        }}
        
        Be decisive but explain your reasoning clearly.
        Return only valid JSON, no additional text."""
        
        # Use generate_with_completion for automatic truncation handling
        response = self.generate_with_completion(prompt)
        
        # Parse verdict
        verdict = self._parse_verdict(response)
        return verdict
    
    def _prepare_case_summary(self,
                              prosecutor_args: List[LegalArgument],
                              defense_args: List[LegalArgument],
                              evidence: CaseEvidence) -> str:
        """Prepare comprehensive case summary for evaluation."""
        summary = f"""
        CASE: {evidence.case_description}
        JURISDICTION: {evidence.jurisdiction}
        
        CASE FACTORS:
        - NDA Present: {evidence.has_nda}
        - Evidence Strength: {evidence.evidence_strength}
        - Venue: {evidence.venue_bias}
        
        PROSECUTOR'S ARGUMENTS:
        """
        
        for arg in prosecutor_args:
            summary += f"\n\n{arg.argument_type.value.upper()}:"
            summary += f"\n{arg.main_argument}"
            if arg.cited_statutes:
                summary += f"\nStatutes cited: {', '.join(arg.cited_statutes[:3])}"
            if arg.cited_precedents:
                summary += f"\nPrecedents cited: {', '.join(arg.cited_precedents[:3])}"
        
        summary += "\n\nDEFENSE ARGUMENTS:"
        
        for arg in defense_args:
            summary += f"\n\n{arg.argument_type.value.upper()}:"
            summary += f"\n{arg.main_argument}"
            if arg.key_points:
                summary += f"\nKey points: {'; '.join(arg.key_points[:3])}"
        
        # Add key evidence
        if evidence.statutes:
            summary += "\n\nAPPLICABLE LAW:"
            for statute in evidence.statutes[:2]:
                summary += f"\n- {statute.citation}: {statute.key_provisions[0] if statute.key_provisions else statute.title}"
        
        if evidence.precedents:
            summary += "\n\nKEY PRECEDENTS:"
            for precedent in evidence.precedents[:2]:
                summary += f"\n- {precedent.case_name} ({precedent.year}): {precedent.holding}"
        
        return summary
    
    def _parse_verdict(self, response: str) -> Verdict:
        """Parse judge's JSON response into verdict."""
        import json
        
        try:
            # Clean response if needed (remove markdown code blocks)
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]
            
            data = json.loads(response.strip())
            
            # Map winner to outcome
            winner = data.get('winner', 'defendant').lower()
            if winner == 'plaintiff':
                outcome = VerdictOutcome.PLAINTIFF_WIN
            elif winner == 'settlement':
                outcome = VerdictOutcome.SETTLEMENT
            else:
                outcome = VerdictOutcome.DEFENSE_WIN
                winner = 'defendant'
            
            return Verdict(
                outcome=outcome,
                winner=winner,
                rationale=data.get('rationale', ''),
                key_factors=data.get('key_factors', [])[:5],
                cited_authorities=data.get('cited_authorities', [])[:5],
                confidence_score=min(1.0, max(0.0, float(data.get('confidence_score', 0.7))))
            )
            
        except (json.JSONDecodeError, Exception) as e:
            # Fallback to basic parsing if JSON fails
            print(f"Warning: Failed to parse verdict JSON: {e}")
            
            # Try basic text parsing as fallback
            response_lower = response.lower()
            
            if 'plaintiff' in response_lower and 'win' in response_lower:
                outcome = VerdictOutcome.PLAINTIFF_WIN
                winner = "plaintiff"
            elif 'settlement' in response_lower:
                outcome = VerdictOutcome.SETTLEMENT
                winner = "settlement"
            else:
                outcome = VerdictOutcome.DEFENSE_WIN
                winner = "defendant"
            
            return Verdict(
                outcome=outcome,
                winner=winner,
                rationale=response,
                key_factors=["Evidence evaluation", "Legal analysis"],
                cited_authorities=[],
                confidence_score=0.5
            )


class ResearchAgent(BaseAgent):
    """
    Research Agent - Coordinates with PrecedentAgent and StatuteAgent to gather evidence.
    """
    
    def __init__(self,
                 name: str = "ResearchCoordinator",
                 **kwargs):
        """Initialize Research Agent."""
        system_prompt = """You are a legal research coordinator preparing comprehensive case evidence.
        Your role is to:
        1. Analyze case descriptions to identify key legal issues
        2. Determine relevant statutes and areas of law
        3. Identify important precedents to research
        4. Extract key facts and claims
        5. Prepare structured evidence packets
        
        Focus on trade secret law, particularly DTSA and UTSA provisions."""
        
        super().__init__(
            name=name,
            system_prompt=system_prompt,
            temperature=0.3,
            enable_tools=False,
            response_format='json',  # Enable JSON output for case analysis
            **kwargs
        )
        
        # Initialize specialized agents
        self.precedent_agent = PrecedentAgent(use_browser=False)  # Faster without browser
        self.statute_agent = StatuteAgent()
    
    def gather_evidence(self, 
                       case_description: str,
                       jurisdiction: str = "Federal") -> CaseEvidence:
        """
        Gather comprehensive evidence for a case.
        
        Args:
            case_description: Natural language description of the case
            jurisdiction: Legal jurisdiction
            
        Returns:
            Complete evidence packet
        """
        print(f"\n[Research Agent] Analyzing case...")
        
        # Extract key information from case description
        case_analysis = self._analyze_case(case_description)
        
        # Search for relevant statutes
        print(f"[Research Agent] Searching for relevant statutes...")
        statutes = self._search_statutes(case_analysis['legal_issues'])
        
        # Search for relevant precedents
        print(f"[Research Agent] Searching for relevant precedents...")
        precedents = self._search_precedents(case_analysis['legal_issues'], jurisdiction)
        
        # Create evidence packet
        evidence = CaseEvidence(
            case_description=case_description,
            jurisdiction=jurisdiction,
            has_nda=case_analysis.get('has_nda', False),
            evidence_strength=case_analysis.get('evidence_strength', 'moderate'),
            venue_bias=case_analysis.get('venue_bias', 'neutral'),
            statutes=statutes[:5],  # Top 5 statutes
            precedents=precedents[:5],  # Top 5 precedents
            facts=case_analysis.get('key_facts', []),
            plaintiff_claims=case_analysis.get('plaintiff_claims', []),
            defendant_claims=case_analysis.get('defendant_claims', []),
            disputed_facts=case_analysis.get('disputed_facts', [])
        )
        
        print(f"[Research Agent] Evidence gathering complete.")
        return evidence
    
    def _analyze_case(self, case_description: str) -> Dict[str, Any]:
        """Analyze case to extract key information."""
        import json
        
        prompt = f"""Analyze this legal case and extract key information:

        {case_description}

        Return your analysis in the following JSON format:
        {{
            "legal_issues": ["issue1", "issue2", ...],
            "key_facts": ["fact1", "fact2", ...],
            "has_nda": true/false,
            "evidence_strength": "weak" or "moderate" or "strong",
            "venue_bias": "plaintiff-friendly" or "defendant-friendly" or "neutral",
            "plaintiff_claims": ["claim1", "claim2", ...],
            "defendant_defenses": ["defense1", "defense2", ...],
            "disputed_facts": ["fact1", "fact2", ...]
        }}

"""
        
        # Use generate_with_completion for automatic truncation handling
        response = self.generate_with_completion(prompt)
        
        # Parse JSON response
        try:
            # When response_format='json', Gemini returns raw JSON
            if isinstance(response, str):
                # Try to parse as-is first
                try:
                    analysis = json.loads(response.strip())
                except json.JSONDecodeError:
                    # Fallback: clean markdown if present
                    if '```json' in response:
                        response = response.split('```json')[1].split('```')[0]
                    elif '```' in response:
                        response = response.split('```')[1].split('```')[0]
                    analysis = json.loads(response.strip())
            else:
                analysis = response  # Already parsed
            
            # Ensure all required fields exist with defaults
            defaults = {
                'legal_issues': [],
                'key_facts': [],
                'has_nda': False,
                'evidence_strength': 'moderate',
                'venue_bias': 'neutral',
                'plaintiff_claims': [],
                'defendant_defenses': [],
                'disputed_facts': []
            }
            
            # Merge with defaults to handle missing fields
            for key, default_value in defaults.items():
                if key not in analysis:
                    analysis[key] = default_value
                    
            # Handle legacy field name
            if 'defendant_defenses' in analysis:
                analysis['defendant_claims'] = analysis.get('defendant_defenses', [])
                    
        except (json.JSONDecodeError, Exception) as e:
            # Fallback to defaults if parsing fails
            print(f"Warning: Failed to parse case analysis JSON: {e}")
            analysis = {
                'legal_issues': [],
                'key_facts': [],
                'has_nda': False,
                'evidence_strength': 'moderate',
                'venue_bias': 'neutral',
                'plaintiff_claims': [],
                'defendant_claims': [],
                'disputed_facts': []
            }
        
        return analysis
    
    def _search_statutes(self, legal_issues: List[str]) -> List[StatuteInfo]:
        """Search for relevant statutes."""
        # Focus on trade secret statutes
        queries = [
            "DTSA Defend Trade Secrets Act requirements elements",
            "UTSA Uniform Trade Secrets Act provisions"
        ]
        
        # Add issue-specific queries
        for issue in legal_issues[:2]:
            queries.append(f"trade secret law {issue}")
        
        all_statutes = []
        for query in queries:
            try:
                # Use comprehensive_research method which returns structured data
                result = self.statute_agent.comprehensive_research(query, include_case_law=False)
                if result and 'statute' in result:
                    statute_info = StatuteInfo(
                        title=result['statute'].get('title', 'Unknown'),
                        citation=result['statute'].get('citation', ''),
                        definitions=result['statute'].get('definitions', {}),
                        key_provisions=result['statute'].get('key_provisions', []),
                        remedies=result['statute'].get('remedies', []),
                        snippet=result['statute'].get('snippet', '')
                    )
                    all_statutes.append(statute_info)
            except Exception as e:
                print(f"  Error searching statutes: {e}")
        
        return all_statutes
    
    def _search_precedents(self, legal_issues: List[str], jurisdiction: str) -> List[CasePrecedent]:
        """Search for relevant precedents."""
        queries = [
            f"trade secret misappropriation cases {jurisdiction}",
            "landmark trade secret cases federal circuit"
        ]
        
        for issue in legal_issues[:2]:
            queries.append(f"trade secret precedent {issue}")
        
        all_precedents = []
        for query in queries:
            try:
                # Use quick_search method as it's simpler and faster
                result_str = self.precedent_agent.quick_search(query, use_browser=False)
                
                # Create a basic precedent from the result
                if result_str:
                    # Parse the result to extract basic info
                    from agents.precedentAgent import CourtLevel
                    precedent = CasePrecedent(
                        case_name=f"Case re: {query[:30]}",
                        year="2023",
                        citation="[Citation pending]",
                        court=jurisdiction,
                        court_level=CourtLevel.FEDERAL_DISTRICT,
                        holding=result_str[:300] if len(result_str) > 300 else result_str,
                        rule="[Rule to be extracted]",
                        confidence_score=0.7
                    )
                    all_precedents.append(precedent)
            except Exception as e:
                print(f"  Error searching precedents: {e}")
        
        return all_precedents


class LegalSimulation:
    """
    Main simulation orchestrator for legal proceedings.
    """
    
    def __init__(self,
                 prosecutor_strategy: str = "moderate",
                 defense_strategy: str = "moderate",
                 judge_temperament: str = "balanced"):
        """
        Initialize simulation with agent configurations.
        
        Args:
            prosecutor_strategy: Strategy for prosecutor agent
            defense_strategy: Strategy for defense agent
            judge_temperament: Temperament for judge agent
        """
        self.prosecutor = ProsecutorAgent(strategy=prosecutor_strategy)
        self.defense = DefenseAgent(strategy=defense_strategy)
        self.judge = JudgeAgent(temperament=judge_temperament)
        self.research = ResearchAgent()
        
        self.case_evidence = None
        self.arguments = {
            'prosecutor': [],
            'defense': []
        }
        self.verdict = None
    
    def prepare_case(self, case_description: str, jurisdiction: str = "Federal") -> CaseEvidence:
        """
        Prepare case by gathering evidence.
        
        Args:
            case_description: Natural language case description
            jurisdiction: Legal jurisdiction
            
        Returns:
            Evidence packet
        """
        print(f"\n{'='*60}")
        print("CASE PREPARATION")
        print(f"{'='*60}")
        
        self.case_evidence = self.research.gather_evidence(case_description, jurisdiction)
        
        print(f"\nEvidence Summary:")
        print(f"  - Statutes found: {len(self.case_evidence.statutes)}")
        print(f"  - Precedents found: {len(self.case_evidence.precedents)}")
        print(f"  - Key facts: {len(self.case_evidence.facts)}")
        print(f"  - NDA present: {self.case_evidence.has_nda}")
        print(f"  - Evidence strength: {self.case_evidence.evidence_strength}")
        
        return self.case_evidence
    
    def run_trial(self, include_rebuttals: bool = True) -> Verdict:
        """
        Run the complete trial simulation.
        
        Args:
            include_rebuttals: Whether to include rebuttal phase
            
        Returns:
            Judge's verdict
        """
        if not self.case_evidence:
            raise ValueError("Must prepare case first with prepare_case()")
        
        print(f"\n{'='*60}")
        print("TRIAL PROCEEDINGS")
        print(f"{'='*60}")
        
        # Phase 1: Opening Arguments
        print(f"\n--- OPENING ARGUMENTS ---")
        print(f"\n[Prosecutor's Opening]")
        prosecutor_opening = self.prosecutor.make_opening_argument(self.case_evidence)
        self.arguments['prosecutor'].append(prosecutor_opening)
        print(f"Main argument: {prosecutor_opening.main_argument}...")
        print(f"Cited: {len(prosecutor_opening.cited_statutes)} statutes, {len(prosecutor_opening.cited_precedents)} cases")
        
        print(f"\n[Defense Opening]")
        defense_opening = self.defense.make_opening_argument(self.case_evidence)
        self.arguments['defense'].append(defense_opening)
        print(f"Main argument: {defense_opening.main_argument}...")
        print(f"Key points: {len(defense_opening.key_points)}")
        
        # Phase 2: Rebuttals (optional)
        if include_rebuttals:
            print(f"\n--- REBUTTALS ---")
            print(f"\n[Prosecutor's Rebuttal]")
            prosecutor_rebuttal = self.prosecutor.make_rebuttal(defense_opening, self.case_evidence)
            self.arguments['prosecutor'].append(prosecutor_rebuttal)
            print(f"Rebuttal: {prosecutor_rebuttal.main_argument}...")
            
            print(f"\n[Defense Rebuttal]")
            defense_rebuttal = self.defense.make_rebuttal(prosecutor_opening, self.case_evidence)
            self.arguments['defense'].append(defense_rebuttal)
            print(f"Rebuttal: {defense_rebuttal.main_argument}...")
        
        # Phase 3: Judge's Verdict
        print(f"\n--- JUDGE'S VERDICT ---")
        self.verdict = self.judge.evaluate_case(
            self.arguments['prosecutor'],
            self.arguments['defense'],
            self.case_evidence
        )
        
        print(f"\n🔨 VERDICT: {self.verdict.winner.upper()} WINS")
        print(f"Confidence: {self.verdict.confidence_score:.2%}")
        print(f"\nRationale: {self.verdict.rationale[:300]}...")
        print(f"\nKey Factors:")
        for factor in self.verdict.key_factors[:3]:
            print(f"  - {factor}")
        
        return self.verdict
    
    def get_trial_summary(self) -> Dict[str, Any]:
        """Get comprehensive trial summary."""
        if not self.verdict:
            return {"status": "Trial not completed"}
        
        return {
            "case": self.case_evidence.case_description,
            "strategies": {
                "prosecutor": self.prosecutor.strategy,
                "defense": self.defense.strategy,
                "judge": self.judge.temperament
            },
            "arguments_made": {
                "prosecutor": len(self.arguments['prosecutor']),
                "defense": len(self.arguments['defense'])
            },
            "verdict": {
                "winner": self.verdict.winner,
                "outcome": self.verdict.outcome.value,
                "confidence": self.verdict.confidence_score,
                "key_factors": self.verdict.key_factors
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def save_results(self, filepath: str):
        """Save trial results to file."""
        summary = self.get_trial_summary()
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"\nResults saved to {filepath}")


class MonteCarloSimulation:
    """
    Monte Carlo simulation for exploring different strategy combinations.
    """
    
    STRATEGIES = ["aggressive", "moderate", "conservative"]
    TEMPERAMENTS = ["strict", "balanced", "lenient"]
    
    def __init__(self):
        """Initialize Monte Carlo simulator."""
        self.results = []
    
    def run_simulations(self,
                       case_description: str,
                       num_simulations: int = 10,
                       vary_strategies: bool = True,
                       fixed_judge: Optional[str] = None) -> Dict[str, Any]:
        """
        Run multiple simulations with varying strategies.
        
        Args:
            case_description: Case to simulate
            num_simulations: Number of simulations to run
            vary_strategies: Whether to vary agent strategies
            fixed_judge: Fix judge temperament (None to vary)
            
        Returns:
            Simulation results and statistics
        """
        print(f"\n{'='*60}")
        print(f"MONTE CARLO SIMULATION - {num_simulations} trials")
        print(f"{'='*60}")
        
        results = []
        
        for i in range(num_simulations):
            print(f"\n--- Simulation {i+1}/{num_simulations} ---")
            
            # Select strategies
            if vary_strategies:
                prosecutor_strategy = random.choice(self.STRATEGIES)
                defense_strategy = random.choice(self.STRATEGIES)
            else:
                prosecutor_strategy = "moderate"
                defense_strategy = "moderate"
            
            judge_temperament = fixed_judge if fixed_judge else random.choice(self.TEMPERAMENTS)
            
            print(f"Configuration: P={prosecutor_strategy}, D={defense_strategy}, J={judge_temperament}")
            
            # Run simulation
            try:
                sim = LegalSimulation(
                    prosecutor_strategy=prosecutor_strategy,
                    defense_strategy=defense_strategy,
                    judge_temperament=judge_temperament
                )
                
                # Prepare case (reuse evidence for consistency)
                if i == 0:
                    base_evidence = sim.prepare_case(case_description)
                else:
                    sim.case_evidence = base_evidence
                
                # Run trial
                verdict = sim.run_trial(include_rebuttals=True)
                
                # Store result
                result = {
                    'simulation_id': i + 1,
                    'prosecutor_strategy': prosecutor_strategy,
                    'defense_strategy': defense_strategy,
                    'judge_temperament': judge_temperament,
                    'winner': verdict.winner,
                    'outcome_value': verdict.outcome.value,
                    'confidence': verdict.confidence_score
                }
                results.append(result)
                
            except Exception as e:
                print(f"  Simulation failed: {e}")
                continue
        
        # Analyze results
        analysis = self._analyze_results(results)
        
        print(f"\n{'='*60}")
        print("SIMULATION RESULTS")
        print(f"{'='*60}")
        print(f"\nTotal simulations: {len(results)}")
        print(f"Plaintiff wins: {analysis['plaintiff_wins']} ({analysis['plaintiff_win_rate']:.1%})")
        print(f"Defense wins: {analysis['defense_wins']} ({analysis['defense_win_rate']:.1%})")
        print(f"Average confidence: {analysis['avg_confidence']:.2%}")
        
        print(f"\nBest strategies:")
        print(f"  For Plaintiff: {analysis['best_prosecutor_strategy']}")
        print(f"  For Defense: {analysis['best_defense_strategy']}")
        
        return {
            'results': results,
            'analysis': analysis,
            'case': case_description
        }
    
    def _analyze_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze simulation results."""
        if not results:
            return {}
        
        # Basic statistics
        plaintiff_wins = sum(1 for r in results if r['winner'] == 'plaintiff')
        defense_wins = sum(1 for r in results if r['winner'] == 'defendant')
        total = len(results)
        
        # Strategy effectiveness
        prosecutor_strategies = {}
        defense_strategies = {}
        
        for result in results:
            p_strat = result['prosecutor_strategy']
            d_strat = result['defense_strategy']
            
            if p_strat not in prosecutor_strategies:
                prosecutor_strategies[p_strat] = {'wins': 0, 'total': 0}
            if d_strat not in defense_strategies:
                defense_strategies[d_strat] = {'wins': 0, 'total': 0}
            
            prosecutor_strategies[p_strat]['total'] += 1
            defense_strategies[d_strat]['total'] += 1
            
            if result['winner'] == 'plaintiff':
                prosecutor_strategies[p_strat]['wins'] += 1
            else:
                defense_strategies[d_strat]['wins'] += 1
        
        # Find best strategies
        best_prosecutor = max(prosecutor_strategies.items(),
                            key=lambda x: x[1]['wins'] / x[1]['total'] if x[1]['total'] > 0 else 0)
        best_defense = max(defense_strategies.items(),
                         key=lambda x: x[1]['wins'] / x[1]['total'] if x[1]['total'] > 0 else 0)
        
        return {
            'plaintiff_wins': plaintiff_wins,
            'defense_wins': defense_wins,
            'plaintiff_win_rate': plaintiff_wins / total if total > 0 else 0,
            'defense_win_rate': defense_wins / total if total > 0 else 0,
            'avg_confidence': sum(r['confidence'] for r in results) / total if total > 0 else 0,
            'best_prosecutor_strategy': best_prosecutor[0],
            'best_defense_strategy': best_defense[0],
            'strategy_stats': {
                'prosecutor': prosecutor_strategies,
                'defense': defense_strategies
            }
        }


# Example usage functions
def run_single_trial_example():
    """Run a single trial simulation example."""
    case_description = """
    TechCorp, a leading software company, alleges that former employee John Doe 
    misappropriated trade secrets when he joined competitor InnovateTech. 
    John had signed an NDA and had access to proprietary algorithms for machine learning
    optimization. TechCorp discovered that InnovateTech released a suspiciously similar 
    product just 3 months after John joined them. Evidence includes access logs showing 
    John downloaded key repositories days before leaving, and code similarities between 
    the products. The case is in the Northern District of California.
    """
    
    # Create simulation with specific strategies
    sim = LegalSimulation(
        prosecutor_strategy="aggressive",
        defense_strategy="moderate",
        judge_temperament="balanced"
    )
    
    # Prepare case
    evidence = sim.prepare_case(case_description, jurisdiction="Federal")
    
    # Run trial
    verdict = sim.run_trial(include_rebuttals=True)
    
    # Save results
    sim.save_results("trial_results.json")
    
    return verdict


def run_monte_carlo_example():
    """Run Monte Carlo simulation example."""
    case_description = """
    BioPharm Inc claims that former research scientist Dr. Smith took confidential 
    drug formulation data to competitor MedTech. No formal NDA exists, but company 
    policies prohibit sharing confidential information. Evidence is mixed - some emails 
    suggest knowledge transfer, but no direct proof of document theft. The case is in 
    Delaware federal court, known for being business-friendly.
    """
    
    # Create Monte Carlo simulator
    mc_sim = MonteCarloSimulation()
    
    # Run simulations
    results = mc_sim.run_simulations(
        case_description=case_description,
        num_simulations=5,  # Small number for example
        vary_strategies=True,
        fixed_judge=None  # Vary judge temperament too
    )
    
    # Save comprehensive results
    with open("monte_carlo_results.json", 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    return results


if __name__ == "__main__":
    print("Legal Case Simulation System")
    print("============================\n")
    
    # Run single trial example
    print("1. Running Single Trial Example...")
    verdict = run_single_trial_example()
    
    # Run Monte Carlo example
    print("\n2. Running Monte Carlo Example...")
    mc_results = run_monte_carlo_example()
    
    print("\nSimulation complete! Check trial_results.json and monte_carlo_results.json for details.")
