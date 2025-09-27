"""
Enhanced Trial Simulation with Proper Timestamps and Extended Dialogue
======================================================================
This module provides an enhanced trial simulation with:
- Proper sequential timestamps
- Extended back-and-forth dialogue
- Full message content without truncation
"""

import os
import sys
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.simulation import (
    LegalSimulation,
    CaseEvidence,
    LegalArgument,
    ArgumentType,
    Verdict
)
from database.mongodb_manager import AgentMessage, CaseSimulation, SimulationStatus


class EnhancedLegalSimulation(LegalSimulation):
    """
    Enhanced legal simulation with proper timestamps and extended dialogue.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = None
        self.message_delay = 2  # seconds between messages for realistic timestamps
        
    def run_extended_trial(self, 
                          num_exchanges: int = 3,
                          include_procedural: bool = True) -> Tuple[List[AgentMessage], Verdict]:
        """
        Run an extended trial with multiple exchanges and proper timestamps.
        
        Args:
            num_exchanges: Number of argument-rebuttal exchanges
            include_procedural: Include procedural messages (judge instructions, etc.)
            
        Returns:
            Tuple of (messages list, verdict)
        """
        if not self.case_evidence:
            raise ValueError("Must prepare case first with prepare_case()")
        
        messages = []
        self.start_time = datetime.now()
        current_time = self.start_time
        
        print(f"\n{'='*60}")
        print("EXTENDED TRIAL PROCEEDINGS")
        print(f"{'='*60}")
        
        # Opening: Judge's Introduction
        if include_procedural:
            judge_intro = f"""This court is now in session. We are here today to hear the case of {self.case_evidence.case_description[:100]}...
            
The plaintiff must prove by a preponderance of evidence that trade secret misappropriation occurred under the Defend Trade Secrets Act. 
The defense may present arguments and evidence to refute these claims.

