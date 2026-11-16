import json
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()

def ask_haiku(system_prompt, content, max_tokens=2000):
    """Send a request to Haiku and return its answer as a Python dictionary."""
    response = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": content}],
    )

    if response.stop_reason == "max_tokens":
        raise ValueError("Answer was cut off because it was too long. Keep lists and text much shorter.")

    answer = ""
    for block in response.content:
        if block.type == "text":
            answer = block.text

    answer = answer.strip().removeprefix("```json").removesuffix("```").strip()
    return json.loads(answer)

def ask_haiku_with_search(system_prompt, content, max_searches=3, max_tokens=3000):
    """Like ask_haiku, but Haiku can search the web. Also returns the source links."""
    response = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": content}],
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": max_searches}],
    )

    steps = sum(1 for block in response.content if block.type == "server_tool_use")
    usage = getattr(response.usage, "server_tool_use", None)
    searches = getattr(usage, "web_search_requests", 0) if usage else 0
    print(f"Searches made: {searches} (tool steps: {steps})")

    text_parts = []
    sources = []
    for block in response.content:
        if block.type == "text":
            text_parts.append(block.text)
        elif block.type == "web_search_tool_result" and isinstance(block.content, list):
            for result in block.content:
                if result.url not in[s["url"] for s in sources]:
                    sources.append({"title": result.title, "url": result.url})
        elif block.type == "web_search_tool_result":
            print(f"Web search error: {getattr(block.content, 'error_code', block.content)}")
            
    full_text = "".join(text_parts)
    start = full_text.find("{")
    end = full_text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON found in the answer.")

    result = json.loads(full_text[start:end + 1])
    result["sources"] = sources[:10]
    return result