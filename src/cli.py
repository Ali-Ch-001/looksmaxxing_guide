"""Command-line interface for Evidence-Led SEO Pipeline."""

import argparse
import asyncio
import json
import sys
from src.pipeline.orchestrator import EvidenceLedPipeline
from src.deployment.cms_exporter import CMSExporter


async def main_async():
    parser = argparse.ArgumentParser(
        description="Evidence-Led Content Engine with Medical Harm-Reduction Gates"
    )
    parser.add_argument(
        "--topic",
        type=str,
        required=True,
        help="Target aesthetic or dermatological topic to process"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="dist/content",
        help="Directory to save generated Markdown and Schema.org JSON-LD"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=":memory:",
        help="SQLite database path for immutable state snapshots"
    )

    args = parser.parse_args()

    pipeline = EvidenceLedPipeline()
    print(f"[*] Ingesting topic: '{args.topic}'...")
    state = await pipeline.run(args.topic)

    print(f"[*] Discipline Namespace: {state.discipline_namespace}")
    print(f"[*] Risk Category: {state.risk_category}")

    if state.is_crisis_routed:
        print("\n[!] BANNED TOPIC OR TOXIC TROPE DETECTED")
        print(f"[!] Rejection Reason: {state.rejection_reason}")
        advisory_path = CMSExporter.export_to_file(state, output_dir=args.output_dir)
        print(f"[+] Exported Harm-Reduction Advisory to: {advisory_path}")
        sys.exit(1)

    if not state.audit_passed:
        print("\n[X] AUDIT FAILED")
        print(f"[X] Rejection Reason: {state.rejection_reason}")
        sys.exit(1)

    print("\n[✓] ALL DETERMINISTIC VERIFICATION GATES PASSED")
    print(f"[*] Citations Verified: {state.draft.citations}")
    print(f"[*] Protocol Steps: {len(state.draft.actionable_protocol)}")

    out_file = CMSExporter.export_to_file(state, output_dir=args.output_dir)
    print(f"[+] Rendered Article and Schema.org JSON-LD exported to: {out_file}")


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
