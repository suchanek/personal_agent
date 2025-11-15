"""Test smolagents docstring format."""

from smolagents import tool


@tool
def test_tool(param1: str, param2: int = 5) -> str:
    """
    This is a test tool.

    Args:
        param1: First parameter description
        param2: Second parameter description (default 5)

    Returns:
        str: A test result
    """
    return f"test: {param1}, {param2}"


if __name__ == "__main__":
    print("Tool created successfully")
    print("Tool name:", test_tool.name)
    print("Tool description:", test_tool.description)
