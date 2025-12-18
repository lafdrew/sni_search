#!/usr/bin/env python
"""SNI Recognition CLI Demo.

Usage:
    uv run python demo/cli.py <sni>
    uv run python demo/cli.py  (interactive mode)
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from src.tools import SNITools
from src.config import settings


API_URL = f"http://localhost:{settings.API_PORT}"


def query_via_api(sni: str) -> dict:
    """Query SNI via API server."""
    try:
        response = requests.post(
            f"{API_URL}/api/query",
            json={"query": sni},
            timeout=60,
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.text}
    except requests.exceptions.ConnectionError:
        return {"error": "API server not running"}


def query_direct(sni: str) -> dict:
    """Query SNI directly using tools."""
    tools = SNITools()

    # Try exact match first
    result = tools.search_sni_exact(sni)
    if result.get("found"):
        return {
            "type": "exact",
            "sni": result["sni"],
            "domain": result["domain"],
            "protocols": result.get("protocols", []),
            "related_snis": result.get("all_related_snis", []),
        }

    # Fallback to vector search
    results = tools.search_sni_vector(sni, top_k=3)
    if results:
        return {
            "type": "vector",
            "query": sni,
            "matches": results,
        }

    return {"type": "not_found", "sni": sni}


def format_result(result: dict) -> str:
    """Format result for display."""
    lines = []
    lines.append("-" * 50)

    if "error" in result:
        lines.append(f"Error: {result['error']}")

    elif "answer" in result:
        # API response
        lines.append(f"Query: {result.get('query', 'N/A')}")
        lines.append(f"Steps: {result.get('steps', 0)}")
        lines.append("")
        lines.append(result["answer"])

    elif result.get("type") == "exact":
        lines.append(f"SNI: {result['sni']}")
        lines.append(f"Domain: {result['domain']}")
        lines.append(f"Protocols: {', '.join(result.get('protocols', []))}")
        if result.get("related_snis"):
            lines.append(f"Related SNIs: {', '.join(result['related_snis'][:5])}")

    elif result.get("type") == "vector":
        lines.append(f"Query: {result['query']}")
        lines.append("Similar SNIs found:")
        for match in result.get("matches", []):
            lines.append(
                f"  - {match['sni']} (domain: {match['domain']}, score: {match['score']})"
            )

    elif result.get("type") == "not_found":
        lines.append(f"SNI '{result['sni']}' not found in database")

    lines.append("-" * 50)
    return "\n".join(lines)


def main():
    """Main entry point."""
    print("=" * 50)
    print("SNI Recognition Demo")
    print("=" * 50)

    # Check if API is available
    use_api = False
    try:
        resp = requests.get(f"{API_URL}/api/health", timeout=2)
        if resp.status_code == 200:
            use_api = True
            print(f"Mode: API (server running at {API_URL})")
    except Exception:
        pass

    if not use_api:
        print("Mode: Direct (using local tools)")

    print("")

    # Single query mode
    if len(sys.argv) > 1:
        sni = sys.argv[1]
        print(f"Querying: {sni}")
        if use_api:
            result = query_via_api(sni)
        else:
            result = query_direct(sni)
        print(format_result(result))
        return

    # Interactive mode
    print("Enter SNI to query (or 'quit' to exit):")
    print("")

    while True:
        try:
            sni = input("SNI> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not sni:
            continue

        if sni.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break

        print(f"Querying: {sni}")
        if use_api:
            result = query_via_api(sni)
        else:
            result = query_direct(sni)
        print(format_result(result))


if __name__ == "__main__":
    main()
