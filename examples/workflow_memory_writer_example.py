"""
Example: Memory-Based Writing Workflow using Agno Workflow

This example demonstrates how to use the Agno Workflow object to create a
memory-based writing system that properly coordinates between memory retrieval
and content creation.

The workflow ensures that when writing content "based on memories", it:
1. First retrieves relevant memories
2. Then creates content using those actual memories
3. Maintains session state and memory persistence

Author: Personal Agent Team
"""

import asyncio
from typing import Iterator, Optional

from agno.agent import Agent
from agno.memory import Memory
from agno.run.response import RunResponse
from agno.workflow import Workflow

# Import personal agent components
try:
    from personal_agent.config.settings import LLM_MODEL, OLLAMA_URL
    from personal_agent.config.user_id_mgr import get_userid
    from personal_agent.core.agent_model_manager import AgentModelManager
    from personal_agent.core.agno_agent import AgnoPersonalAgent
except ImportError:
    print("Warning: Personal agent components not found. Using defaults.")
    LLM_MODEL = "llama3.1:8b"
    OLLAMA_URL = "http://localhost:11434"

    def get_userid():
        return "grok"


class MemoryBasedWritingWorkflow(Workflow):
    """
    A workflow that demonstrates proper memory-to-writer coordination.

    This workflow:
    1. Retrieves user memories using a memory agent
    2. Creates personalized content using a writer agent
    3. Maintains session state and memory persistence
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="Memory-Based Writing Workflow",
            description="Creates personalized content based on user memories",
            **kwargs,
        )

        # Initialize agents (will be set up in run method)
        self.memory_agent: Optional[Agent] = None
        self.writer_agent: Optional[Agent] = None

    async def setup_agents(self):
        """Set up the memory and writer agents."""
        user_id = get_userid()

        # Create memory agent using AgnoPersonalAgent
        try:
            self.memory_agent = AgnoPersonalAgent(
                model_provider="ollama",
                model_name=LLM_MODEL,
                enable_memory=True,
                enable_mcp=False,
                debug=True,
                user_id=user_id,
                recreate=False,
                alltools=False,
                ollama_base_url=OLLAMA_URL,
            )
            await self.memory_agent._ensure_initialized()
        except Exception as e:
            print(f"Warning: Could not create AgnoPersonalAgent: {e}")
            # Fallback to basic agent
            model_manager = AgentModelManager(
                model_provider="ollama",
                model_name=LLM_MODEL,
                ollama_base_url=OLLAMA_URL,
            )
            model = model_manager.create_model()

            self.memory_agent = Agent(
                name="Memory Agent",
                model=model,
                memory=Memory(),
                instructions=[
                    "You are a memory agent that stores and retrieves user information.",
                    "When asked about memories, provide detailed information about the user.",
                ],
            )

        # Create writer agent
        model_manager = AgentModelManager(
            model_provider="ollama",
            model_name=LLM_MODEL,
            ollama_base_url=OLLAMA_URL,
        )
        writer_model = model_manager.create_model()

        self.writer_agent = Agent(
            name="Writer Agent",
            model=writer_model,
            instructions=[
                "You are a versatile writer who creates engaging content.",
                "When provided with memories or personal information, use them to create personalized content.",
                "Write in a natural, engaging tone while being factually accurate.",
                "If no memories are provided, create generic content.",
            ],
        )

    def run(
        self,
        content_type: str = "story",
        topic: str = "user's life",
        use_memories: bool = True,
    ) -> RunResponse:
        """
        Main workflow execution (synchronous version).

        Args:
            content_type: Type of content to create (story, poem, article, etc.)
            topic: Topic for the content
            use_memories: Whether to retrieve and use memories

        Returns:
            RunResponse with the created content
        """

        # For sync version, we'll create a simple response
        # In a real implementation, you'd use sync agents or run async code differently
        final_content = f"""# {content_type.title()} about {topic}

This is a demonstration of the Agno Workflow pattern.
In a full implementation, this would:

1. Retrieve user memories using the memory agent
2. Create personalized content using the writer agent
3. Return the generated content

Content type: {content_type}
Topic: {topic}
Use memories: {use_memories}

