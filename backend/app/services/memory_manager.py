"""Conversation memory management service with automatic summarization."""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass, field
from collections import defaultdict
import tiktoken
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from app.services.performance_logger import performance_logger
from app.core.config import settings


@dataclass
class MemoryConfig:
    """Configuration for memory management."""
    max_context_percentage: float = 0.4  # 40% of context window
    summarization_model: str = "google/gemini-2.0-flash"  # Cheap, fast model
    summarization_temperature: float = 0.3  # Low temperature for consistency
    session_timeout_minutes: int = 30
    preserve_recent_messages: int = 10  # Always keep last N messages
    max_summary_tokens: int = 500  # Max tokens for summary
    
    # Entities to preserve in summaries
    preserve_entities: List[str] = field(default_factory=lambda: [
        "wallet_addresses",
        "token_amounts",
        "token_symbols",
        "decisions_made",
        "swap_details",
        "portfolio_values"
    ])
    
    # Configurable summarization prompt
    summarization_prompt_template: str = """Summarize the following conversation history, preserving key information:

Entities to preserve:
{preserve_entities}

Conversation:
{conversation}

Create a concise summary that captures:
1. Main topics discussed
2. Key decisions and outcomes
3. Important numerical values and addresses
4. User preferences expressed

Keep the summary under {max_tokens} tokens."""


