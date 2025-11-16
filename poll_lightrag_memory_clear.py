import time

import requests

LIGHTRAG_STATS_URL = (
    "http://localhost:8001/api/v1/memory/stats"  # Or direct LightRAG endpoint
)
MAX_ATTEMPTS = 5
DELAY_SECONDS = 2


def poll_lightrag_clear():
    for attempt in range(MAX_ATTEMPTS):
        try:
            response = requests.get(LIGHTRAG_STATS_URL, timeout=10)
            if response.ok:
                data = response.json()
                stats = data.get("stats", {})
                lightrag_docs = stats.get("lightrag_total_documents", None)
                print(
                    f"Attempt {attempt+1}: LightRAG documents remaining: {lightrag_docs}"
                )
                if lightrag_docs == 0:
                    print("✅ LightRAG memory fully cleared.")
                    return True
            else:
                print(f"Failed to get stats: {response.text}")
        except Exception as e:
            print(f"Error polling LightRAG: {e}")
        time.sleep(DELAY_SECONDS)
    print("⚠️ LightRAG memory not fully cleared after polling.")
    return False


if __name__ == "__main__":
    poll_lightrag_clear()