---
*This is a demo response showing the workflow structure*
"""

        return RunResponse(
            content=final_content,
            session_id=self.session_id,
            workflow_id=self.workflow_id,
        )

    async def arun(
        self,
        content_type: str = "story",
        topic: str = "user's life",
        use_memories: bool = True,
    ) -> RunResponse:
        """
        Async workflow execution.

        Args:
            content_type: Type of content to create (story, poem, article, etc.)
            topic: Topic for the content
            use_memories: Whether to retrieve and use memories

        Returns:
            RunResponse with the created content
        """

        # Setup agents
        await self.setup_agents()

        memories_content = ""

        if use_memories and self.memory_agent:
            # Step 1: Retrieve memories
            print("🧠 Retrieving user memories...")

            try:
                # Try to get memories using the memory agent
                memory_response = await self.memory_agent.arun(
                    "What do you remember about the user? List all memories."
                )
                memories_content = (
                    memory_response.content
                    if memory_response.content
                    else "No memories found."
                )
                print(f"📝 Retrieved memories: {len(memories_content)} characters")
            except Exception as e:
                print(f"⚠️ Could not retrieve memories: {e}")
                memories_content = "No memories available."

        # Step 2: Create content using memories
        print(f"✍️ Creating {content_type} about {topic}...")

        if (
            use_memories
            and memories_content
            and memories_content != "No memories available."
        ):
            # Create personalized content using memories
            writing_prompt = f"""Write a {content_type} about {topic} using these memories about the user:

{memories_content}

Make the {content_type} personal and engaging, incorporating the specific details from the memories."""
        else:
            # Create generic content
            writing_prompt = f"Write a {content_type} about {topic}."

        try:
            writer_response = await self.writer_agent.arun(writing_prompt)
            content = (
                writer_response.content
                if writer_response.content
                else f"Could not create {content_type}."
            )
        except Exception as e:
            print(f"⚠️ Could not create content: {e}")
            content = f"Error creating {content_type}: {str(e)}"

        # Create the final response
        final_content = f"""# {content_type.title()} about {topic}

{content}

---
*Created using {'user memories' if use_memories and memories_content != 'No memories available.' else 'generic content'}*
"""

        return RunResponse(
            content=final_content,
            session_id=self.session_id,
            workflow_id=self.workflow_id,
        )


class StreamingMemoryWritingWorkflow(Workflow):
    """
    A streaming version of the memory-based writing workflow.

    This demonstrates how to create a workflow that yields intermediate results
    as it progresses through the memory retrieval and writing steps.
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="Streaming Memory Writing Workflow",
            description="Creates personalized content with streaming updates",
            **kwargs,
        )

        self.memory_agent: Optional[Agent] = None
        self.writer_agent: Optional[Agent] = None

    async def setup_agents(self):
        """Set up the memory and writer agents."""
        user_id = get_userid()

        # Create memory agent
        try:
            self.memory_agent = AgnoPersonalAgent(
                model_provider="ollama",
                model_name=LLM_MODEL,
                enable_memory=True,
                enable_mcp=False,
                debug=True,
                user_id=user_id,
                recreate=False,
                alltools=False,
                ollama_base_url=OLLAMA_URL,
            )
            await self.memory_agent._ensure_initialized()
        except Exception as e:
            print(f"Warning: Could not create AgnoPersonalAgent: {e}")
            # Fallback to basic agent
            model_manager = AgentModelManager(
                model_provider="ollama",
                model_name=LLM_MODEL,
                ollama_base_url=OLLAMA_URL,
            )
            model = model_manager.create_model()

            self.memory_agent = Agent(
                name="Memory Agent",
                model=model,
                memory=Memory(),
                instructions=[
                    "You are a memory agent that stores and retrieves user information.",
                ],
            )

        # Create writer agent
        model_manager = AgentModelManager(
            model_provider="ollama",
            model_name=LLM_MODEL,
            ollama_base_url=OLLAMA_URL,
        )
        writer_model = model_manager.create_model()

        self.writer_agent = Agent(
            name="Writer Agent",
            model=writer_model,
            instructions=[
                "You are a versatile writer who creates engaging content.",
                "When provided with memories, use them to create personalized content.",
            ],
        )

    async def arun(
        self,
        content_type: str = "story",
        topic: str = "user's life",
        use_memories: bool = True,
    ) -> Iterator[RunResponse]:
        """
        Streaming workflow execution that yields progress updates.

        Args:
            content_type: Type of content to create
            topic: Topic for the content
            use_memories: Whether to retrieve and use memories

        Yields:
            RunResponse objects with progress updates
        """

        # Setup agents
        await self.setup_agents()

        # Yield initial status
        yield RunResponse(
            content="🚀 Starting memory-based writing workflow...\n",
            session_id=self.session_id,
            workflow_id=self.workflow_id,
        )

        memories_content = ""

        if use_memories and self.memory_agent:
            # Step 1: Retrieve memories
            yield RunResponse(
                content="🧠 Retrieving user memories...\n",
                session_id=self.session_id,
                workflow_id=self.workflow_id,
            )

            try:
                memory_response = await self.memory_agent.arun(
                    "What do you remember about the user? List all memories."
                )
                memories_content = (
                    memory_response.content
                    if memory_response.content
                    else "No memories found."
                )

                yield RunResponse(
                    content=f"📝 Retrieved {len(memories_content)} characters of memories\n",
                    session_id=self.session_id,
                    workflow_id=self.workflow_id,
                )
            except Exception as e:
                yield RunResponse(
                    content=f"⚠️ Could not retrieve memories: {e}\n",
                    session_id=self.session_id,
                    workflow_id=self.workflow_id,
                )
                memories_content = "No memories available."

        # Step 2: Create content
        yield RunResponse(
            content=f"✍️ Creating {content_type} about {topic}...\n",
            session_id=self.session_id,
            workflow_id=self.workflow_id,
        )

        if (
            use_memories
            and memories_content
            and memories_content != "No memories available."
        ):
            writing_prompt = f"""Write a {content_type} about {topic} using these memories:

{memories_content}

Make it personal and engaging."""
        else:
            writing_prompt = f"Write a {content_type} about {topic}."

        try:
            writer_response = await self.writer_agent.arun(writing_prompt)
            content = (
                writer_response.content
                if writer_response.content
                else f"Could not create {content_type}."
            )
        except Exception as e:
            content = f"Error creating {content_type}: {str(e)}"

        # Yield final result
        final_content = f"""# {content_type.title()} about {topic}

{content}

---
*Created using {'user memories' if use_memories and memories_content != 'No memories available.' else 'generic content'}*
"""

        yield RunResponse(
            content=final_content,
            session_id=self.session_id,
            workflow_id=self.workflow_id,
        )