Counsel, please present your opening statements."""
            
            messages.append(AgentMessage(
                agent_name="Judge",
                role="assistant",
                content=judge_intro,
                timestamp=current_time,
                metadata={"phase": "introduction", "type": "procedural"}
            ))
            current_time = self._advance_time(current_time, 5)
        
        # Phase 1: Opening Statements
        print(f"\n--- OPENING STATEMENTS ---")
        
        # Prosecutor's Opening
        print(f"\n[Prosecutor's Opening Statement]")
        prosecutor_opening = self.prosecutor.make_opening_argument(self.case_evidence)
        self.arguments['prosecutor'].append(prosecutor_opening)
        
        # Get FULL content, not truncated
        full_prosecutor_opening = self._get_full_argument_content(prosecutor_opening)
        
        messages.append(AgentMessage(
            agent_name="Prosecutor",
            role="assistant",
            content=full_prosecutor_opening,
            timestamp=current_time,
            metadata={
                "phase": "opening_statement",
                "type": "argument",
                "cited_statutes": prosecutor_opening.cited_statutes,
                "cited_precedents": prosecutor_opening.cited_precedents,
                "key_points": prosecutor_opening.key_points
            }
        ))
        current_time = self._advance_time(current_time, 8)
        
        # Defense's Opening
        print(f"\n[Defense Opening Statement]")
        defense_opening = self.defense.make_opening_argument(self.case_evidence)
        self.arguments['defense'].append(defense_opening)
        
        full_defense_opening = self._get_full_argument_content(defense_opening)
        
        messages.append(AgentMessage(
            agent_name="Defense",
            role="assistant",
            content=full_defense_opening,
            timestamp=current_time,
            metadata={
                "phase": "opening_statement",
                "type": "argument",
                "key_points": defense_opening.key_points
            }
        ))
        current_time = self._advance_time(current_time, 8)
        
        # Phase 2: Multiple Rounds of Arguments and Rebuttals
        for exchange_num in range(num_exchanges):
            print(f"\n--- EXCHANGE {exchange_num + 1} ---")
            
            # Judge prompts for rebuttals if needed
            if include_procedural and exchange_num == 0:
                judge_prompt = "Counsel may now present rebuttals to the opening statements."
                messages.append(AgentMessage(
                    agent_name="Judge",
                    role="assistant",
                    content=judge_prompt,
                    timestamp=current_time,
                    metadata={"phase": f"exchange_{exchange_num + 1}", "type": "procedural"}
                ))
                current_time = self._advance_time(current_time, 2)
            
            # Prosecutor's Rebuttal/Argument
            print(f"\n[Prosecutor's Rebuttal {exchange_num + 1}]")
            prosecutor_rebuttal = self.prosecutor.make_rebuttal(
                self.arguments['defense'][-1], 
                self.case_evidence
            )
            self.arguments['prosecutor'].append(prosecutor_rebuttal)
            
            full_prosecutor_rebuttal = self._get_full_rebuttal_content(
                prosecutor_rebuttal, 
                exchange_num + 1
            )
            
            messages.append(AgentMessage(
                agent_name="Prosecutor",
                role="assistant",
                content=full_prosecutor_rebuttal,
                timestamp=current_time,
                metadata={
                    "phase": f"exchange_{exchange_num + 1}",
                    "type": "rebuttal",
                    "round": exchange_num + 1,
                    "cited_statutes": prosecutor_rebuttal.cited_statutes,
                    "cited_precedents": prosecutor_rebuttal.cited_precedents
                }
            ))
            current_time = self._advance_time(current_time, 6)
            
            # Defense's Counter-Rebuttal
            print(f"\n[Defense Counter-Rebuttal {exchange_num + 1}]")
            defense_rebuttal = self.defense.make_rebuttal(
                self.arguments['prosecutor'][-2],  # Respond to prosecutor's previous argument
                self.case_evidence
            )
            self.arguments['defense'].append(defense_rebuttal)
            
            full_defense_rebuttal = self._get_full_rebuttal_content(
                defense_rebuttal,
                exchange_num + 1
            )
            
            messages.append(AgentMessage(
                agent_name="Defense",
                role="assistant",
                content=full_defense_rebuttal,
                timestamp=current_time,
                metadata={
                    "phase": f"exchange_{exchange_num + 1}",
                    "type": "counter_rebuttal",
                    "round": exchange_num + 1,
                    "key_points": defense_rebuttal.key_points
                }
            ))
            current_time = self._advance_time(current_time, 6)
            
            # Additional back-and-forth within each exchange
            if exchange_num < num_exchanges - 1:  # Not the last exchange
                # Quick prosecutor response
                quick_response = self._generate_quick_response(
                    "prosecutor",
                    defense_rebuttal.main_argument
                )
                messages.append(AgentMessage(
                    agent_name="Prosecutor",
                    role="assistant",
                    content=quick_response,
                    timestamp=current_time,
                    metadata={
                        "phase": f"exchange_{exchange_num + 1}",
                        "type": "quick_response"
                    }
                ))
                current_time = self._advance_time(current_time, 3)
                
                # Quick defense counter
                quick_counter = self._generate_quick_response(
                    "defense",
                    quick_response
                )
                messages.append(AgentMessage(
                    agent_name="Defense",
                    role="assistant",
                    content=quick_counter,
                    timestamp=current_time,
                    metadata={
                        "phase": f"exchange_{exchange_num + 1}",
                        "type": "quick_counter"
                    }
                ))
                current_time = self._advance_time(current_time, 3)
        
        # Phase 3: Closing Arguments
        print(f"\n--- CLOSING ARGUMENTS ---")
        
        if include_procedural:
            judge_closing_prompt = "Counsel, please present your closing arguments."
            messages.append(AgentMessage(
                agent_name="Judge",
                role="assistant",
                content=judge_closing_prompt,
                timestamp=current_time,
                metadata={"phase": "closing", "type": "procedural"}
            ))
            current_time = self._advance_time(current_time, 2)
        
        # Prosecutor's Closing
        prosecutor_closing = self._generate_closing_argument("prosecutor")
        messages.append(AgentMessage(
            agent_name="Prosecutor",
            role="assistant",
            content=prosecutor_closing,
            timestamp=current_time,
            metadata={"phase": "closing", "type": "closing_argument"}
        ))
        current_time = self._advance_time(current_time, 5)
        
        # Defense's Closing
        defense_closing = self._generate_closing_argument("defense")
        messages.append(AgentMessage(
            agent_name="Defense",
            role="assistant",
            content=defense_closing,
            timestamp=current_time,
            metadata={"phase": "closing", "type": "closing_argument"}
        ))
        current_time = self._advance_time(current_time, 5)
        
        # Phase 4: Judge's Verdict
        print(f"\n--- JUDGE'S VERDICT ---")
        
        if include_procedural:
            judge_deliberation = "The court will now consider all arguments and evidence presented."
            messages.append(AgentMessage(
                agent_name="Judge",
                role="assistant",
                content=judge_deliberation,
                timestamp=current_time,
                metadata={"phase": "verdict", "type": "procedural"}
            ))
            current_time = self._advance_time(current_time, 3)
        
        # Get verdict
        self.verdict = self.judge.evaluate_case(
            self.arguments['prosecutor'],
            self.arguments['defense'],
            self.case_evidence
        )
        
        # Full verdict message
        full_verdict = self._format_full_verdict(self.verdict)
        
        messages.append(AgentMessage(
            agent_name="Judge",
            role="assistant",
            content=full_verdict,
            timestamp=current_time,
            metadata={
                "phase": "verdict",
                "type": "final_verdict",
                "winner": self.verdict.winner,
                "confidence": self.verdict.confidence_score,
                "key_factors": self.verdict.key_factors,
                "cited_authorities": self.verdict.cited_authorities
            }
        ))
        
        print(f"\n🔨 VERDICT: {self.verdict.winner.upper()} WINS")
        print(f"Confidence: {self.verdict.confidence_score:.2%}")
        print(f"Total messages: {len(messages)}")
        
        return messages, self.verdict
    
    def _advance_time(self, current_time: datetime, seconds: int) -> datetime:
        """Advance timestamp by specified seconds."""
        return current_time + timedelta(seconds=seconds)
    
    def _get_full_argument_content(self, argument: LegalArgument) -> str:
        """Get full argument content without truncation."""
        content = f"""**{argument.argument_type.value.upper()} ARGUMENT**

