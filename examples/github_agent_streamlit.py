from os import getenv

import nest_asyncio
import streamlit as st
from agno.agent import Agent
from agno.utils.log import logger
from utils import (
    CUSTOM_CSS,
    about_widget,
    add_message,
    display_tool_calls,
    sidebar_widget,
)

nest_asyncio.apply()
st.set_page_config(
    page_title="GitHub Repo Analyzer",
    page_icon="👨‍💻",
    layout="wide",
)

# Load custom CSS with dark mode support
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

from agno.tools.github import GithubTools


def get_github_agent(debug_mode: bool = True) -> Optional[Agent]:
    """
    Args:
        repo_name: Optional repository name ("owner/repo"). If None, agent relies on user query.
        debug_mode: Whether to enable debug mode for tool calls.
    """

    return Agent(
        model=OpenAIChat(id="gpt-4.1"),
        description=dedent(
            """
            You are an expert Code Reviewing Agent specializing in analyzing GitHub repositories,
            with a strong focus on detailed code reviews for Pull Requests.
            Use your tools to answer questions accurately and provide insightful analysis.
        """
        ),
        instructions=dedent(
            f"""\
        **Core Task:** Analyze GitHub repositories and answer user questions based on the available tools and conversation history.

        **Repository Context Management:**
        1.  **Context Persistence:** Once a target repository (owner/repo) is identified (either initially or from a user query like 'analyze owner/repo'), **MAINTAIN THAT CONTEXT** for all subsequent questions in the current conversation unless the user clearly specifies a *different* repository.
        2.  **Determining Context:** If no repository is specified in the *current* user query, **CAREFULLY REVIEW THE CONVERSATION HISTORY** to find the most recently established target repository. Use that repository context.
        3.  **Accuracy:** When extracting a repository name (owner/repo) from the query or history, **BE EXTREMELY CAREFUL WITH SPELLING AND FORMATTING**. Double-check against the user's exact input.
        4.  **Ambiguity:** If no repository context has been established in the conversation history and the current query doesn't specify one, **YOU MUST ASK THE USER** to clarify which repository (using owner/repo format) they are interested in before using tools that require a repository name.

        **How to Answer Questions:**
        *   **Identify Key Information:** Understand the user's goal and the target repository (using the context rules above).
        *   **Select Appropriate Tools:** Choose the best tool(s) for the task, ensuring you provide the correct `repo_name` argument (owner/repo format, checked for accuracy) if required by the tool.
            *   Project Overview: `get_repository`, `get_file_content` (for README.md).
            *   Libraries/Dependencies: `get_file_content` (for requirements.txt, pyproject.toml, etc.), `get_directory_content`, `search_code`.
            *   PRs/Issues: Use relevant PR/issue tools.
            *   List User Repos: `list_repositories` (no repo_name needed).
            *   Search Repos: `search_repositories` (no repo_name needed).
        *   **Execute Tools:** Run the selected tools.
        *   **Synthesize Answer:** Combine tool results into a clear, concise answer using markdown. If a tool fails (e.g., 404 error because the repo name was incorrect), state that you couldn't find the specified repository and suggest checking the name.
        *   **Cite Sources:** Mention specific files (e.g., "According to README.md...").

        **Specific Analysis Areas (Most require a specific repository):**
        *   Issues: Listing, summarizing, searching.
        *   Pull Requests (PRs): Listing, summarizing, searching, getting details/changes.
        *   Code & Files: Searching code, getting file content, listing directory contents.
        *   Repository Stats & Activity: Stars, contributors, recent activity.

        **Code Review Guidelines (Requires repository and PR):**
        *   Fetch Changes: Use `get_pull_request_changes` or `get_pull_request_with_details`.
        *   Analyze Patch: Evaluate based on functionality, best practices, style, clarity, efficiency.
        *   Present Review: Structure clearly, cite lines/code, be constructive.
        """
        ),
        tools=[
            GithubTools(
                get_repository=True,
                search_repositories=True,
                get_pull_request=True,
                get_pull_request_changes=True,
                list_branches=True,
                get_pull_request_count=True,
                get_pull_requests=True,
                get_pull_request_comments=True,
                get_pull_request_with_details=True,
                list_issues=True,
                get_issue=True,
                update_file=True,
                get_file_content=True,
                get_directory_content=True,
                search_code=True,
            ),
        ],
        markdown=True,
        debug_mode=debug_mode,
        add_history_to_messages=True,
    )


