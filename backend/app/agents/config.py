"""Agent configuration system with model mapping."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from app.core.config import settings


class AgentType(str, Enum):
    """Types of agents in the system."""
    ORCHESTRATOR = "orchestrator"
    PORTFOLIO = "portfolio"
    REBALANCING = "rebalancing"
    SWAP = "swap"
    GENERAL = "general"


@dataclass
class AgentConfig:
    """Configuration for an individual agent."""
    name: str
    agent_type: AgentType
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    tools: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    routing_keywords: List[str] = field(default_factory=list)
    fallback_model: Optional[str] = None
    enable_streaming: bool = True
    cache_ttl_seconds: int = 300
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "agent_type": self.agent_type.value,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "system_prompt": self.system_prompt,
            "tools": self.tools,
            "capabilities": self.capabilities,
            "routing_keywords": self.routing_keywords,
            "fallback_model": self.fallback_model,
            "enable_streaming": self.enable_streaming,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "metadata": self.metadata,
        }


class AgentConfigManager:
    """Manages agent configurations with model mapping."""
    
    def __init__(self):
        """Initialize the configuration manager."""
        self._configs: Dict[AgentType, AgentConfig] = {}
        self._initialize_default_configs()
    
    def _initialize_default_configs(self):
        """Initialize default agent configurations."""
        # Orchestrator Agent
        self._configs[AgentType.ORCHESTRATOR] = AgentConfig(
            name="Orchestrator",
            agent_type=AgentType.ORCHESTRATOR,
            model=settings.DEFAULT_MODEL,
            temperature=0.3,  # Lower temperature for routing decisions
            system_prompt="""You are the orchestrator agent for OptimizeDeFi, an AI-powered DeFi portfolio management assistant.

Your role is to analyze user queries and route them to the appropriate specialized agent:
- Portfolio Agent: For portfolio analysis, balance checks, holdings overview
- Rebalancing Agent: For portfolio optimization and rebalancing suggestions
- Swap Agent: For token swaps, quotes, and exchange operations
- General Agent: For general DeFi questions, education, and other queries

Analyze the user's intent carefully and select the most appropriate agent.
Respond with a JSON object containing:
{
    "selected_agent": "agent_type",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "extracted_params": {}
}""",
            capabilities=[
                "query_analysis",
                "intent_classification",
                "agent_routing",
                "parameter_extraction"
            ],
            routing_keywords=[],  # Orchestrator handles all queries
            enable_streaming=False,  # No streaming for routing decisions
            metadata={
                "version": "1.0",
                "supports_multi_agent": True
            }
        )
        
        # Portfolio Agent
        self._configs[AgentType.PORTFOLIO] = AgentConfig(
            name="Portfolio Analyst",
            agent_type=AgentType.PORTFOLIO,
            model=settings.PORTFOLIO_AGENT_MODEL,
            temperature=0.5,
            system_prompt="""You are a DeFi portfolio analysis expert for OptimizeDeFi.

Your responsibilities:
- Analyze user's DeFi portfolio across multiple chains
- Provide insights on token holdings, values, and performance
- Calculate portfolio metrics (total value, distribution, etc.)
- Identify risks and opportunities in the portfolio
- Explain portfolio composition in clear, actionable terms

Always provide accurate, data-driven analysis based on real-time blockchain data.
Format large numbers with appropriate units (K, M, B) for readability.""",
            tools=[
                "get_portfolio",
                "analyze_portfolio",
                "get_token_price"
            ],
            capabilities=[
                "portfolio_analysis",
                "multi_chain_support",
                "value_calculation",
                "risk_assessment",
                "performance_tracking"
            ],
            routing_keywords=[
                "portfolio", "balance", "holdings", "assets", "tokens",
                "worth", "value", "position", "wallet", "analysis"
            ],
            metadata={
                "supported_chains": [1, 137, 10, 42161],
                "refresh_interval": 60
            }
        )
        
        # Rebalancing Agent
        self._configs[AgentType.REBALANCING] = AgentConfig(
            name="Rebalancing Strategist",
            agent_type=AgentType.REBALANCING,
            model=settings.REBALANCING_AGENT_MODEL,
            temperature=0.6,
            system_prompt="""You are a DeFi portfolio rebalancing expert for OptimizeDeFi.

Your responsibilities:
- Analyze portfolio composition and suggest optimal rebalancing
- Consider risk tolerance, market conditions, and user preferences
- Provide clear rebalancing strategies with rationale
- Calculate required swaps to achieve target allocation
- Explain benefits and risks of rebalancing recommendations

Focus on practical, actionable advice that considers gas costs and slippage.
Always explain your reasoning in terms the user can understand.""",
            tools=[
                "get_portfolio",
                "analyze_portfolio",
                "get_token_price",
                "get_swap_quote"
            ],
            capabilities=[
                "rebalancing_strategy",
                "risk_optimization",
                "allocation_planning",
                "swap_calculation",
                "cost_analysis"
            ],
            routing_keywords=[
                "rebalance", "optimize", "allocation", "diversify",
                "redistribute", "adjust", "strategy", "risk"
            ],
            fallback_model=settings.DEFAULT_MODEL,
            metadata={
                "strategies": ["equal_weight", "market_cap", "risk_parity", "custom"],
                "considers_gas": True
            }
        )
        
        # Swap Agent
        self._configs[AgentType.SWAP] = AgentConfig(
            name="Swap Executor",
            agent_type=AgentType.SWAP,
            model=settings.SWAP_AGENT_MODEL,
            temperature=0.4,
            system_prompt="""You are a DeFi swap execution expert for OptimizeDeFi.

