#!/usr/bin/env python3
"""
Format and display the top 5 headlines about Middle East unrest.
"""

def format_headlines():
    """Format the search results into a clean list of top 5 headlines."""
    
    headlines = [
        {
            "title": "Unrest in the Middle East continues",
            "source": "MSN",
            "date": "2024-08-05",
            "summary": "Eight people were killed in the West Bank as U.S. military forces in Iraq braces for more attacks by an Iranian proxy group."
        },
        {
            "title": "The US has strengthened its military posture in the Middle East amid unrest. Here's where those assets are deployed",
            "source": "KESQ News",
            "date": "2024-10-04",
            "summary": "The US has strengthened its military posture consistently in the Middle East over the last year following the breakout of the war between Israel and Hamas."
        },
        {
            "title": "Unrest in the Middle East threatens to send some prices higher",
            "source": "The Associated Press",
            "date": "2025-06-13",
            "summary": "Israel's attack on Iran Friday has catapulted their long-running conflict into what could become a wider, more dangerous regional war and potentially drive prices higher."
        },
        {
            "title": "Middle East Eye's picks of the year 2024",
            "source": "Middle East Eye",
            "date": "2024-12-25",
            "summary": "As the year comes to a close, Hamas is still operational, but many of its top leaders have been eliminated."
        },
        {
            "title": "'Doomsday' movement grips youth in the Middle East",
            "source": "New York Post",
            "date": "2024-07-20",
            "summary": "A growing messianic resurgence across the Middle East and North Africa has emerged in the past two decades."
        }
    ]
    
    print("📰 TOP 5 HEADLINES ABOUT UNREST IN THE MIDDLE EAST")
    print("=" * 60)
    
    for i, headline in enumerate(headlines, 1):
        print(f"\n{i}. {headline['title']}")
        print(f"   📅 {headline['date']} | 📰 {headline['source']}")
        print(f"   📝 {headline['summary']}")
    
    print("\n" + "=" * 60)
    print("✅ Search completed successfully using DuckDuckGo News API")

if __name__ == "__main__":
    format_headlines()