{argument.main_argument}

**Key Legal Points:**
{chr(10).join(f"• {point}" for point in argument.key_points)}

**Cited Statutes:**
{', '.join(argument.cited_statutes) if argument.cited_statutes else "None cited"}

**Cited Precedents:**
{', '.join(argument.cited_precedents) if argument.cited_precedents else "None cited"}

**Conclusion:**
{argument.conclusion}"""
        return content
    
    def _get_full_rebuttal_content(self, argument: LegalArgument, round_num: int) -> str:
        """Get full rebuttal content with round information."""
        content = f"""**REBUTTAL - Round {round_num}**

{argument.main_argument}

**Direct Responses to Opposing Arguments:**
{chr(10).join(f"• {point}" for point in argument.key_points[:3])}

**Legal Authority Supporting Our Position:**
- Statutes: {', '.join(argument.cited_statutes[:2]) if argument.cited_statutes else "See opening statement"}
- Precedents: {', '.join(argument.cited_precedents[:2]) if argument.cited_precedents else "As previously cited"}

**Summary:**
{argument.conclusion}"""
        return content
    
    def _generate_quick_response(self, side: str, previous_argument: str) -> str:
        """Generate a quick response to the previous argument."""
        if side == "prosecutor":
            agent = self.prosecutor
            perspective = "The prosecution maintains that"
        else:
            agent = self.defense
            perspective = "The defense asserts that"
        
        prompt = f"""Provide a brief (2-3 sentence) response to: {previous_argument[:200]}
        Keep it focused and direct. Start with '{perspective}'"""
        
        response = agent.chat(prompt)
        # Ensure response isn't too long
        if len(response) > 500:
            response = response[:497] + "..."
        
        return response
    
    def _generate_closing_argument(self, side: str) -> str:
        """Generate a comprehensive closing argument."""
        if side == "prosecutor":
            agent = self.prosecutor
            args = self.arguments['prosecutor']
            position = "prosecution"
        else:
            agent = self.defense
            args = self.arguments['defense']
            position = "defense"
        
        # Summarize key points from all arguments
        key_points_summary = "\n".join([
            f"- {arg.key_points[0]}" 
            for arg in args[-3:] if arg.key_points
        ])
        
        prompt = f"""Based on all arguments presented, provide a strong closing statement for the {position}.
        
        Summarize:
        1. Why your client should prevail
        2. The strongest evidence/arguments in your favor
        3. Why the opposing arguments fail
        4. The remedy or outcome sought
        
        Key points from trial:
        {key_points_summary}
        
        Keep it persuasive but professional. Maximum 3 paragraphs."""
        
        response = agent.chat(prompt)
        return response
    
    def _format_full_verdict(self, verdict: Verdict) -> str:
        """Format the complete verdict with all details."""
        content = f"""**FINAL VERDICT**

