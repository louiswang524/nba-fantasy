import logging
import os
from dotenv import load_dotenv
import google.genai as genai

load_dotenv()

MODEL = "gemini-2.0-flash"
logger = logging.getLogger(__name__)


def ask_gemini(prompt: str) -> str:
    """Send a prompt to Gemini and return the response text."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in .env")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=MODEL, contents=prompt)
    if not response.text:
        logger.warning("Gemini returned empty response: %s", response)
        raise ValueError("Gemini returned empty or malformed response")
    return response.text


def build_matchup_prompt(
    my_proj: dict,
    opp_proj: dict,
    classification: dict,
    b2b_players: list[str] | None = None,
) -> str:
    lines = ["You are an expert fantasy basketball analyst. Here is this week's H2H category matchup projection:\n"]
    lines.append(f"{'Category':<8} {'My Team':>10} {'Opponent':>10} {'Status':>10}")
    lines.append("-" * 42)
    for cat in my_proj:
        lines.append(f"{cat:<8} {my_proj[cat]:>10.1f} {opp_proj.get(cat, 0.0):>10.1f} {classification.get(cat, '?'):>10}")
    if b2b_players:
        lines.append(f"\n⚠️  Back-to-back risk this week: {', '.join(b2b_players)}")
    lines.append("\nProvide a concise weekly strategy: which categories to focus on winning, which to punt, and 2-3 specific streaming/lineup actions to swing toss-up categories.")
    return "\n".join(lines)


def build_start_sit_prompt(players: list[dict]) -> str:
    lines = ["You are an expert fantasy basketball analyst. Here is today's roster ranked by projected contribution:\n"]
    lines.append(f"{'Rank':<5} {'Player':<22} {'Status':<6} {'G':<3} {'Proj PTS':<10} {'Floor':<8} {'Ceil':<8} {'B2B':<5} {'USG%Δ':<7}")
    lines.append("-" * 78)
    for i, p in enumerate(players, 1):
        proj = p.get("projected", {})
        pts = proj.get("PTS", 0)
        std = p.get("std_pts", 0.0)
        floor_pts = max(0.0, pts - std)
        ceil_pts = pts + std
        b2b = "YES" if p.get("games_detail", {}).get("b2b_count", 0) > 0 else "-"
        usg_delta = p.get("usg_spike", 0.0)
        usg_str = f"+{usg_delta:.1f}" if usg_delta > 0 else f"{usg_delta:.1f}"
        lines.append(
            f"{i:<5} {p['name']:<22} {p.get('status',''):<6} {p.get('games_remaining', 0):<3} "
            f"{pts:<10.1f} {floor_pts:<8.1f} {ceil_pts:<8.1f} {b2b:<5} {usg_str:<7}"
        )
    lines.append("\nGive a clear start/sit recommendation for each player. Flag high-variance players (wide floor/ceiling gap) and B2B risks. Be direct.")
    return "\n".join(lines)


def build_waiver_prompt(free_agents: list[dict], my_weaknesses: list[str]) -> str:
    lines = [f"You are a fantasy basketball analyst. My team is weak in: {', '.join(my_weaknesses)}.\n"]
    lines.append("Top available free agents scored against my needs:\n")
    lines.append(f"{'Rank':<5} {'Player':<22} {'Pos':<6} {'G':<3} {'Fit':<7} {'PTS':<6} {'REB':<6} {'AST':<6} {'3PM':<6} {'STL':<6} {'BLK':<6} {'TO':<6} {'USG%Δ':<7}")
    lines.append("-" * 95)
    for i, p in enumerate(free_agents[:20], 1):
        proj = p.get("projected", {})
        usg_delta = p.get("usg_spike", 0.0)
        usg_str = f"+{usg_delta:.1f}" if usg_delta > 0 else f"{usg_delta:.1f}"
        lines.append(
            f"{i:<5} {p['name']:<22} {p.get('position',''):<6} {p.get('games_remaining',0):<3} "
            f"{p.get('fit_score',0):<7.2f} {proj.get('PTS',0):<6.1f} {proj.get('REB',0):<6.1f} "
            f"{proj.get('AST',0):<6.1f} {proj.get('FG3M',0):<6.1f} {proj.get('STL',0):<6.1f} "
            f"{proj.get('BLK',0):<6.1f} {proj.get('TOV',0):<6.1f} {usg_str:<7}"
        )
    lines.append("\nRecommend the top 5 pickups. Highlight players with rising usage (USG%Δ > 3) as emerging streamers. One sentence of reasoning each.")
    return "\n".join(lines)


def build_trade_prompt(delta: dict, matchup_context: dict) -> str:
    lines = ["You are a fantasy basketball analyst evaluating a trade. Per-category impact (+ = gain):\n"]
    lines.append(f"{'Category':<8} {'Delta':>10} {'Matchup Status':>15}")
    lines.append("-" * 36)
    for cat in delta:
        status = matchup_context.get(cat, "?")
        lines.append(f"{cat:<8} {delta[cat]:>+10.1f} {status:>15}")
    lines.append("\nGive a verdict: ACCEPT, DECLINE, or COUNTER with brief reasoning (3-5 sentences).")
    return "\n".join(lines)
