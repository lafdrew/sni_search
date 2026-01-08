"""Test script to verify TGT standardization refactoring."""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.agent import SNIAgent


async def test_tgt_standardization():
    """Test TGT standardization as independent node."""

    print("=" * 60)
    print("Testing TGT Standardization Refactoring")
    print("=" * 60)

    # Initialize agent
    agent = SNIAgent()

    # Test query
    test_query = "api.bilibili.com"

    print(f"\n[Test Query]: {test_query}")
    print("\nExpected behavior:")
    print("  1. Workflow should have 12 nodes (not 11)")
    print("  2. synthesize_node should return 'raw_answer'")
    print("  3. tgt_standardization_node should execute independently")
    print("  4. Final answer should contain '_tgt_metadata'")

    print("\n" + "-" * 60)
    print("Executing search with streaming...")
    print("-" * 60)

    try:
        # Track stages
        stages_seen = []

        # Execute search with streaming
        async for event in agent.aquery_stream(
            query=test_query,
            verbose=True
        ):
            # Event structure: {"type": "node_{node_name}", "data": {"node": ..., "state": ...}}
            event_type = event.get("type", "")
            stage = event.get("data", {}).get("node") if event_type.startswith("node_") else None
            state = event.get("data", {}).get("state", {})

            if stage and stage not in stages_seen:
                stages_seen.append(stage)
                print(f"[OK] Stage: {stage}")

                # Check for specific fields
                if stage == "synthesize":
                    if "raw_answer" in state:
                        print("  -> raw_answer present [OK]")
                    else:
                        print("  -> raw_answer MISSING [FAIL]")

                if stage == "tgt_standardization":
                    if "final_answer" in state:
                        print("  -> final_answer present [OK]")
                    else:
                        print("  -> final_answer MISSING [FAIL]")

                    if "tgt_metadata" in state:
                        print("  -> tgt_metadata present [OK]")
                        metadata = state.get("tgt_metadata", {})
                        match_type = metadata.get("match_type", "unknown")
                        print(f"  -> match_type: {match_type}")
                    else:
                        print("  -> tgt_metadata MISSING [FAIL]")

        print("\n" + "=" * 60)
        print("Test Results:")
        print("=" * 60)

        # Verify results
        success = True

        # Check 1: Stage count
        if len(stages_seen) == 12:
            print(f"[OK] Stage count: {len(stages_seen)} (expected 12)")
        else:
            print(f"[FAIL] Stage count: {len(stages_seen)} (expected 12)")
            success = False

        # Check 2: synthesize stage
        if "synthesize" in stages_seen:
            print("[OK] synthesize stage executed")
        else:
            print("[FAIL] synthesize stage NOT executed")
            success = False

        # Check 3: tgt_standardization stage
        if "tgt_standardization" in stages_seen:
            print("[OK] tgt_standardization stage executed")
        else:
            print("[FAIL] tgt_standardization stage NOT executed")
            success = False

        # Check 4: Stage order
        if stages_seen.index("synthesize") < stages_seen.index("tgt_standardization"):
            print("[OK] Stage order correct (synthesize -> tgt_standardization)")
        else:
            print("[FAIL] Stage order INCORRECT")
            success = False

        print("\n" + "=" * 60)
        if success:
            print("[SUCCESS] ALL TESTS PASSED!")
        else:
            print("[FAILURE] SOME TESTS FAILED!")
        print("=" * 60)

        return success

    except Exception as e:
        print(f"\n[ERROR] Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_tgt_standardization())
    sys.exit(0 if result else 1)
