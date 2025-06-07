import asyncio

import nest_asyncio
import streamlit as st
from agno.team import Team
from agno.utils.log import logger
from css import CUSTOM_CSS
from uagi import UAgIConfig, create_uagi, uagi_memory
from utils import (
    about_agno,
    add_message,
    display_tool_calls,
    example_inputs,
    initialize_session_state,
    knowledge_widget,
    selected_agents,
    selected_model,
    selected_tools,
    session_selector,
    show_user_memories,
    utilities_widget,
)

nest_asyncio.apply()
st.set_page_config(
    page_title="UAgI",
    page_icon="💎",
    layout="wide",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


async def header():
    st.markdown(
        "<h1 class='heading'>Universal Agent Interface</h1>", unsafe_allow_html=True
    )
    st.markdown(
        "<p class='subheading'>A Universal Interface for orchestrating multiple Agents</p>",
        unsafe_allow_html=True,
    )


async def body() -> None:
    ####################################################################
    # Initialize User and Session State
    ####################################################################
    user_id = st.sidebar.text_input(":technologist: User Id", value="Ava")

    ####################################################################
    # Select Model
    ####################################################################
    model_id = await selected_model()

    ####################################################################
    # Select Tools
    ####################################################################
    tools = await selected_tools()

    ####################################################################
    # Select Team Members
    ####################################################################
    agents = await selected_agents()

    ####################################################################
    # Create UAgI
    ####################################################################
    uagi_config = UAgIConfig(
        user_id=user_id, model_id=model_id, tools=tools, agents=agents
    )

    # Check if UAgI instance should be recreated
    recreate_uagi = (
        "uagi" not in st.session_state
        or st.session_state.get("uagi") is None
        or st.session_state.get("uagi_config") != uagi_config
    )

    # Create UAgI instance if it doesn't exist or configuration has changed
    uagi: Team
    if recreate_uagi:
        logger.info("---*--- Creating UAgI instance ---*---")
        uagi = create_uagi(uagi_config)
        st.session_state["uagi"] = uagi
        st.session_state["uagi_config"] = uagi_config
        logger.info(f"---*--- UAgI instance created ---*---")
    else:
        uagi = st.session_state["uagi"]
        logger.info(f"---*--- UAgI instance exists ---*---")

    ####################################################################
    # Load Agent Session from the database
    ####################################################################
    try:
        logger.info(f"---*--- Loading UAgI session ---*---")
        st.session_state["session_id"] = uagi.load_session()
    except Exception:
        st.warning("Could not create UAgI session, is the database running?")
        return
    logger.info(f"---*--- UAgI session: {st.session_state.get('session_id')} ---*---")

    ####################################################################
    # Load agent runs (i.e. chat history) from memory if messages is not empty
    ####################################################################
    chat_history = uagi.get_messages_for_session()
    if len(chat_history) > 0:
        logger.info("Loading messages")
        # Clear existing messages
        st.session_state["messages"] = []
        # Loop through the runs and add the messages to the messages list
        for message in chat_history:
            if message.role == "user":
                await add_message(message.role, str(message.content))
            if message.role == "assistant":
                await add_message("assistant", str(message.content), message.tool_calls)

    ####################################################################
    # Get user input
    ####################################################################
    if prompt := st.chat_input("✨ How can I help, bestie?"):
        await add_message("user", prompt)

    ####################################################################
    # Show example inputs
    ####################################################################
    await example_inputs()

    ####################################################################
    # Show user memories
    ####################################################################
    await show_user_memories(uagi_memory, user_id)

    ####################################################################
    # Display agent messages
    ####################################################################
    for message in st.session_state["messages"]:
        if message["role"] in ["user", "assistant"]:
            _content = message["content"]
            if _content is not None:
                with st.chat_message(message["role"]):
                    # Display tool calls if they exist in the message
                    if "tool_calls" in message and message["tool_calls"]:
                        display_tool_calls(st.empty(), message["tool_calls"])
                    st.markdown(_content)

    ####################################################################
    # Generate response for user message
    ####################################################################
    last_message = (
        st.session_state["messages"][-1] if st.session_state["messages"] else None
    )
    if last_message and last_message.get("role") == "user":
        user_message = last_message["content"]
        logger.info(f"Responding to message: {user_message}")
        with st.chat_message("assistant"):
            # Create container for tool calls
            tool_calls_container = st.empty()
            resp_container = st.empty()
            with st.spinner(":thinking_face: Thinking..."):
                response = ""
                try:
                    # Run the agent and stream the response
                    run_response = await uagi.arun(
                        user_message, stream=True, stream_intermediate_steps=True
                    )
                    # Create a status container for real-time updates
                    status_container = st.empty()

                    # Collect tool results from the stream
                    tool_results_map = {}
                    all_tool_calls = []

                    async for resp_chunk in run_response:
                        # DIAGNOSTIC: Log the chunk structure
                        print(f"\n🔍 CHUNK DEBUG:")
                        print(f"   Type: {type(resp_chunk)}")
                        print(
                            f"   Dir: {[attr for attr in dir(resp_chunk) if not attr.startswith('_')]}"
                        )

                        if hasattr(resp_chunk, "event"):
                            print(f"   Event: {resp_chunk.event}")

                        if hasattr(resp_chunk, "tools") and resp_chunk.tools:
                            print(f"   Tools count: {len(resp_chunk.tools)}")
                            for i, tool in enumerate(resp_chunk.tools):
                                print(f"     Tool {i}:")
                                print(f"       Type: {type(tool)}")
                                print(
                                    f"       Dir: {[attr for attr in dir(tool) if not attr.startswith('_')]}"
                                )
                                if hasattr(tool, "name"):
                                    print(f"       Name: {tool.name}")
                                if hasattr(tool, "id"):
                                    print(f"       ID: {tool.id}")
                                if hasattr(tool, "result"):
                                    print(f"       Result: {repr(tool.result)}")
                                if hasattr(tool, "content"):
                                    print(f"       Content: {repr(tool.content)}")

                        if hasattr(resp_chunk, "messages") and resp_chunk.messages:
                            print(f"   Messages count: {len(resp_chunk.messages)}")
                            for i, msg in enumerate(resp_chunk.messages):
                                print(f"     Message {i}:")
                                print(f"       Type: {type(msg)}")
                                print(f"       Role: {getattr(msg, 'role', 'N/A')}")
                                print(
                                    f"       Content: {repr(getattr(msg, 'content', 'N/A'))}"
                                )
                                print(
                                    f"       Tool Call ID: {getattr(msg, 'tool_call_id', 'N/A')}"
                                )

                        # Show real-time status updates for all events
                        if hasattr(resp_chunk, "event") and resp_chunk.event:
                            event_name = resp_chunk.event

                            # Display status based on event type
                            if event_name == "run_started":
                                with status_container.container():
                                    st.info("🚀 Starting to process your request...")
                            elif event_name == "tool_call_started":
                                with status_container.container():
                                    st.info(
                                        "🔧 Using tools to help with your request..."
                                    )
                            elif event_name == "reasoning_started":
                                with status_container.container():
                                    st.info("🧠 Thinking through the problem...")
                            elif event_name == "reasoning_step":
                                if (
                                    hasattr(resp_chunk, "content")
                                    and resp_chunk.content
                                ):
                                    with status_container.container():
                                        st.info(f"💭 {resp_chunk.content}")
                            elif event_name == "tool_call_completed":
                                with status_container.container():
                                    st.info("✅ Tool execution completed")

                                # Display raw tool results immediately
                                if hasattr(resp_chunk, "tools") and resp_chunk.tools:
                                    for tool in resp_chunk.tools:
                                        tool_name = getattr(
                                            tool, "name", "Unknown Tool"
                                        )
                                        tool_result = getattr(
                                            tool, "result", None
                                        ) or getattr(tool, "content", None)

                                        if tool_result:
                                            with st.expander(
                                                f"🔧 {tool_name} - Raw Output",
                                                expanded=True,
                                            ):
                                                st.text(str(tool_result))

                        # Collect tool results from messages with role='tool'
                        if hasattr(resp_chunk, "messages") and resp_chunk.messages:
                            for message in resp_chunk.messages:
                                if hasattr(message, "role") and message.role == "tool":
                                    if hasattr(message, "tool_call_id") and hasattr(
                                        message, "content"
                                    ):
                                        tool_results_map[message.tool_call_id] = (
                                            message.content
                                        )

                                        # Also display raw tool results immediately from messages
                                        with st.expander(
                                            f"🔧 Tool Result (ID: {message.tool_call_id}) - Raw Output",
                                            expanded=True,
                                        ):
                                            st.text(str(message.content))

                        # Display tool calls if available and update with results
                        if resp_chunk.tools and len(resp_chunk.tools) > 0:
                            # Update tool calls with results if available
                            enhanced_tools = []
                            for tool in resp_chunk.tools:
                                tool_dict = (
                                    tool
                                    if isinstance(tool, dict)
                                    else {
                                        "tool_name": getattr(
                                            tool,
                                            "tool_name",
                                            getattr(tool, "name", "Unknown Tool"),
                                        ),
                                        "tool_args": getattr(
                                            tool,
                                            "tool_args",
                                            getattr(tool, "arguments", {}),
                                        ),
                                        "metrics": getattr(tool, "metrics", None),
                                        "id": getattr(tool, "id", None),
                                    }
                                )

                                # Add result if available
                                tool_id = tool_dict.get("id")
                                if tool_id and tool_id in tool_results_map:
                                    tool_dict["content"] = tool_results_map[tool_id]
                                elif not tool_dict.get("content"):
                                    # Check if the tool object already has content/result
                                    content = getattr(tool, "content", None) or getattr(
                                        tool, "result", None
                                    )
                                    if content:
                                        tool_dict["content"] = content

                                enhanced_tools.append(tool_dict)

                            # Store for final display
                            all_tool_calls = enhanced_tools
                            display_tool_calls(tool_calls_container, enhanced_tools)

                        # Display response content as it streams (for any event with content)
                        if (
                            hasattr(resp_chunk, "content")
                            and resp_chunk.content is not None
                        ):
                            # Only accumulate content for RunResponse events for final response
                            if resp_chunk.event == "RunResponse":
                                response += resp_chunk.content
                                resp_container.markdown(response)
                            else:
                                # For other events with text content, show as intermediate status
                                content = resp_chunk.content
                                if isinstance(content, str) and content.strip():
                                    with status_container.container():
                                        st.info(f"💬 {content}")

                    # Clear status when done
                    status_container.empty()

                    # Add the response to the messages with enhanced tool calls
                    if all_tool_calls:
                        await add_message("assistant", response, all_tool_calls)
                    elif uagi.run_response is not None:
                        await add_message(
                            "assistant", response, uagi.run_response.tools
                        )
                    else:
                        await add_message("assistant", response)
                except Exception as e:
                    logger.error(f"Error during agent run: {str(e)}", exc_info=True)
                    error_message = f"Sorry, I encountered an error: {str(e)}"
                    await add_message("assistant", error_message)
                    st.error(error_message)

    ####################################################################
    # Knowledge widget
    ####################################################################
    await knowledge_widget(uagi)

    ####################################################################
    # Session selector
    ####################################################################
    await session_selector(uagi, uagi_config)

    ####################################################################
    # About section
    ####################################################################
    await utilities_widget(uagi)


async def main():
    await initialize_session_state()
    await header()
    await body()
    await about_agno()


if __name__ == "__main__":
    asyncio.run(main())
