import asyncio
from rapidfuzz import process
from app.db.models.user import User
from langchain_groq import ChatGroq
from app.core.config import settings
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from app.schemas.chatbot import IntentClassification, DecomposedQueries, Reflection
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Annotated, Literal, TypedDict, List, AsyncGenerator
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage, AIMessage, ToolMessage
from app.services.chatbot_tools import get_chatbot_tools
from app.services.chatbot_instructions import (
    IDEAL_QUERIES,
    INTENT_PROMPT_TEMPLATE, 
    SYSTEM_PROMPT_TEMPLATE, 
    ENHANCEMENT_AND_DECOMPOSITION_PROMPT,
    REFLECTION_PROMPT_TEMPLATE
)

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

class ChatbotService:
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in environment or .env file.")
        self.model = ChatGroq(model="llama-3.1-8b-instant", api_key=settings.GROQ_API_KEY, temperature=0.0)
        self.checkpointer = MemorySaver()

    async def detect_intent(self, query: str, user: User) -> str:
        all_intents = ["event_query", "booking_query", "general_query", "other"]
        
        intent_prompt = INTENT_PROMPT_TEMPLATE.format(query=query, all_intents=', '.join(all_intents))
        
        intent_classifier = self.model.with_structured_output(IntentClassification)
        try:
            intent_result = await intent_classifier.ainvoke([SystemMessage(content=intent_prompt)])
            user_intent = intent_result.intent
        except Exception:
            user_intent = "other"
        
        if user_intent not in all_intents:
            user_intent = "other"
        
        return user_intent

    async def query_llm(self, query: str, user: User, user_intent: str, session: AsyncSession) -> str:
        tool_map = get_chatbot_tools(session, user)
        common_tools = [tool_map["list_events"], tool_map["search_events"]]
        
        if user_intent == "event_query":
            tools = common_tools + [
                tool_map["create_event"],
                tool_map["update_event"],
                tool_map["delete_event"],
                tool_map["get_event_attendees"]
            ]
        elif user_intent == "booking_query":
            tools = common_tools + [
                tool_map["create_booking"],
                tool_map["get_user_bookings"],
                tool_map["cancel_booking"]
            ]
        else:
            tools = [] 

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(user_role=user.role.value)

        if tools:
            model_to_use = self.model.bind_tools(tools, parallel_tool_calls=True)
        else:
            model_to_use = self.model

        async def agent_node(state: AgentState):
            # SAFE CONTEXT PRUNING: Keep max 15 messages to prevent Token Limit Exhaustion
            pruned_msgs = state["messages"]
            if len(pruned_msgs) > 15:
                pruned_msgs = pruned_msgs[-15:]
                # Guarantee we don't severe a ToolMessage from its parent AIMessage (Causes API Crash)
                while pruned_msgs and (isinstance(pruned_msgs[0], ToolMessage) or (isinstance(pruned_msgs[0], AIMessage) and getattr(pruned_msgs[0], 'tool_calls', None))):
                    pruned_msgs.pop(0)
                    
            messages = [SystemMessage(content=system_prompt)] + pruned_msgs
            try:
                response = await model_to_use.ainvoke(messages)
            except Exception as e:
                return {"messages": [AIMessage(content="I encountered a technical issue. Please try again.")]}
            return {"messages": [response]}

        async def reflection_node(state: AgentState):
            reflector = self.model.with_structured_output(Reflection)
            try:
                critiques = [m for m in state["messages"] if isinstance(m, HumanMessage) and m.content.startswith("CRITIQUE:")]
                if len(critiques) >= 2:  # Max 2 self-correction attempts logic
                    return {"messages": []}

                res = await reflector.ainvoke(state["messages"] + [SystemMessage(content=REFLECTION_PROMPT_TEMPLATE)])
                if res.grade != "Pass":
                    return {"messages": [HumanMessage(content=f"CRITIQUE: {res.grade}")]}
                return {"messages": []}
            except Exception:
                return {"messages": []}

        workflow = StateGraph(AgentState)
        workflow.add_node("agent", agent_node)
        workflow.add_edge(START, "agent")
        
        if tools:
            workflow.add_node("tools", ToolNode(tools))
            workflow.add_node("reflection", reflection_node)
            
            def should_continue(state: AgentState) -> Literal["tools", "reflection"]:
                last_message = state["messages"][-1]
                if getattr(last_message, 'tool_calls', None):
                    return "tools"
                return "reflection"
                
            def route_after_reflection(state: AgentState) -> Literal["agent", END]:
                last_msg = state["messages"][-1]
                if isinstance(last_msg, HumanMessage) and last_msg.content.startswith("CRITIQUE:"):
                    return "agent"
                return END
                
            workflow.add_conditional_edges("agent", should_continue)
            workflow.add_conditional_edges("reflection", route_after_reflection)
            workflow.add_edge("tools", "agent")
        else:
            workflow.add_edge("agent", END)

        app = workflow.compile(checkpointer=self.checkpointer)

        # EXECUTE
        inputs = {"messages": [HumanMessage(content=query)]}
        config = {"configurable": {"thread_id": str(user.id)}}
        
        async for event in app.astream_events(inputs, config=config, version="v2"):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                if "chunk" in event["data"]:
                    content = event["data"]["chunk"].content
                    if isinstance(content, str) and content:
                        yield content

    async def analyze_and_decompose_query(self, query: str) -> List[str]:
        best_match = process.extractOne(query, IDEAL_QUERIES)
        
        # Lowered fuzz threshold to safely skip LLM decomposition more often (latency shredder)
        if best_match and best_match[1] >= 75:
            return [query]

        # Explicitly ask LLM to decompose compound queries, or fix messy text
        enhancement_prompt = ENHANCEMENT_AND_DECOMPOSITION_PROMPT.format(raw_query=query)
        enhancer = self.model.with_structured_output(DecomposedQueries)
        try:
            result = await enhancer.ainvoke([SystemMessage(content=enhancement_prompt)])
            return [q.lower().strip() for q in result.queries]
        except Exception:
            return [query] # Fallback if API fails

    async def process_query(self, query: str, user: User, session: AsyncSession) -> AsyncGenerator[str, None]:
        clean_queries = await self.analyze_and_decompose_query(query)

        for i, q in enumerate(clean_queries):
            if i > 0:
                yield "\n\n"
                
            if q == "other":
                yield "I am strictly an Event Booking Assistant. I can only assist you with event and booking related tasks."
                continue
                
            user_intent = await self.detect_intent(q, user)
            print(f"Sub-Query: '{q}' -> Intent: {user_intent}")
            
            if user_intent == "other":
                yield "I am strictly an Event Booking Assistant. I can only assist you with event and booking related tasks."
                continue
                
            async for chunk in self.query_llm(q, user, user_intent, session):
                yield chunk

chatbot_service = ChatbotService()