@dataclass
class ConversationSession:
    """A single conversation session."""
    session_id: str
    user_address: Optional[str]
    messages: List[BaseMessage] = field(default_factory=list)
    summary: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    total_tokens: int = 0
    summarization_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationMemoryManager:
    """Manages conversation memory with automatic summarization."""
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        """
        Initialize the memory manager.
        
        Args:
            config: Memory configuration
        """
        self.config = config or MemoryConfig()
        self.sessions: Dict[str, ConversationSession] = {}
        self._lock = asyncio.Lock()
        
        # Initialize tokenizer
        try:
            self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        except:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_expired_sessions())
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))
    
    def _count_message_tokens(self, message: BaseMessage) -> int:
        """Count tokens in a message."""
        # Rough estimate including message structure overhead
        return self._count_tokens(message.content) + 10
    
    async def get_or_create_session(
        self,
        session_id: str,
        user_address: Optional[str] = None
    ) -> ConversationSession:
        """
        Get existing session or create new one.
        
        Args:
            session_id: Session identifier
            user_address: Optional user wallet address
            
        Returns:
            Conversation session
        """
        async with self._lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = ConversationSession(
                    session_id=session_id,
                    user_address=user_address
                )
                
                performance_logger.log_custom(
                    "memory_session_created",
                    session_id=session_id,
                    user_address=user_address
                )
            
            session = self.sessions[session_id]
            session.last_activity = datetime.utcnow()
            return session
    
    async def add_message(
        self,
        session_id: str,
        message: BaseMessage,
        context_window_size: int = 8192
    ) -> bool:
        """
        Add message to session and check if summarization is needed.
        
        Args:
            session_id: Session identifier
            message: Message to add
            context_window_size: Model's context window size
            
        Returns:
            True if summarization was triggered
        """
        session = await self.get_or_create_session(session_id)
        
        async with self._lock:
            # Add message
            session.messages.append(message)
            
            # Count tokens
            message_tokens = self._count_message_tokens(message)
            session.total_tokens += message_tokens
            
            # Log message addition
            performance_logger.log_memory_operation(
                operation="add_message",
                memory_type="conversation",
                size_bytes=len(message.content.encode()),
                metadata={
                    "session_id": session_id,
                    "message_type": type(message).__name__,
                    "tokens": message_tokens,
                    "total_tokens": session.total_tokens
                }
            )
            
            # Check if summarization is needed
            threshold = int(context_window_size * self.config.max_context_percentage)
            
            if session.total_tokens > threshold:
                # Trigger summarization
                await self._summarize_conversation(session_id, context_window_size)
                return True
            
            return False
    
    async def _summarize_conversation(
        self,
        session_id: str,
        context_window_size: int
    ):
        """
        Summarize older messages to reduce token count.
        
        Args:
            session_id: Session identifier
            context_window_size: Model's context window size
        """
        session = self.sessions.get(session_id)
        if not session or len(session.messages) <= self.config.preserve_recent_messages:
            return
        
        try:
            # Track summarization
            async with performance_logger.log_operation(
                operation_type="memory_summarization",
                session_id=session_id,
                message_count=len(session.messages)
            ) as metrics:
                # Split messages
                messages_to_summarize = session.messages[:-self.config.preserve_recent_messages]
                recent_messages = session.messages[-self.config.preserve_recent_messages:]
                
                # Prepare conversation text
                conversation_text = self._format_messages_for_summary(messages_to_summarize)
                
                # Create summarization prompt
                prompt = self.config.summarization_prompt_template.format(
                    preserve_entities="\n".join(f"- {e}" for e in self.config.preserve_entities),
                    conversation=conversation_text,
                    max_tokens=self.config.max_summary_tokens
                )
                
                # Import here to avoid circular dependency
                from app.agents.base import BaseAgent
                
                # Create summarizer agent
                summarizer = BaseAgent(
                    name="MemorySummarizer",
                    model=self.config.summarization_model,
                    temperature=self.config.summarization_temperature,
                    max_tokens=self.config.max_summary_tokens,
                    system_prompt="You are a conversation summarizer. Create concise summaries that preserve key information."
                )
                
                # Get summary
                response = await summarizer.invoke(prompt)
                summary_text = response.content if hasattr(response, 'content') else str(response)
                
                # Create new summary message
                if session.summary:
                    # Combine with existing summary
                    combined_summary = f"Previous Summary:\n{session.summary}\n\nAdditional Summary:\n{summary_text}"
                    summary_tokens = self._count_tokens(combined_summary)
                    
                    # If combined is too long, summarize the summaries
                    if summary_tokens > self.config.max_summary_tokens:
                        meta_prompt = f"Combine these summaries into one concise summary under {self.config.max_summary_tokens} tokens:\n\n{combined_summary}"
                        meta_response = await summarizer.invoke(meta_prompt)
                        session.summary = meta_response.content if hasattr(meta_response, 'content') else str(meta_response)
                    else:
                        session.summary = combined_summary
                else:
                    session.summary = summary_text
                
                # Replace old messages with summary + recent
                summary_message = SystemMessage(
                    content=f"[Conversation Summary]\n{session.summary}",
                    metadata={"is_summary": True, "summarized_at": datetime.utcnow().isoformat()}
                )
                
                session.messages = [summary_message] + recent_messages
                
                # Recalculate tokens
                old_tokens = session.total_tokens
                session.total_tokens = sum(self._count_message_tokens(m) for m in session.messages)
                session.summarization_count += 1
                
                # Log results
                metrics.metadata["old_message_count"] = len(messages_to_summarize)
                metrics.metadata["tokens_before"] = old_tokens
                metrics.metadata["tokens_after"] = session.total_tokens
                metrics.metadata["tokens_saved"] = old_tokens - session.total_tokens
                
                performance_logger.log_custom(
                    "memory_summarization_complete",
                    session_id=session_id,
                    messages_summarized=len(messages_to_summarize),
                    tokens_saved=old_tokens - session.total_tokens,
                    summarization_count=session.summarization_count
                )
                
        except Exception as e:
            performance_logger.logger.error(
                "memory_summarization_failed",
                session_id=session_id,
                error=str(e),
                error_type=type(e).__name__
            )
    
    def _format_messages_for_summary(self, messages: List[BaseMessage]) -> str:
        """Format messages for summarization."""
        formatted = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                agent = msg.metadata.get("agent", "AI") if hasattr(msg, "metadata") else "AI"
                formatted.append(f"{agent}: {msg.content}")
            elif isinstance(msg, SystemMessage) and not msg.metadata.get("is_summary"):
                formatted.append(f"System: {msg.content}")
        
        return "\n\n".join(formatted)
    
    async def get_messages_for_context(
        self,
        session_id: str,
        max_tokens: Optional[int] = None
    ) -> List[BaseMessage]:
        """
        Get messages optimized for LLM context.
        
        Args:
            session_id: Session identifier
            max_tokens: Optional max tokens to return
            
        Returns:
            List of messages
        """
        session = self.sessions.get(session_id)
        if not session:
            return []
        
        async with self._lock:
            if not max_tokens:
                return session.messages.copy()
            
            # Return messages that fit in token limit
            messages = []
            token_count = 0
            
            # Start from most recent
            for msg in reversed(session.messages):
                msg_tokens = self._count_message_tokens(msg)
                if token_count + msg_tokens > max_tokens:
                    break
                messages.insert(0, msg)
                token_count += msg_tokens
            
            return messages
    
    async def clear_session(self, session_id: str):
        """Clear a specific session."""
        async with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                
                performance_logger.log_memory_operation(
                    operation="clear",
                    memory_type="conversation",
                    metadata={"session_id": session_id}
                )
    
    async def get_session_metrics(self, session_id: str) -> Dict[str, Any]:
        """Get metrics for a session."""
        session = self.sessions.get(session_id)
        if not session:
            return {}
        
        return {
            "session_id": session_id,
            "user_address": session.user_address,
            "message_count": len(session.messages),
            "total_tokens": session.total_tokens,
            "summarization_count": session.summarization_count,
            "has_summary": session.summary is not None,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "duration_minutes": (session.last_activity - session.created_at).total_seconds() / 60
        }
    
    async def _cleanup_expired_sessions(self):
        """Background task to clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                async with self._lock:
                    now = datetime.utcnow()
                    timeout_delta = timedelta(minutes=self.config.session_timeout_minutes)
                    
                    expired_sessions = []
                    for session_id, session in self.sessions.items():
                        if now - session.last_activity > timeout_delta:
                            expired_sessions.append(session_id)
                    
                    for session_id in expired_sessions:
                        del self.sessions[session_id]
                        
                        performance_logger.log_custom(
                            "memory_session_expired",
                            session_id=session_id
                        )
                        
            except Exception as e:
                performance_logger.logger.error(
                    "memory_cleanup_error",
                    error=str(e)
                )


# Global memory manager instance
memory_manager = ConversationMemoryManager()