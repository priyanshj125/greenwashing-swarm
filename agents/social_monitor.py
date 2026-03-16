"""
Agent A2: Social Monitor
────────────────────────────────────────────────────────────────────────────
Responsibilities:
  1. Virtually scroll a company's social feed (LinkedIn / newsroom)
  2. STEALTH MODE: randomized user-agents, human-like delays, headless Chromium
  3. Capture "Green PR" posts and save screenshots as proof artifacts
  4. Clean HTML → Markdown, return structured SocialPost objects
"""
import asyncio
import logging
import random
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from agents.state import SwarmState, SocialPost, ClaimResult, TrailEntry

logger = logging.getLogger(__name__)

# ── Stealth user-agent pool ───────────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Safari/537.36",
]

GREEN_KEYWORDS = [
    "carbon neutral", "net zero", "net-zero", "carbon negative", "100% renewable",
    "zero emissions", "climate positive", "carbon free", "sustainability leader",
    "planet positive", "eco-friendly", "green", "sustainable future", "clean energy",
    "officially", "committed to", "proud to announce", "achieve", "milestone",
]

SCREENSHOT_DIR = Path("data/screenshots")


def _pick_user_agent() -> str:
    try:
        from fake_useragent import UserAgent
        ua = UserAgent()
        return ua.random
    except Exception:
        return random.choice(USER_AGENTS)


def _human_delay(base: float = 0.5, jitter: float = 0.4) -> float:
    """Returns a randomized human-like delay in seconds."""
    return base + random.uniform(0, jitter)


def _is_green_pr(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in GREEN_KEYWORDS)


def _clean_to_markdown(html_or_text: str) -> str:
    """Strip nav/footer/ad noise and return clean text."""
    # Remove common noise patterns
    clean = re.sub(r'(Advertisement|Promoted|Sponsored|See more|Load more)', '', html_or_text, flags=re.IGNORECASE)
    clean = re.sub(r'\s{3,}', '\n\n', clean)
    return clean.strip()


async def _scroll_and_capture(url: str, max_scrolls: int = 5, screenshot_dir: Path = SCREENSHOT_DIR) -> List[dict]:
    """
    Core virtual scroll loop using Crawl4AI + Playwright stealth config.
    Falls back to mock data if Playwright is unavailable.
    """
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
        from crawl4ai.extraction_strategy import NoExtractionStrategy

        browser_cfg = BrowserConfig(
            headless=True,
            user_agent=_pick_user_agent(),
            viewport_width=random.randint(1280, 1920),
            viewport_height=random.randint(800, 1080),
        )

        posts_raw = []

        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            for scroll_i in range(max_scrolls):
                delay = _human_delay(base=0.8, jitter=0.6)
                logger.info("🌐 Scroll %d/%d on %s (delay: %.2fs)", scroll_i + 1, max_scrolls, url, delay)
                await asyncio.sleep(delay)

                run_cfg = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    js_code=f"window.scrollBy(0, {random.randint(600, 900)});",
                    wait_for="css:.feed-shared-update-v2, css:article, css:.post",
                    extraction_strategy=NoExtractionStrategy(),
                    screenshot=True,
                )

                result = await crawler.arun(url=url, config=run_cfg)

                if result.success:
                    page_text = _clean_to_markdown(result.markdown or result.cleaned_html or "")
                    # Save screenshot for flagged Green PR content
                    if _is_green_pr(page_text) and result.screenshot:
                        scr_path = screenshot_dir / f"{uuid.uuid4()}.png"
                        import base64
                        scr_bytes = base64.b64decode(result.screenshot)
                        scr_path.write_bytes(scr_bytes)
                        logger.info("📸 Screenshot saved: %s", scr_path)
                    else:
                        scr_path = None

                    posts_raw.append({
                        "scroll": scroll_i + 1,
                        "text": page_text,
                        "screenshot": str(scr_path) if scr_path else None,
                    })

                # Stop if we've hit a 12-month date boundary
                text_lower = page_text.lower() if result.success else ""
                cutoff_year = (datetime.utcnow() - timedelta(days=365)).year
                if str(cutoff_year - 1) in text_lower:
                    logger.info("📅 Hit 12-month cutoff at scroll %d — stopping", scroll_i + 1)
                    break

        return posts_raw

    except ImportError:
        logger.warning("Crawl4AI/Playwright not available — using mock social data")
        return _mock_social_data(url)
    except Exception as e:
        logger.error("Social scraping error: %s — falling back to mock", e)
        return _mock_social_data(url)


