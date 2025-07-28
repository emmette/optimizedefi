"""Orchestrator agent for query routing."""

import json
from typing import Dict, Any, Optional, List, Tuple
import re
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from app.agents.base import BaseAgent
from app.agents.config import AgentType, agent_config_manager
from app.services.performance_logger import performance_logger


class OrchestratorAgent(BaseAgent):
    """Agent responsible for routing queries to appropriate specialized agents."""
    
    def __init__(self):
        """Initialize the orchestrator agent."""
        config = agent_config_manager.get_config(AgentType.ORCHESTRATOR)
        super().__init__(
            name=config.name,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            system_prompt=config.system_prompt
        )
        self.config = config
        
        # Compile routing patterns
        self._compile_routing_patterns()
    
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt."""
        return self.config.system_prompt
    
    def _compile_routing_patterns(self):
        """Compile regex patterns for quick routing."""
        self.routing_patterns = {
            AgentType.PORTFOLIO: re.compile(
                r'\b(portfolio|balance|holdings?|assets?|tokens?|worth|value|positions?|wallet)\b',
                re.IGNORECASE
            ),
            AgentType.REBALANCING: re.compile(
                r'\b(rebalanc|optimiz|allocat|diversif|redistribut|adjust|strateg|risk)\b',
                re.IGNORECASE
            ),
            AgentType.SWAP: re.compile(
                r'\b(swap|exchange|trade|convert|sell|buy|quote|price|route|slippage)\b',
                re.IGNORECASE
            ),
            AgentType.GENERAL: re.compile(
                r'\b(what|how|why|explain|help|defi|protocol|yield|liquidity|gas)\b',
                re.IGNORECASE
            )
        }
    
    async def route_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Route a query to the appropriate agent.
        
        Args:
            query: User query
            context: Optional context
            
        Returns:
            Routing decision with agent selection and metadata
        """
        # Track routing operation
        async with performance_logger.log_operation(
            operation_type="query_routing",
            agent=self.name,
            model=self.model,
            query_length=len(query)
        ) as metrics:
            try:
                # First try pattern-based routing for speed
                pattern_match = self._pattern_based_routing(query)
                
                # If high confidence pattern match, use it
                if pattern_match and pattern_match["confidence"] >= 0.8:
                    metrics.metadata["routing_method"] = "pattern"
                    metrics.metadata["selected_agent"] = pattern_match["selected_agent"]
                    
                    performance_logger.log_agent_routing(
                        query=query,
                        selected_agent=pattern_match["selected_agent"],
                        confidence=pattern_match["confidence"],
                        routing_time_ms=metrics.duration_ms or 0
                    )
                    
                    return pattern_match
                
                # Use LLM for complex routing
                llm_result = await self._llm_based_routing(query, context)
                
                metrics.metadata["routing_method"] = "llm"
                metrics.metadata["selected_agent"] = llm_result["selected_agent"]
                
                performance_logger.log_agent_routing(
                    query=query,
                    selected_agent=llm_result["selected_agent"],
                    confidence=llm_result["confidence"],
                    routing_time_ms=metrics.duration_ms or 0,
                    alternatives=llm_result.get("alternatives", [])
                )
                
                return llm_result
                
            except Exception as e:
                # Default to general agent on error
                performance_logger.logger.error(
                    "routing_failed",
                    error=str(e),
                    query=query[:100]
                )
                
                return {
                    "selected_agent": AgentType.GENERAL.value,
                    "confidence": 0.5,
                    "reasoning": "Routing failed, defaulting to general agent",
                    "extracted_params": {},
                    "error": str(e)
                }
    
    def _pattern_based_routing(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Perform pattern-based routing for common queries.
        
        Args:
            query: User query
            
        Returns:
            Routing decision or None
        """
        matches = {}
        
        # Check each pattern
        for agent_type, pattern in self.routing_patterns.items():
            if pattern.search(query):
                # Count matches
                matches[agent_type] = len(pattern.findall(query))
        
        if not matches:
            return None
        
        # Select agent with most matches
        selected_agent = max(matches.items(), key=lambda x: x[1])[0]
        
        # Calculate confidence based on match strength
        total_matches = sum(matches.values())
        confidence = matches[selected_agent] / total_matches if total_matches > 0 else 0
        
        # Extract basic parameters
        params = self._extract_basic_params(query, selected_agent)
        
        return {
            "selected_agent": selected_agent.value,
            "confidence": min(confidence * 1.2, 1.0),  # Boost confidence slightly
            "reasoning": f"Pattern matching identified {matches[selected_agent]} keywords for {selected_agent.value}",
            "extracted_params": params,
            "method": "pattern"
        }
    
    def _extract_basic_params(
        self,
        query: str,
        agent_type: AgentType
    ) -> Dict[str, Any]:
        """
        Extract basic parameters from query.
        
        Args:
            query: User query
            agent_type: Selected agent type
            
        Returns:
            Extracted parameters
        """
        params = {}
        
        # Extract wallet address if present
        wallet_pattern = r'0x[a-fA-F0-9]{40}'
        wallet_match = re.search(wallet_pattern, query)
        if wallet_match:
            params["wallet_address"] = wallet_match.group()
        
        # Extract token symbols
        token_pattern = r'\b[A-Z]{2,10}\b'
        tokens = re.findall(token_pattern, query)
        if tokens:
            params["tokens"] = tokens
        
        # Extract amounts
        amount_pattern = r'\b(\d+(?:\.\d+)?)\s*(?:tokens?|eth|bnb|matic|usd[tc]?)\b'
        amounts = re.findall(amount_pattern, query, re.IGNORECASE)
        if amounts:
            params["amounts"] = [float(a) for a in amounts]
        
        # Agent-specific extraction
        if agent_type == AgentType.SWAP:
            # Extract from/to tokens
            swap_pattern = r'(?:swap|exchange|convert)\s+(\d*\.?\d*\s*)?(\w+)\s+(?:to|for)\s+(\w+)'
            swap_match = re.search(swap_pattern, query, re.IGNORECASE)
            if swap_match:
                if swap_match.group(1):
                    params["amount"] = float(swap_match.group(1).strip())
                params["from_token"] = swap_match.group(2).upper()
                params["to_token"] = swap_match.group(3).upper()
        
        return params
    
    async def _llm_based_routing(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Use LLM for sophisticated query routing.
        
        Args:
            query: User query
            context: Optional context
            
        Returns:
            Routing decision
        """
        # Prepare the routing prompt
        routing_prompt = f"""Analyze this user query and determine which specialized agent should handle it.

User Query: {query}

Context: {json.dumps(context or {}, indent=2)}

Available Agents:
1. portfolio - Portfolio analysis, balance checks, holdings overview
2. rebalancing - Portfolio optimization and rebalancing suggestions  
3. swap - Token swaps, quotes, and exchange operations
4. general - General DeFi questions, education, and other queries

Respond with ONLY a JSON object in this exact format:
{{
    "selected_agent": "agent_name",
    "confidence": 0.8,
    "reasoning": "Brief explanation",
    "extracted_params": {{}}
}}"""
        
        try:
            # Invoke the LLM
            response = await self.invoke(routing_prompt)
            
            # Extract JSON from response - try multiple methods
            content = response.content.strip()
            
            # Method 1: Try to parse the entire content as JSON
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Method 2: Find JSON block in markdown code block
                json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_block_match:
                    result = json.loads(json_block_match.group(1))
                else:
                    # Method 3: Find first complete JSON object
                    # This regex finds a JSON object by matching balanced braces
                    brace_count = 0
                    start_idx = content.find('{')
                    if start_idx == -1:
                        raise ValueError("No JSON object found in response")
                    
                    for i, char in enumerate(content[start_idx:], start_idx):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_str = content[start_idx:i+1]
                                result = json.loads(json_str)
                                break
                    else:
                        raise ValueError("Unclosed JSON object in response")
                
                # Validate and normalize result
                if "selected_agent" not in result:
                    raise ValueError("Missing selected_agent in response")
                
                # Ensure agent type is valid
                selected = result["selected_agent"]
                valid_agents = [a.value for a in AgentType if a != AgentType.ORCHESTRATOR]
                if selected not in valid_agents:
                    result["selected_agent"] = AgentType.GENERAL.value
                    result["confidence"] = 0.5
                
                return result
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            performance_logger.logger.error(
                "llm_routing_failed",
                error=str(e),
                query=query[:100]
            )
            
            # Fallback to general agent
            return {
                "selected_agent": AgentType.GENERAL.value,
                "confidence": 0.3,
                "reasoning": f"LLM routing failed: {str(e)}",
                "extracted_params": {}
            }
    
    async def analyze_routing_options(
        self,
        query: str
    ) -> List[Dict[str, float]]:
        """
        Analyze all possible routing options with scores.
        
        Args:
            query: User query
            
        Returns:
            List of agents with confidence scores
        """
        options = []
        
        # Check each agent type
        for agent_type in AgentType:
            if agent_type == AgentType.ORCHESTRATOR:
                continue
            
            config = agent_config_manager.get_config(agent_type)
            
            # Calculate keyword match score
            keywords = query.lower().split()
            agent_keywords = [k.lower() for k in config.routing_keywords]
            
            matches = sum(1 for k in keywords if any(ak in k for ak in agent_keywords))
            score = matches / len(keywords) if keywords else 0
            
            options.append({
                "agent": agent_type.value,
                "score": round(score, 3),
                "capabilities": config.capabilities[:3]  # Top 3 capabilities
            })
        
        # Sort by score
        options.sort(key=lambda x: x["score"], reverse=True)
        
        return options
    
    async def route_with_history(
        self,
        query: str,
        conversation_history: List[BaseMessage],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Route query considering conversation history.
        
        Args:
            query: Current user query
            conversation_history: Previous messages
            context: Optional context
            
        Returns:
            Routing decision
        """
        # Build context from history
        if not context:
            context = {}
        
        # Extract relevant context from history
        if conversation_history:
            # Get last agent used
            for msg in reversed(conversation_history):
                if hasattr(msg, 'metadata') and 'agent' in msg.metadata:
                    context["last_agent"] = msg.metadata["agent"]
                    break
            
            # Get recent topics
            recent_topics = []
            for msg in conversation_history[-5:]:  # Last 5 messages
                if isinstance(msg, HumanMessage):
                    recent_topics.append(msg.content[:50])
            context["recent_topics"] = recent_topics
        
        # Route with enhanced context
        result = await self.route_query(query, context)
        
        # Consider conversation continuity
        if "last_agent" in context and result["confidence"] < 0.7:
            # Slight preference for continuing with same agent
            if context["last_agent"] == result["selected_agent"]:
                result["confidence"] = min(result["confidence"] * 1.2, 1.0)
                result["reasoning"] += " (continuing conversation)"
        
        return result