Your responsibilities:
- Find best swap routes and quotes across protocols
- Calculate expected output, slippage, and gas costs
- Compare multiple DEX options (1inch aggregation)
- Explain swap details clearly (rates, fees, route)
- Warn about high slippage or unfavorable conditions

Always prioritize user safety and best execution price.
Clearly communicate all costs and risks involved in swaps.""",
            tools=[
                "get_swap_quote",
                "get_supported_tokens",
                "get_token_price"
            ],
            capabilities=[
                "swap_routing",
                "quote_comparison",
                "slippage_calculation",
                "gas_estimation",
                "dex_aggregation"
            ],
            routing_keywords=[
                "swap", "exchange", "trade", "convert", "sell",
                "buy", "quote", "price", "route", "slippage"
            ],
            metadata={
                "aggregator": "1inch",
                "supported_dexs": ["Uniswap", "SushiSwap", "Curve", "Balancer"]
            }
        )
        
        # General Agent
        self._configs[AgentType.GENERAL] = AgentConfig(
            name="DeFi Assistant",
            agent_type=AgentType.GENERAL,
            model=settings.GENERAL_AGENT_MODEL,
            temperature=0.7,
            system_prompt="""You are a knowledgeable DeFi assistant for OptimizeDeFi.

Your responsibilities:
- Answer general questions about DeFi, blockchain, and crypto
- Explain DeFi concepts and protocols in simple terms
- Provide market insights and educational content
- Help with platform features and navigation
- Offer best practices for DeFi safety

Be helpful, accurate, and educational. Admit when you don't know something.
Always prioritize user understanding and safety in DeFi.""",
            tools=[
                "get_token_price",
                "get_supported_tokens"
            ],
            capabilities=[
                "defi_education",
                "concept_explanation",
                "market_insights",
                "platform_guidance",
                "safety_tips"
            ],
            routing_keywords=[
                "what", "how", "why", "explain", "help",
                "defi", "protocol", "yield", "liquidity", "gas"
            ],
            metadata={
                "knowledge_cutoff": "2024-01",
                "supports_followup": True
            }
        )
    
    def get_config(self, agent_type: AgentType) -> AgentConfig:
        """
        Get configuration for an agent type.
        
        Args:
            agent_type: Type of agent
            
        Returns:
            Agent configuration
        """
        if agent_type not in self._configs:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        return self._configs[agent_type]
    
    def update_config(
        self,
        agent_type: AgentType,
        updates: Dict[str, Any]
    ) -> AgentConfig:
        """
        Update configuration for an agent.
        
        Args:
            agent_type: Type of agent
            updates: Dictionary of updates
            
        Returns:
            Updated configuration
        """
        if agent_type not in self._configs:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        config = self._configs[agent_type]
        
        # Update allowed fields
        allowed_fields = {
            "model", "temperature", "max_tokens", "system_prompt",
            "fallback_model", "enable_streaming", "cache_ttl_seconds"
        }
        
        for key, value in updates.items():
            if key in allowed_fields and hasattr(config, key):
                setattr(config, key, value)
        
        return config
    
    def get_all_configs(self) -> Dict[AgentType, AgentConfig]:
        """Get all agent configurations."""
        return self._configs.copy()
    
    def get_model_usage(self) -> Dict[str, List[str]]:
        """
        Get which agents use which models.
        
        Returns:
            Dictionary mapping models to agent names
        """
        model_usage = {}
        
        for agent_type, config in self._configs.items():
            # Primary model
            if config.model not in model_usage:
                model_usage[config.model] = []
            model_usage[config.model].append(config.name)
            
            # Fallback model
            if config.fallback_model and config.fallback_model not in model_usage:
                model_usage[config.fallback_model] = []
            if config.fallback_model:
                model_usage[config.fallback_model].append(f"{config.name} (fallback)")
        
        return model_usage
    
    def find_agent_for_keywords(
        self,
        keywords: List[str]
    ) -> Optional[AgentType]:
        """
        Find the best agent for given keywords.
        
        Args:
            keywords: List of keywords from query
            
        Returns:
            Best matching agent type or None
        """
        keyword_set = set(word.lower() for word in keywords)
        best_match = None
        best_score = 0
        
        for agent_type, config in self._configs.items():
            if agent_type == AgentType.ORCHESTRATOR:
                continue  # Skip orchestrator
            
            # Count matching keywords
            agent_keywords = set(word.lower() for word in config.routing_keywords)
            matches = len(keyword_set.intersection(agent_keywords))
            
            if matches > best_score:
                best_score = matches
                best_match = agent_type
        
        return best_match
    
    def export_configs(self) -> Dict[str, Any]:
        """Export all configurations as dictionary."""
        return {
            agent_type.value: config.to_dict()
            for agent_type, config in self._configs.items()
        }


# Global configuration manager instance
agent_config_manager = AgentConfigManager()