def main() -> None:
    #####################################################################
    # App header
    ####################################################################
    st.markdown(
        "<h1 class='main-header'>👨‍💻 GitHub Repo Analyzer</h1>", unsafe_allow_html=True
    )
    st.markdown("Analyze GitHub repositories")

    ####################################################################
    # Initialize Agent
    ####################################################################
    github_agent: Agent
    if (
        "github_agent" not in st.session_state
        or st.session_state["github_agent"] is None
    ):
        logger.info("---*--- Creating new Github agent ---*---")
        github_agent = get_github_agent()
        st.session_state["github_agent"] = github_agent
        st.session_state["messages"] = []
        st.session_state["github_token"] = getenv("GITHUB_ACCESS_TOKEN")
    else:
        github_agent = st.session_state["github_agent"]

    ####################################################################
    # Load Agent Session from the database
    ####################################################################
    try:
        st.session_state["github_agent_session_id"] = github_agent.load_session()
    except Exception:
        st.warning("Could not create Agent session, is the database running?")
        return

    ####################################################################
    # Load runs from memory (v2 Memory) only on initial load
    ####################################################################
    if github_agent.memory is not None and not st.session_state.get("messages"):
        session_id = st.session_state.get("github_agent_session_id")
        # Fetch stored runs for this session
        agent_runs = github_agent.memory.get_runs(session_id)
        if agent_runs:
            logger.debug("Loading run history")
            st.session_state["messages"] = []
            for run_response in agent_runs:
                # Iterate through stored messages in the run
                for msg in run_response.messages or []:
                    if msg.role in ["user", "assistant"] and msg.content is not None:
                        # Include any tool calls attached to this message
                        add_message(
                            msg.role, msg.content, getattr(msg, "tool_calls", None)
                        )
        else:
            logger.debug("No run history found")
            st.session_state["messages"] = []

    ####################################################################
    # Sidebar
    ####################################################################
    sidebar_widget()

    ####################################################################
    # Get user input
    ####################################################################
    if prompt := st.chat_input("👋 Ask me about GitHub repositories!"):
        add_message("user", prompt)

    ####################################################################
    # Display chat history
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
        question = last_message["content"]
        with st.chat_message("assistant"):
            # Create container for tool calls
            tool_calls_container = st.empty()
            resp_container = st.empty()
            with st.spinner("🤔 Thinking..."):
                response = ""
                try:
                    # Run the agent and stream the response
                    run_response = github_agent.run(
                        question, stream=True, stream_intermediate_steps=True
                    )
                    for _resp_chunk in run_response:
                        # Display tool calls if available
                        if hasattr(_resp_chunk, "tool") and _resp_chunk.tool:
                            display_tool_calls(tool_calls_container, [_resp_chunk.tool])

                        # Display response if available and event is RunResponse
                        if (
                            _resp_chunk.event == "RunResponse"
                            and _resp_chunk.content is not None
                        ):
                            response += _resp_chunk.content
                            resp_container.markdown(response)

                    add_message("assistant", response, github_agent.run_response.tools)
                except Exception as e:
                    logger.exception(e)
                    error_message = f"Sorry, I encountered an error: {str(e)}"
                    add_message("assistant", error_message)
                    st.error(error_message)

    ####################################################################
    # About section
    ####################################################################
    about_widget()


if __name__ == "__main__":
    main()