async def demo_basic_workflow():
    """Demonstrate the basic memory-based writing workflow."""
    print("=" * 60)
    print("🔥 DEMO: Basic Memory-Based Writing Workflow")
    print("=" * 60)

    # Create and run the workflow
    workflow = MemoryBasedWritingWorkflow(user_id=get_userid(), debug_mode=True)

    # Run the workflow using the sync method (which is what Agno expects)
    response = workflow.run(
        content_type="story", topic="my life experiences", use_memories=True
    )

    print("\n📖 Generated Content:")
    print("-" * 40)
    print(response.content)
    print("-" * 40)


async def demo_streaming_workflow():
    """Demonstrate the streaming memory-based writing workflow."""
    print("\n" + "=" * 60)
    print("🌊 DEMO: Streaming Memory-Based Writing Workflow")
    print("=" * 60)

    # Create the streaming workflow
    workflow = StreamingMemoryWritingWorkflow(user_id=get_userid(), debug_mode=True)

    # Run the streaming workflow
    print("\n🔄 Streaming Progress:")
    print("-" * 40)

    async for response in workflow.arun(
        content_type="poem", topic="my journey", use_memories=True
    ):
        print(response.content, end="")

    print("-" * 40)


async def demo_comparison():
    """Demonstrate the difference between memory-based and generic content."""
    print("\n" + "=" * 60)
    print("🔍 DEMO: Memory-Based vs Generic Content Comparison")
    print("=" * 60)

    workflow = MemoryBasedWritingWorkflow(user_id=get_userid(), debug_mode=True)

    # Create content with memories
    print("\n1️⃣ Creating content WITH memories:")
    memory_response = workflow.run(
        content_type="short story", topic="a day in my life", use_memories=True
    )

    print("📖 Memory-based content:")
    print("-" * 30)
    print(
        memory_response.content[:500] + "..."
        if len(memory_response.content) > 500
        else memory_response.content
    )
    print("-" * 30)

    # Create content without memories
    print("\n2️⃣ Creating content WITHOUT memories:")
    generic_response = workflow.run(
        content_type="short story", topic="a day in my life", use_memories=False
    )

    print("📖 Generic content:")
    print("-" * 30)
    print(
        generic_response.content[:500] + "..."
        if len(generic_response.content) > 500
        else generic_response.content
    )
    print("-" * 30)


async def main():
    """Run all workflow demonstrations."""
    print("🚀 Agno Workflow Memory-Based Writing Examples")
    print("=" * 60)
    print("This example demonstrates how to use Agno Workflow objects")
    print("to create a proper memory-to-writer coordination system.")
    print("=" * 60)

    try:
        # Run basic workflow demo
        await demo_basic_workflow()

        # Run streaming workflow demo
        await demo_streaming_workflow()

        # Run comparison demo
        # await demo_comparison()

        print("\n" + "=" * 60)
        print("✅ All workflow demonstrations completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error running workflow demos: {e}")
        print("Make sure Ollama is running and the required models are available.")


if __name__ == "__main__":
    # Run the demonstrations
    asyncio.run(main())
