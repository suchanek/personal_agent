import asyncio


class OllamaAgent:
    def __init__(
        self,
        model_name,
        temperature=0.7,
        max_tokens=150,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.ollama_instance = self.initialize_ollama()

    def initialize_ollama(self):
        # Initialize the Ollama instance with the specified model
        return Ollama(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
        )

    async def generate_response(self, prompt):
        # Use the Ollama instance to generate a response based on the prompt asynchronously
        response = await self.ollama_instance.generate(prompt)
        return response


# Example usage
async def main():
    agent = OllamaAgent(model_name="gpt-3.5-turbo")
    response = await agent.generate_response("What is the capital of France?")
    print(response)


# Run the async main function
asyncio.run(main())
