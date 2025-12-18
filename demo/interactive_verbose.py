#!/usr/bin/env python
"""Interactive demo with streaming output (shows complete raw LLM thinking)."""

from src.agent import create_sni_agent, stream_query


def main():
    """Interactive agent demo with streaming output."""
    print("\n" + "="*80)
    print("SNI Agent Interactive Demo - Streaming Mode")
    print("="*80)
    print("\nYou will see the complete raw output from the LLM as it thinks.")
    print("This includes the reasoning process and tool calling decisions.")
    print("\nType 'quit' to exit.\n")

    agent = create_sni_agent()

    while True:
        try:
            query = input("\nEnter your query: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nBye!")
            break

        if not query:
            continue

        if query.lower() in ('quit', 'exit', 'q'):
            print("Bye!")
            break

        result = stream_query(agent, query)

        print("\n" + "-"*80)
        print("EXECUTION SUMMARY")
        print("-"*80)
        print(f"Total Iterations: {result['iterations']}")
        print(f"Tools Called: {len(result['tool_calls'])}")

        if result['tool_calls']:
            print("\nTool Sequence:")
            for i, tc in enumerate(result['tool_calls'], 1):
                args_str = ', '.join(f"{k}={v}" for k, v in tc['args'].items())
                print(f"  {i}. {tc['tool']}({args_str})")


if __name__ == "__main__":
    main()
