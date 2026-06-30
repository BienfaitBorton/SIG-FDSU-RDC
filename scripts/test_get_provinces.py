#!/usr/bin/env python3
import urllib.request, sys, traceback

import sys

PORT = sys.argv[1] if len(sys.argv) > 1 else "8000"
URL = f"http://127.0.0.1:{PORT}/provinces"

def main():
    try:
        resp = urllib.request.urlopen(URL, timeout=10)
        print(resp.status)
        print(resp.read().decode())
    except Exception:
        traceback.print_exc()
        return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