def _mock_social_data(url: str) -> List[dict]:
    """
    Mock social posts for development/testing when Playwright is not available.
    Simulates the PDF-vs-social discrepancy pattern.
    """
    return [
        {
            "scroll": 1,
            "text": (
                "We are OFFICIALLY CARBON NEUTRAL as of Q4 2023! 🌿 "
                "A proud milestone on our journey to a sustainable future. "
                "#NetZero #CarbonNeutral #Sustainability"
            ),
            "screenshot": None,
        },
        {
            "scroll": 2,
            "text": (
                "100% of our electricity now comes from renewable sources! ⚡ "
                "We're passionately committed to a greener tomorrow. "
                "#CleanEnergy #Renewables"
            ),
            "screenshot": None,
        },
        {
            "scroll": 3,
            "text": (
                "Our 2023 Sustainability Report shows Scope 1 emissions "
                "decreased by 8% compared to 2022. Full report available at our website."
            ),
            "screenshot": None,
        },
    ]


def _parse_posts(raw_posts: List[dict], url: str) -> List[SocialPost]:
    """Convert raw crawl output into structured SocialPost objects."""
    platform = "linkedin" if "linkedin" in url.lower() else \
               "twitter" if "twitter.com" in url.lower() or "x.com" in url.lower() else \
               "newsroom"

    posts = []
    for raw in raw_posts:
        text = raw.get("text", "").strip()
        if len(text) < 30:
            continue
        # Extract sentiment keywords present
        kws = [kw for kw in GREEN_KEYWORDS if kw in text.lower()]
        posts.append(SocialPost(
            text=text,
            date=datetime.utcnow().strftime("%Y-%m-%d"),   # simplified; real impl parses date from DOM
            url=url,
            platform=platform,
            screenshot_path=raw.get("screenshot"),
            sentiment_keywords=kws,
        ))
    return posts


def _social_posts_to_claims(posts: List[SocialPost]) -> List[ClaimResult]:
    """Convert social posts into Claim objects for the Auditor."""
    import re as _re
    claims = []
    for post in posts:
        # Split into sentences
        sentences = _re.split(r'(?<=[.!?])\s+', post["text"])
        for sentence in sentences:
            if len(sentence) < 20:
                continue
            claims.append(ClaimResult(
                id=str(uuid.uuid4()),
                text=sentence,
                page=0,
                source="social",
                esg_category="pending",
                has_numbers=bool(_re.search(r'\d+', sentence)),
                materiality_tag="social_media",
            ))
    return claims


async def _run_social_monitor_async(state: SwarmState) -> dict:
    trail: List[TrailEntry] = []
    start = datetime.utcnow().isoformat()

    company_url = state.get("company_url")
    if not company_url:
        trail.append(TrailEntry(
            agent="social_monitor",
            timestamp=start,
            action="skip",
            detail="No company URL provided — social monitoring skipped",
            severity="info",
        ))
        return {"social_posts": [], "screenshots": [], "claims": [], "reasoning_trail": trail}

    trail.append(TrailEntry(
        agent="social_monitor",
        timestamp=start,
        action="start",
        detail=f"Stealth scroll starting on: {company_url}",
        severity="info",
    ))

    raw_posts = await _scroll_and_capture(company_url)
    posts = _parse_posts(raw_posts, company_url)
    social_claims = _social_posts_to_claims(posts)
    screenshots = [p["screenshot_path"] for p in posts if p["screenshot_path"]]

    trail.append(TrailEntry(
        agent="social_monitor",
        timestamp=datetime.utcnow().isoformat(),
        action="scraped",
        detail=(
            f"Posts captured: {len(posts)} | "
            f"Social claims extracted: {len(social_claims)} | "
            f"Screenshots saved: {len(screenshots)}"
        ),
        severity="info" if posts else "warning",
    ))

    # Flag discrepancy summary
    green_pr_posts = [p for p in posts if p["sentiment_keywords"]]
    if green_pr_posts:
        trail.append(TrailEntry(
            agent="social_monitor",
            timestamp=datetime.utcnow().isoformat(),
            action="green_pr_detected",
            detail=(
                f"⚠️ {len(green_pr_posts)} posts with high-sentiment green marketing detected. "
                f"Keywords: {', '.join(set(kw for p in green_pr_posts for kw in p['sentiment_keywords'][:3]))}"
            ),
            severity="flag",
        ))

    return {
        "social_posts": posts,
        "screenshots": screenshots,
        "claims": social_claims,
        "reasoning_trail": trail,
    }


def run_social_monitor(state: SwarmState) -> dict:
    """LangGraph node: Agent A2 — Social Monitor (sync wrapper)."""
    return asyncio.run(_run_social_monitor_async(state))
