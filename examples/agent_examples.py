"""
Example usage of the BaseAgent class demonstrating various features.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.baseAgent import BaseAgent


def example_basic_agent():
    """Example 1: Basic agent with system prompt and simple conversation"""
    print("=" * 60)
    print("EXAMPLE 1: Basic Agent")
    print("=" * 60)
    
    # Create a basic agent
    agent = BaseAgent(
        name="Assistant",
        system_prompt="You are a helpful AI assistant that provides clear and concise answers. Always be polite and professional.",
        model_name="gemini-1.5-flash",
        temperature=0.7,
        max_output_tokens=512
    )
    
    # Have a conversation
    print("\nUser: What is machine learning?")
    response = agent.chat("What is machine learning?")
    print(f"Assistant: {response}\n")
    
    print("User: Can you give me a simple example?")
    response = agent.chat("Can you give me a simple example?")
    print(f"Assistant: {response}\n")
    
    # Show chat history
    print("\n--- Chat History ---")
    print(agent.get_history("text"))
    print()


def example_agent_with_tools():
    """Example 2: Agent with Perplexity search and BrowserUse tools"""
    print("=" * 60)
    print("EXAMPLE 2: Agent with Tool Calling")
    print("=" * 60)
    
    # Create an agent with tools enabled
    research_agent = BaseAgent(
        name="ResearchBot",
        system_prompt="""You are a research assistant that can search the web for real-time information.
        When asked about current events or facts that might change, use the perplexity_search tool.
        When asked to interact with websites, use the browser_use tool.""",
        model_name="gemini-1.5-flash",
        temperature=0.5,
        enable_tools=True,
        auto_execute_tools=True
    )
    
    # Example queries that might trigger tool usage
    queries = [
        "What are the latest developments in AI for 2025?",
        "Can you find information about the current weather in San Francisco?"
    ]
    
    for query in queries:
        print(f"\nUser: {query}")
        response = research_agent.chat(query)
        print(f"ResearchBot: {response[:500]}..." if len(response) > 500 else f"ResearchBot: {response}")
        print()


def example_multi_agent_system():
    """Example 3: Multi-agent communication and collaboration"""
    print("=" * 60)
    print("EXAMPLE 3: Multi-Agent System")
    print("=" * 60)
    
    # Create multiple specialized agents
    analyst = BaseAgent(
        name="DataAnalyst",
        system_prompt="You are a data analyst who provides insights based on data and trends. You focus on quantitative analysis.",
        temperature=0.3  # Lower temperature for more focused responses
    )
    
    strategist = BaseAgent(
        name="Strategist",
        system_prompt="You are a business strategist who develops high-level strategies and evaluates opportunities.",
        temperature=0.7
    )
    
    critic = BaseAgent(
        name="Critic",
        system_prompt="You are a critical thinker who evaluates ideas, identifies potential issues, and suggests improvements.",
        temperature=0.5
    )
    
    # Connect agents for communication
    analyst.connect_agent(strategist)
    analyst.connect_agent(critic)
    strategist.connect_agent(analyst)
    strategist.connect_agent(critic)
    critic.connect_agent(analyst)
    critic.connect_agent(strategist)
    
    # Scenario: Analyzing a business proposal
    print("\n--- Multi-Agent Discussion ---")
    print("\nAnalyst presents data:")
    analyst_insight = "Based on our Q4 data, customer acquisition cost has increased by 35% while retention rates dropped by 12%."
    print(f"DataAnalyst: {analyst_insight}")
    
    # Analyst sends findings to strategist
    print("\n[DataAnalyst → Strategist]")
    strategy_response = analyst.send_to_agent(
        "Strategist",
        analyst_insight + " What strategic adjustments should we consider?"
    )
    print(f"Strategist: {strategy_response[:300]}...")
    
    # Strategist's proposal goes to critic
    print("\n[Strategist → Critic]")
    critic_response = strategist.send_to_agent(
        "Critic",
        f"I propose: {strategy_response[:200]}... Please evaluate this strategy."
    )
    print(f"Critic: {critic_response[:300]}...")
    
    # Broadcast for final thoughts
    print("\n--- Broadcasting for Final Thoughts ---")
    final_responses = analyst.broadcast_to_agents(
        "Based on our discussion, what is your final recommendation for the Q1 strategy?"
    )
    
    for agent_name, response in final_responses.items():
        print(f"\n{agent_name}: {response[:200]}...")


def example_history_management():
    """Example 4: Managing and persisting chat history"""
    print("=" * 60)
    print("EXAMPLE 4: History Management")
    print("=" * 60)
    
    # Create an agent with memory limit
    agent = BaseAgent(
        name="MemoryBot",
        system_prompt="You are an AI that remembers conversations.",
        memory_limit=10  # Keep only last 10 messages
    )
    
    # Have a conversation
    topics = ["Python programming", "Machine learning", "Web development", "Data science"]
    
    for i, topic in enumerate(topics, 1):
        print(f"\nConversation {i} about {topic}:")
        response = agent.chat(f"Tell me one interesting fact about {topic}")
        print(f"Response: {response[:150]}...")
    
    # Save history
    history_file = "conversation_history.json"
    agent.save_history(history_file)
    print(f"\n✓ History saved to {history_file}")
    
    # Create new agent and load history
    new_agent = BaseAgent(name="RestoredBot")
    new_agent.load_history(history_file)
    print(f"✓ History loaded into new agent")
    
    # Verify history was loaded
    print(f"\nLoaded {len(new_agent.chat_history)} messages")
    print("\nContinuing conversation with loaded history:")
    response = new_agent.chat("What topics have we discussed so far?")
    print(f"RestoredBot: {response}")
    
    # Clean up
    if os.path.exists(history_file):
        os.remove(history_file)
        print(f"\n✓ Cleaned up {history_file}")


async def example_async_operations():
    """Example 5: Asynchronous chat operations"""
    print("=" * 60)
    print("EXAMPLE 5: Async Operations")
    print("=" * 60)
    
    # Create multiple agents for parallel processing
    agents = [
        BaseAgent(name=f"AsyncBot{i}", system_prompt=f"You are async bot number {i}.")
        for i in range(1, 4)
    ]
    
    # Questions for parallel processing
    questions = [
        "What is the meaning of life?",
        "Explain quantum computing in simple terms.",
        "What are the benefits of async programming?"
    ]
    
    print("\nSending questions to agents asynchronously...")
    
    # Create tasks for parallel execution
    tasks = []
    for agent, question in zip(agents, questions):
        print(f"- {agent.name} processing: {question[:50]}...")
        task = agent.chat_async(question)
        tasks.append(task)
    
    # Wait for all responses
    responses = await asyncio.gather(*tasks)
    
    print("\n--- Async Responses ---")
    for agent, response in zip(agents, responses):
        print(f"\n{agent.name}: {response[:200]}...")


def example_custom_tools_workflow():
    """Example 6: Advanced workflow with custom tool usage"""
    print("=" * 60)
    print("EXAMPLE 6: Custom Tools Workflow")
    print("=" * 60)
    
    # Create a specialized research and analysis agent
    agent = BaseAgent(
        name="ResearchAnalyst",
        system_prompt="""You are a research analyst who:
        1. Searches for information using perplexity_search
        2. Visits websites for detailed information using browser_use
        3. Provides comprehensive analysis
        
        Always cite your sources and be thorough in your research.""",
        enable_tools=True,
        auto_execute_tools=True,
        temperature=0.3  # More deterministic for research
    )
    
    # Complex research task
    research_task = """
    I need to understand the current state of renewable energy adoption in 2025.
    Please research:
    1. Current global statistics
    2. Leading countries
    3. Most promising technologies
    4. Recent breakthroughs
    """
    
    print(f"\nUser: {research_task}")
    print("\n[Agent conducting research with tools...]")
    
    response = agent.chat(research_task)
    
    print(f"\nResearchAnalyst: {response[:800]}...")
    
    # Show tool usage from history
    print("\n--- Tool Usage Log ---")
    for msg in agent.chat_history:
        if msg.role.value == "tool":
            print(f"• {msg.content[:100]}...")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print(" BaseAgent Examples - Multi-Agent System with Gemini")
    print("=" * 60 + "\n")
    
    # Check for API keys
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  Warning: GEMINI_API_KEY not found in environment variables")
        print("   Please set it in your .env file to run these examples\n")
        return
    
    # Run examples
    try:
        # Basic examples
        example_basic_agent()
        input("\nPress Enter to continue to the next example...")
        
        # Tool usage (requires Perplexity API key)
        if os.getenv("PERPLEXITY_API_KEY"):
            example_agent_with_tools()
            input("\nPress Enter to continue to the next example...")
        else:
            print("\n⚠️  Skipping tool examples - PERPLEXITY_API_KEY not found")
        
        # Multi-agent system
        example_multi_agent_system()
        input("\nPress Enter to continue to the next example...")
        
        # History management
        example_history_management()
        input("\nPress Enter to continue to the next example...")
        
        # Async operations
        print("\nRunning async example...")
        asyncio.run(example_async_operations())
        
        # Advanced workflow (if tools available)
        if os.getenv("PERPLEXITY_API_KEY"):
            input("\nPress Enter to continue to the final example...")
            example_custom_tools_workflow()
        
        print("\n" + "=" * 60)
        print(" All examples completed successfully!")
        print("=" * 60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")


if __name__ == "__main__":
    main()
