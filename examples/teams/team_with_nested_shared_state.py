from agno.agent.agent import Agent
from agno.models.openai.chat import OpenAIChat
from agno.team import Team


# Define tools to manage our shopping list
def add_item(agent: Agent, item: str) -> str:
    """Add an item to the shopping list and return confirmation.

    Args:
        item (str): The item to add to the shopping list.
    """
    # Add the item if it's not already in the list
    if item.lower() not in [
        i.lower() for i in agent.team_session_state["shopping_list"]
    ]:
        agent.team_session_state["shopping_list"].append(item)
        return f"Added '{item}' to the shopping list"
    else:
        return f"'{item}' is already in the shopping list"


def remove_item(agent: Agent, item: str) -> str:
    """Remove an item from the shopping list by name.

    Args:
        item (str): The item to remove from the shopping list.
    """
    # Case-insensitive search
    for i, list_item in enumerate(agent.team_session_state["shopping_list"]):
        if list_item.lower() == item.lower():
            agent.team_session_state["shopping_list"].pop(i)
            return f"Removed '{list_item}' from the shopping list"

    return f"'{item}' was not found in the shopping list. Current shopping list: {agent.team_session_state['shopping_list']}"


def remove_all_items(agent: Agent) -> str:
    """Remove all items from the shopping list."""
    agent.team_session_state["shopping_list"] = []
    return "All items removed from the shopping list"


shopping_list_agent = Agent(
    name="Shopping List Agent",
    role="Manage the shopping list",
    agent_id="shopping_list_manager",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[add_item, remove_item, remove_all_items],
    instructions=[
        "Manage the shopping list by adding and removing items",
        "Always confirm when items are added or removed",
        "If the task is done, update the session state to log the changes & chores you've performed",
    ],
)


# Shopping management team - new layer for handling all shopping list modifications
shopping_mgmt_team = Team(
    name="Shopping Management Team",
    team_id="shopping_management",
    mode="coordinate",
    model=OpenAIChat(id="gpt-4o-mini"),
    show_tool_calls=True,
    members=[shopping_list_agent],
    instructions=[
        "Manage adding and removing items from the shopping list using the Shopping List Agent",
        "Forward requests to add or remove items to the Shopping List Agent",
    ],
)


def get_ingredients(agent: Agent) -> str:
    """Retrieve ingredients from the shopping list to use for recipe suggestions.

    Args:
        meal_type (str): Type of meal to suggest (breakfast, lunch, dinner, snack, or any)
    """
    shopping_list = agent.team_session_state["shopping_list"]

    if not shopping_list:
        return "The shopping list is empty. Add some ingredients first to get recipe suggestions."

    # Just return the ingredients - the agent will create recipes
    return f"Available ingredients from shopping list: {', '.join(shopping_list)}"


recipe_agent = Agent(
    name="Recipe Suggester",
    agent_id="recipe_suggester",
    role="Suggest recipes based on available ingredients",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[get_ingredients],
    instructions=[
        "First, use the get_ingredients tool to get the current ingredients from the shopping list",
        "After getting the ingredients, create detailed recipe suggestions based on those ingredients",
        "Create at least 3 different recipe ideas using the available ingredients",
        "For each recipe, include: name, ingredients needed (highlighting which ones are from the shopping list), and brief preparation steps",
        "Be creative but practical with recipe suggestions",
        "Consider common pantry items that people usually have available in addition to shopping list items",
        "Consider dietary preferences if mentioned by the user",
        "If no meal type is specified, suggest a variety of options (breakfast, lunch, dinner, snacks)",
    ],
)


def list_items(team: Team) -> str:
    """List all items in the shopping list."""
    shopping_list = team.team_session_state["shopping_list"]

    if not shopping_list:
        return "The shopping list is empty."

    items_text = "\n".join([f"- {item}" for item in shopping_list])
    return f"Current shopping list:\n{items_text}"


# Create meal planning subteam
meal_planning_team = Team(
    name="Meal Planning Team",
    team_id="meal_planning",
    mode="coordinate",
    model=OpenAIChat(id="gpt-4o-mini"),
    members=[recipe_agent],
    instructions=[
        "You are a meal planning team that suggests recipes based on shopping list items.",
        "IMPORTANT: When users ask 'What can I make with these ingredients?' or any recipe-related questions, IMMEDIATELY forward the EXACT SAME request to the recipe_agent WITHOUT asking for further information.",
        "DO NOT ask the user for ingredients - the recipe_agent will work with what's already in the shopping list.",
        "Your primary job is to forward recipe requests directly to the recipe_agent without modification.",
    ],
)


def add_chore(team: Team, chore: str, priority: str = "medium") -> str:
    """Add a chore to the list with priority level.

    Args:
        chore (str): The chore to add to the list
        priority (str): Priority level of the chore (low, medium, high)

    Returns:
        str: Confirmation message
    """
    # Initialize chores list if it doesn't exist
    if "chores" not in team.session_state:
        team.session_state["chores"] = []

    # Validate priority
    valid_priorities = ["low", "medium", "high"]
    if priority.lower() not in valid_priorities:
        priority = "medium"  # Default to medium if invalid

    # Add the chore with timestamp and priority
    from datetime import datetime

    chore_entry = {
        "description": chore,
        "priority": priority.lower(),
        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    team.session_state["chores"].append(chore_entry)

    return f"Added chore: '{chore}' with {priority} priority"


shopping_team = Team(
    name="Shopping List Team",
    mode="coordinate",
    model=OpenAIChat(id="gpt-4o-mini"),
    team_session_state={"shopping_list": []},
    tools=[list_items, add_chore],
    session_state={"chores": []},
    team_id="shopping_list_team",
    members=[
        shopping_mgmt_team,
        meal_planning_team,
    ],
    show_tool_calls=True,
    markdown=True,
    instructions=[
        "You are a team that manages a shopping list & helps plan meals using that list.",
        "If you need to add or remove items from the shopping list, forward the full request to the Shopping Management Team.",
        "IMPORTANT: If the user asks about recipes or what they can make with ingredients, IMMEDIATELY forward the EXACT request to the meal_planning_team with NO additional questions.",
        "Example: When user asks 'What can I make with these ingredients?', you should simply forward this exact request to meal_planning_team without asking for more information.",
        "If you need to list the items in the shopping list, use the list_items tool.",
        "If the user got something from the shopping list, it means it can be removed from the shopping list.",
        "After each completed task, use the add_chore tool to log exactly what was done with high priority.",
    ],
    show_members_responses=True,
)

# Example usage
shopping_team.print_response(
    "Add milk, eggs, and bread to the shopping list", stream=True
)
print(f"Session state: {shopping_team.team_session_state}")

shopping_team.print_response("I got bread", stream=True)
print(f"Session state: {shopping_team.team_session_state}")

shopping_team.print_response("I need apples and oranges", stream=True)
print(f"Session state: {shopping_team.team_session_state}")

shopping_team.print_response("whats on my list?", stream=True)
print(f"Session state: {shopping_team.team_session_state}")

# Try the meal planning feature
shopping_team.print_response("What can I make with these ingredients?", stream=True)
print(f"Session state: {shopping_team.team_session_state}")

shopping_team.print_response(
    "Clear everything from my list and start over with just bananas and yogurt",
    stream=True,
)
print(f"Shared Session state: {shopping_team.team_session_state}")


print(f"Team session state: {shopping_team.session_state}")
