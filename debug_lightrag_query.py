import asyncio
import aiohttp
import json

async def test_lightrag_query():
    """Test the LightRAG query to see what's happening."""
    
    # Test query
    query = "test query"
    
    # Parameters as currently sent by the agent
    query_params = {
        "query": query.strip(),
        "mode": "global",
        "response_type": "Multiple Paragraphs", 
        "top_k": 10,
        "only_need_context": False,
        "only_need_prompt": False,
        "stream": False,
    }
    
    url = "http://localhost:9622/query"
    
    print(f"Sending request to: {url}")
    print(f"With parameters: {json.dumps(query_params, indent=2)}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=query_params, timeout=60) as response:
                print(f"Response status: {response.status}")
                print(f"Response headers: {dict(response.headers)}")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"Response type: {type(result)}")
                    print(f"Response content: {json.dumps(result, indent=2)}")
                else:
                    error_text = await response.text()
                    print(f"Error response: {error_text}")
                    
    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    asyncio.run(test_lightrag_query())
