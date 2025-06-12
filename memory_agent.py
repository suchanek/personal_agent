import json
import os

from ollama import Ollama

from agno import Agent, agentic_memory


class PersistentMemory(agentic_memory.AgenticMemory):
    def __init__(self, filename="memory.json"):
        super().__init__()
        self.filename = filename
        self.load_memory()

    def load_memory(self):
        """Load memory from a JSON file if it exists."""
        if os.path.exists(self.filename):
            with open(self.filename, "r") as file:
                self.data = json.load(file)
        else:
            self.data = {}

    def save_memory(self):
        """Save memory to a JSON file."""
        with open(self.filename, "w") as file:
            json.dump(self.data, file, indent=4)

    def set(self, key, value):
        """Override set method to save memory after setting a value."""
        super().set(key, value)
        self.save_memory()


class MyAgent(Agent):
    def __init__(self):
        super().__init__()
        self.memory = PersistentMemory()  # Initialize persistent memory
        self.model = Ollama(
            "model_name"
        )  # Replace "model_name" with the actual model you want to use

    def set_preference(self, key, value):
        """Store a user preference in memory."""
        self.memory.set(key, value)
        return f"Preference set: {key} = {value}"

    def get_preference(self, key):
        """Retrieve a user preference from memory."""
        value = self.memory.get(key)
        if value is not None:
            return f"Preference for {key}: {value}"
        else:
            return f"No preference found for {key}."

    def remember_task(self, task):
        """Store a task in memory."""
        tasks = self.memory.get("tasks") or []
        tasks.append(task)
        self.memory.set("tasks", tasks)
        return f"Task added: {task}"

    def show_tasks(self):
        """Show all stored tasks."""
        tasks = self.memory.get("tasks") or []
        if tasks:
            return "Your tasks:\n" + "\n".join(f"- {task}" for task in tasks)
        else:
            return "You have no tasks."

    def call_model(self, user_input):
        """Call the Ollama model with user input."""
        response = self.model.generate(
            user_input
        )  # Assuming generate is the method to call the model
        return response

    def handle_user_input(self, user_input):
        """Process user input and interact with the memory tool."""
        if user_input.startswith("set preference"):
            _, key, value = user_input.split(maxsplit=2)
            return self.set_preference(key, value)
        elif user_input.startswith("get preference"):
            _, key = user_input.split(maxsplit=1)
            return self.get_preference(key)
        elif user_input.startswith("add task"):
            _, task = user_input.split(maxsplit=1)
            return self.remember_task(task)
        elif user_input == "show tasks":
            return self.show_tasks()
        else:
            return self.call_model(user_input)


def main():
    agent = MyAgent()

    print("Welcome to the Virtual Assistant! You can interact with the Ollama model.")
    print("Commands:")
    print(" - set preference <key> <value>")
    print(" - get preference <key>")
    print(" - add task <task>")
    print(" - show tasks")
    print(" - <any other input will be sent to the model>")
    print(" - type 'exit' to quit")

    while True:
        user_input = input("\nEnter command: ")
        if user_input.lower() == "exit":
            print("Exiting the Virtual Assistant. Goodbye!")
            break
        response = agent.handle_user_input(user_input)
        print(response)


if __name__ == "__main__":
    main()