This Court, having carefully considered all arguments, evidence, and applicable law, hereby renders the following verdict:

**DECISION:** The Court finds in favor of the **{verdict.winner.upper()}**.

**RATIONALE:**
{verdict.rationale}

**KEY FACTORS IN THIS DECISION:**
{chr(10).join(f"{i+1}. {factor}" for i, factor in enumerate(verdict.key_factors))}

**LEGAL AUTHORITIES RELIED UPON:**
{', '.join(verdict.cited_authorities) if verdict.cited_authorities else "DTSA, UTSA, and cited precedents"}

**CONFIDENCE IN VERDICT:** {verdict.confidence_score:.1%}

**CONCLUSION:**
Based on the preponderance of evidence standard and the arguments presented, this Court's decision is final. 
{f"The plaintiff is entitled to appropriate remedies under the DTSA." if verdict.winner == "plaintiff" else "The defendant is cleared of all claims of trade secret misappropriation."}

So ordered.

*Gavel strikes*"""
        return content
    
    def convert_to_case_simulation(self, 
                                  messages: List[AgentMessage],
                                  case_id: str,
                                  simulation_id: Optional[int] = None) -> CaseSimulation:
        """
        Convert trial messages to a CaseSimulation for MongoDB storage.
        
        Args:
            messages: List of trial messages
            case_id: Case identifier
            simulation_id: Optional simulation number
            
        Returns:
            CaseSimulation object ready for MongoDB
        """
        return CaseSimulation(
            case_id=case_id,
            case_name=f"Trial Simulation - {self.case_evidence.case_description[:50]}...",
            simulation_type="extended_trial",
            agents_involved=["Prosecutor", "Defense", "Judge"],
            chat_history=messages,
            status=SimulationStatus.COMPLETED,
            created_at=self.start_time or datetime.now(),
            updated_at=datetime.now(),
            completed_at=datetime.now(),
            metadata={
                "prosecutor_strategy": self.prosecutor.strategy,
                "defense_strategy": self.defense.strategy,
                "judge_temperament": self.judge.temperament,
                "num_exchanges": len([m for m in messages if "exchange" in str(m.metadata)]) // 2,
                "total_messages": len(messages),
                "simulation_id": simulation_id
            },
            outcome=self.verdict.winner if self.verdict else None,
            summary=f"Extended trial with verdict: {self.verdict.winner} wins ({self.verdict.confidence_score:.1%} confidence)" if self.verdict else "Trial incomplete"
        )


# Example usage
if __name__ == "__main__":
    case_description = """
    SolarTech Industries alleges that Dr. Sarah Chen, their former Chief Technology Officer,
    misappropriated proprietary solar panel efficiency algorithms when she founded her
    competing company, BrightEnergy Solutions. Dr. Chen had signed a comprehensive NDA
    and non-compete agreement. Evidence includes downloaded source code repositories,
    suspicious email communications with investors before resignation, and BrightEnergy's
    remarkably similar product launched just 3 months after Dr. Chen's departure.
    The case is filed in the Northern District of California.
    """
    
    # Create enhanced simulation
    sim = EnhancedLegalSimulation(
        prosecutor_strategy="aggressive",
        defense_strategy="moderate",
        judge_temperament="balanced"
    )
    
    # Prepare case
    print("Preparing case evidence...")
    evidence = sim.prepare_case(case_description)
    
    # Run extended trial
    print("\nRunning extended trial simulation...")
    messages, verdict = sim.run_extended_trial(
        num_exchanges=3,  # 3 rounds of back-and-forth
        include_procedural=True  # Include judge's procedural messages
    )
    
    print(f"\n{'='*60}")
    print("TRIAL COMPLETE")
    print(f"{'='*60}")
    print(f"Total messages exchanged: {len(messages)}")
    print(f"Trial duration: {(messages[-1].timestamp - messages[0].timestamp).seconds} seconds")
    print(f"Winner: {verdict.winner}")
    print(f"Confidence: {verdict.confidence_score:.1%}")
