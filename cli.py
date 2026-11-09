#!/usr/bin/env python3
"""Command-line tool for the Grid Connect cloud.

Examples
--------
    # List your devices and their local keys (prompts for password):
    python cli.py --email you@example.com --country 61 devices

    # Try another data centre if login fails on the default:
    python cli.py --email you@example.com --region eu devices

    # Read a device's live datapoints:
    python cli.py --email you@example.com dps <devId>

    # Turn a plug on / off (dp 1 is usually the main switch):
    python cli.py --email you@example.com set <devId> 1 true
    python cli.py --email you@example.com set <devId> 1 false

    # Dump everything LocalTuya/tinytuya needs, as JSON:
    python cli.py --email you@example.com --json devices > devices.json

The password is read from the GRIDCONNECT_PASSWORD env var, or prompted for.
Nothing is written anywhere unless you redirect output yourself.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys

from pytuya_gridconnect import GridConnectCloud, GridConnectError, REGIONS


def _value(token: str):
    """Coerce a CLI datapoint value: true/false -> bool, ints -> int, else str."""
    low = token.lower()
    if low in ("true", "false"):
        return low == "true"
    try:
        return int(token)
    except ValueError:
        return token


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Grid Connect cloud CLI")
    p.add_argument("--email", required=True, help="Grid Connect account email")
    p.add_argument("--country", default="61", help="Country calling code (AU=61)")
    p.add_argument(
        "--region", default="us", choices=sorted(REGIONS), help="Tuya data centre"
    )
    p.add_argument("--json", action="store_true", help="Machine-readable JSON output")

    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("devices", help="List all devices + local keys")
    sp = sub.add_parser("dps", help="Read a device's datapoints")
    sp.add_argument("dev_id")
    ss = sub.add_parser("set", help="Write a datapoint")
    ss.add_argument("dev_id")
    ss.add_argument("dp")
    ss.add_argument("value")

    args = p.parse_args(argv)
    password = os.environ.get("GRIDCONNECT_PASSWORD") or getpass.getpass(
        "Grid Connect password: "
    )

    cloud = GridConnectCloud(country_code=args.country, region=args.region)
    try:
        cloud.login_email(args.email, password)
    except GridConnectError as err:
        print(f"Login failed on region '{args.region}': {err}", file=sys.stderr)
        print(
            "If this says SIGN_INVALID the signing keys are wrong; if it says the "
            "account/region is wrong, retry with --region eu (or in).",
            file=sys.stderr,
        )
        return 2

    try:
        if args.cmd == "devices":
            devices = cloud.devices()
            if args.json:
                print(json.dumps([d.__dict__ for d in devices], indent=2, default=str))
            else:
                if not devices:
                    print("No devices found on this account/region.")
                for d in devices:
                    status = "online" if d.online else "offline"
                    print(f"\n{d.name}  ({status})")
                    print(f"  devId     : {d.dev_id}")
                    print(f"  localKey  : {d.local_key}")
                    print(f"  productId : {d.product_id}")
                    print(f"  category  : {d.category}")
                    if d.dps:
                        print(f"  dps       : {json.dumps(d.dps)}")
        elif args.cmd == "dps":
            print(json.dumps(cloud.get_dps(args.dev_id), indent=2))
        elif args.cmd == "set":
            cloud.set_dps(args.dev_id, {args.dp: _value(args.value)})
            print("ok")
    except GridConnectError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
