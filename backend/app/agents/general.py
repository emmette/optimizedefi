"""General Q&A agent for DeFi queries."""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from langchain_core.tools import Tool

from app.agents.base import BaseAgent
from app.agents.config import AgentType, agent_config_manager
from app.services.performance_logger import performance_logger


class GeneralAgent(BaseAgent):
    """Agent for general DeFi questions and educational content."""
    
    # Common DeFi topics for better responses
    DEFI_TOPICS = {
        "yield_farming": "Earning rewards by providing liquidity",
        "liquidity_pools": "Paired token reserves for trading",
        "impermanent_loss": "Temporary loss from providing liquidity",
        "amm": "Automated Market Maker protocols",
        "tvl": "Total Value Locked in protocols",
        "apy_apr": "Annual Percentage Yield vs Rate",
        "gas_optimization": "Reducing transaction costs",
        "mev": "Maximum Extractable Value",
        "bridges": "Cross-chain asset transfers",
        "governance": "Protocol decision making"
    }
    
    def __init__(self, tools: Optional[List[Tool]] = None):
        """
        Initialize the general agent.
        
        Args:
            tools: Optional list of tools
        """
        config = agent_config_manager.get_config(AgentType.GENERAL)
        super().__init__(
            name=config.name,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            system_prompt=config.system_prompt,
            tools=tools
        )
        self.config = config
    
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt."""
        return self.config.system_prompt
    
    async def answer_question(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        education_level: str = "intermediate"
    ) -> str:
        """
        Answer a general DeFi question.
        
        Args:
            query: User's question
            context: Additional context
            education_level: User's knowledge level
            
        Returns:
            Educational answer
        """
        async with performance_logger.log_operation(
            operation_type="general_qa",
            agent=self.name,
            model=self.model,
            education_level=education_level
        ) as metrics:
            try:
                # Enhance query with context
                enhanced_query = self._enhance_educational_query(
                    query, context, education_level
                )
                
                # Get response
                if self.tools:
                    response, tool_calls = await self.invoke_with_tools(
                        enhanced_query,
                        context=context
                    )
                    metrics.metadata["tools_used"] = len(tool_calls)
                else:
                    response = await self.invoke(enhanced_query, context=context)
                    metrics.metadata["tools_used"] = 0
                
                # Detect topic for metrics
                topic = self._detect_topic(query)
                metrics.metadata["topic"] = topic
                
                return response.content if hasattr(response, 'content') else str(response)
                
            except Exception as e:
                performance_logger.logger.error(
                    "general_qa_failed",
                    error=str(e),
                    query=query[:100]
                )
                raise
    
    def _enhance_educational_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]],
        education_level: str
    ) -> str:
        """Enhance query with educational context."""
        parts = [query]
        
        # Add education level guidance
        level_guidance = {
            "beginner": "Explain in simple terms with analogies",
            "intermediate": "Provide detailed explanation with examples",
            "advanced": "Include technical details and edge cases"
        }
        
        parts.append(f"\nEducation Level: {education_level}")
        parts.append(f"Approach: {level_guidance.get(education_level, level_guidance['intermediate'])}")
        
        if context:
            if "user_holdings" in context:
                parts.append("\nUser has DeFi experience (holds tokens)")
            if "previous_topics" in context:
                parts.append(f"Previously discussed: {', '.join(context['previous_topics'][:3])}")
        
        return "\n".join(parts)
    
    def _detect_topic(self, query: str) -> str:
        """Detect the main topic of the query."""
        query_lower = query.lower()
        
        for topic, keywords in self.DEFI_TOPICS.items():
            if topic.replace("_", " ") in query_lower or any(
                word in query_lower for word in keywords.lower().split()
            ):
                return topic
        
        return "general_defi"
    
    async def explain_concept(
        self,
        concept: str,
        depth: str = "comprehensive",
        examples: bool = True
    ) -> str:
        """
        Explain a DeFi concept in detail.
        
        Args:
            concept: Concept to explain
            depth: Level of detail
            examples: Whether to include examples
            
        Returns:
            Concept explanation
        """
        prompt = f"""Explain the DeFi concept: {concept}

Depth: {depth}
Include Examples: {examples}

Structure your explanation:
1. Simple definition
2. How it works
3. Why it matters
4. Common use cases
5. Risks and considerations
{"6. Practical examples" if examples else ""}

