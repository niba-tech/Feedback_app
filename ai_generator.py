import json
import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are an expert social media marketing strategist specializing in e-commerce brands.
You create engaging, platform-specific content that drives sales and builds brand awareness.
You always respond with valid JSON matching the schema requested."""


def _build_product_summary(store_data: dict) -> str:
    lines = [
        f"Store: {store_data.get('store_name', 'Unknown')}",
        f"URL: {store_data.get('url', '')}",
        f"Description: {store_data.get('store_description', 'N/A')}",
        f"Categories: {', '.join(store_data.get('categories', [])) or 'Various'}",
        "",
        "PRODUCTS:",
    ]
    for p in store_data.get("products", [])[:40]:
        line = f"- {p['name']}"
        if p.get("price"):
            line += f" | {p['price']}"
        if p.get("category"):
            line += f" | Category: {p['category']}"
        if p.get("description"):
            line += f" | {p['description'][:120]}"
        lines.append(line)
    return "\n".join(lines)


def generate_strategy(store_data: dict, tone: str = "Friendly", language: str = "English") -> dict:
    product_summary = _build_product_summary(store_data)
    store_name = store_data.get("store_name", "the store")

    user_prompt = f"""Analyze this online store and create a complete social media marketing strategy.

STORE DATA:
{product_summary}

REQUIREMENTS:
- Language: {language}
- Brand tone: {tone}
- Store name: {store_name}

Return a JSON object with EXACTLY this structure:
{{
  "brand_overview": {{
    "target_audience": "description of the ideal customer",
    "unique_selling_points": ["point 1", "point 2", "point 3"],
    "brand_voice": "how the brand should sound",
    "best_selling_categories": ["category 1", "category 2"]
  }},
  "facebook_strategy": {{
    "posts": [
      {{
        "caption": "full ready-to-post caption with emojis",
        "post_type": "Product showcase / Sale announcement / Story / etc",
        "best_time": "e.g. Tuesday 6-8 PM"
      }}
    ],
    "ad_copy_variants": [
      {{
        "headline": "short punchy headline",
        "body": "ad body text",
        "call_to_action": "Shop Now / Learn More / etc"
      }}
    ],
    "page_tips": ["tip 1", "tip 2", "tip 3"]
  }},
  "instagram_strategy": {{
    "posts": [
      {{
        "caption": "full caption with emojis",
        "post_type": "Feed / Reel / Story / Carousel",
        "visual_suggestion": "what the image or video should show"
      }}
    ],
    "hashtag_groups": {{
      "niche": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
      "medium": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
      "broad": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"]
    }},
    "reel_ideas": ["idea 1", "idea 2", "idea 3"],
    "story_ideas": ["idea 1", "idea 2", "idea 3"]
  }},
  "content_calendar": [
    {{
      "day": "Monday",
      "facebook": "what to post",
      "instagram": "what to post",
      "theme": "weekly theme or campaign"
    }}
  ],
  "campaigns": [
    {{
      "name": "Campaign name",
      "description": "what the campaign is about",
      "duration": "e.g. 3 days",
      "facebook_angle": "how to run it on Facebook",
      "instagram_angle": "how to run it on Instagram",
      "expected_outcome": "what result to expect"
    }}
  ],
  "posting_tips": {{
    "facebook": ["tip 1", "tip 2", "tip 3", "tip 4"],
    "instagram": ["tip 1", "tip 2", "tip 3", "tip 4"],
    "general": ["tip 1", "tip 2", "tip 3"]
  }}
}}

Generate:
- 10 Facebook posts (varied types)
- 5 Facebook ad copy variants
- 10 Instagram posts (mix of Feed, Reel, Story, Carousel)
- 30 hashtags total (10 per group: niche, medium, broad)
- 3 Reel ideas and 3 Story ideas
- 7 days in the content calendar (Monday through Sunday)
- 3 promotional campaigns
- 4+ tips per platform

Make all captions ready to copy-paste. Write in {language}."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rsplit("```", 1)[0].strip()

    return json.loads(raw)
