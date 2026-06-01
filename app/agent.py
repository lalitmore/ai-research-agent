import os
import json
import re
import anthropic

client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """You are a competitive intelligence analyst. Given a company name,
research it thoroughly and return a JSON object with this exact structure.

CRITICAL: Your response must start with { and end with }. Nothing before the opening brace. Nothing after the closing brace.

{
  "summary": "2-3 sentence company overview",
  "founded": "year or unknown",
  "headquarters": "city, country or unknown",
  "industry": "primary industry",
  "business_model": "how they make money",
  "key_products": ["product1", "product2"],
  "key_topics": ["topic1", "topic2", "topic3"],
  "recent_news": [
    {"headline": "...", "date": "...", "significance": "..."}
  ],
  "competitors": ["competitor1", "competitor2"],
  "strengths": ["strength1", "strength2"],
  "risks": ["risk1", "risk2"],
  "sentiment": "positive or neutral or negative",
  "interview_tip": "One insight you would want to mention in a job interview at this company"
}"""


def extract_json(text: str) -> dict | None:
    """Robustly extract JSON from model output."""
    text = text.strip()
    
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Strip markdown fences
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    
    # Find the first { ... } block
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    
    return None


async def run_research_agent(company: str) -> dict:
    """Run multi-step research agent with web search."""
    
    tools = [{"type": "web_search_20250305", "name": "web_search"}]

    messages = [
        {
            "role": "user",
            "content": f"Research this company: {company}\n\nSearch for recent news, business model, products, competitors, and notable events. Then return ONLY the JSON object — start your response with {{ and end with }}.",
        }
    ]

    while True:
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

        tool_uses = [b for b in response.content if b.type == "tool_use"]
        text_blocks = [b for b in response.content if b.type == "text"]

        if response.stop_reason == "end_turn" or not tool_uses:
            for block in text_blocks:
                result = extract_json(block.text)
                if result:
                    return result
            # Fallback
            raw = text_blocks[0].text if text_blocks else ""
            return {
                "summary": raw[:500] if raw else "Research complete.",
                "sentiment": "neutral",
                "key_topics": [],
                "key_products": [],
                "competitors": [],
                "strengths": [],
                "risks": [],
                "recent_news": [],
                "founded": "unknown",
                "headquarters": "unknown",
                "industry": "unknown",
                "business_model": "unknown",
                "interview_tip": ""
            }

        messages.append({"role": "assistant", "content": response.content})
        tool_results = [
            {"type": "tool_result", "tool_use_id": t.id, "content": "Search executed."}
            for t in tool_uses
        ]
        messages.append({"role": "user", "content": tool_results})