Make it educational and accessible."""
        
        response = await self.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    
    async def provide_tutorial(
        self,
        task: str,
        platform: Optional[str] = None,
        step_by_step: bool = True
    ) -> str:
        """
        Provide a tutorial for a DeFi task.
        
        Args:
            task: Task to explain
            platform: Specific platform/protocol
            step_by_step: Whether to break into steps
            
        Returns:
            Tutorial content
        """
        prompt = f"""Create a tutorial for: {task}
{f"Platform: {platform}" if platform else "Platform: Any popular DeFi protocol"}

Format: {"Step-by-step guide" if step_by_step else "Overview guide"}

Include:
1. Prerequisites
2. Required tools/wallets
3. {"Detailed steps" if step_by_step else "Process overview"}
4. Expected outcomes
5. Common mistakes to avoid
6. Safety tips

Make it practical and actionable."""
        
        response = await self.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    
    async def analyze_protocol(
        self,
        protocol_name: str,
        aspects: Optional[List[str]] = None
    ) -> str:
        """
        Analyze a DeFi protocol.
        
        Args:
            protocol_name: Name of the protocol
            aspects: Specific aspects to analyze
            
        Returns:
            Protocol analysis
        """
        if not aspects:
            aspects = ["overview", "risks", "opportunities", "tokenomics"]
        
        prompt = f"""Analyze the DeFi protocol: {protocol_name}

Focus on these aspects:
{chr(10).join(f"- {aspect}" for aspect in aspects)}

Provide objective analysis including:
1. What the protocol does
2. Key features and innovations
3. Risk assessment
4. Competitive advantages
5. Potential concerns
6. Overall assessment

Be balanced and factual."""
        
        response = await self.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    
    async def compare_protocols(
        self,
        protocol1: str,
        protocol2: str,
        comparison_criteria: Optional[List[str]] = None
    ) -> str:
        """
        Compare two DeFi protocols.
        
        Args:
            protocol1: First protocol
            protocol2: Second protocol
            comparison_criteria: Criteria for comparison
            
        Returns:
            Comparison analysis
        """
        if not comparison_criteria:
            comparison_criteria = [
                "functionality", "fees", "security",
                "liquidity", "user experience"
            ]
        
        prompt = f"""Compare these DeFi protocols:
- {protocol1}
- {protocol2}

Comparison criteria:
{chr(10).join(f"- {criterion}" for criterion in comparison_criteria)}

Provide a balanced comparison:
1. Overview of each protocol
2. Side-by-side comparison
3. Strengths and weaknesses
4. Best use cases for each
5. Recommendation based on user needs"""
        
        response = await self.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    
    async def explain_transaction(
        self,
        tx_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Explain a type of DeFi transaction.
        
        Args:
            tx_type: Type of transaction
            details: Additional details
            
        Returns:
            Transaction explanation
        """
        prompt = f"""Explain this DeFi transaction type: {tx_type}

{f"Details: {json.dumps(details, indent=2)}" if details else ""}

Explain:
1. What this transaction does
2. Gas costs involved
3. Risks and considerations
4. Best practices
5. How to verify success

Use clear, non-technical language where possible."""
        
        response = await self.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    
    async def safety_check(
        self,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Provide safety guidance for a DeFi action.
        
        Args:
            action: Action user wants to take
            context: Additional context
            
        Returns:
            Safety guidance
        """
        prompt = f"""Provide safety guidance for: {action}

{f"Context: {json.dumps(context, indent=2)}" if context else ""}

Cover:
1. Main risks involved
2. Security best practices
3. Red flags to watch for
4. How to verify legitimacy
5. Recovery options if something goes wrong

Prioritize user safety and asset protection."""
        
        response = await self.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    
    async def market_insight(
        self,
        topic: str,
        timeframe: str = "current"
    ) -> str:
        """
        Provide market insights.
        
        Args:
            topic: Market topic
            timeframe: Time perspective
            
        Returns:
            Market insights
        """
        prompt = f"""Provide DeFi market insights on: {topic}

Timeframe: {timeframe}

Include:
1. Current state of the topic
2. Recent developments
3. Key factors to watch
4. Potential implications
5. Educational context

Note: Avoid price predictions or financial advice.
Focus on educational market understanding."""
        
        response = await self.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)