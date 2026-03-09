#!/usr/bin/env python3
"""Seedream Image Generate - CLI for Star Office UI background generation.

Calls Volcengine Seedream API to generate images.

Expected interface (called by Star Office UI backend):
  python gemini_image_generate.py \
    --prompt "..." \
    --model <model_name> \
    --out-dir /tmp/xxx \
    --cleanup \
    [--aspect-ratio 16:9] \
    [--reference-image /path/to/ref.webp]

Environment:
  SEEDREAM_API_KEY  - Volcengine API key (required)
  SEEDREAM_MODEL    - override model name (optional, --model takes precedence)

Output (last line of stdout):
  {"files": ["/tmp/xxx/generated_0.png"]}
"""

import argparse
import json
import os
import sys
import tempfile
import urllib.request
import urllib.error
from pathlib import Path

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


SEEDREAM_API_URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
DEFAULT_MODEL = "doubao-seedream-5-0-260128"


def main():
    parser = argparse.ArgumentParser(description="Generate image via Seedream API")
    parser.add_argument("--prompt", required=True, help="Generation prompt")
    parser.add_argument("--model", default="", help="Model name")
    parser.add_argument("--out-dir", required=True, help="Output directory")
    parser.add_argument("--cleanup", action="store_true", help="(ignored, kept for compat)")
    parser.add_argument("--aspect-ratio", default="", help="Aspect ratio hint (e.g. 16:9)")
    parser.add_argument("--reference-image", default="", help="Reference image path (ignored for Seedream)")
    args = parser.parse_args()

    api_key = os.environ.get("SEEDREAM_API_KEY", "").strip()
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("ERROR: SEEDREAM_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    model = os.environ.get("SEEDREAM_MODEL", "").strip() or args.model.strip()
    if not model:
        model = DEFAULT_MODEL

    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)

    prompt_text = args.prompt
    if args.aspect_ratio:
        prompt_text += f"\nTarget aspect ratio: {args.aspect_ratio}."

    size_map = {
        "16:9": "2K",
        "16:10": "2K",
        "4:3": "2K",
        "1:1": "1K",
        "3:4": "1K",
        "9:16": "1K",
    }
    size = size_map.get(args.aspect_ratio, "2K")

    payload = {
        "model": model,
        "prompt": prompt_text,
        "sequential_image_generation": "disabled",
        "response_format": "url",
        "size": size,
        "stream": False,
        "watermark": True,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    try:
        req = urllib.request.Request(
            SEEDREAM_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if e.fp else ""
        print(f"ERROR: HTTP {e.code}: {err_body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    image_urls = []
    if isinstance(result, dict):
        data_list = result.get("data") or []
        for item in data_list:
            if isinstance(item, dict):
                url = item.get("url") or item.get("b64_json")
                if url:
                    image_urls.append(url)

    if not image_urls:
        print(f"ERROR: No image URL in response: {json.dumps(result)[:500]}", file=sys.stderr)
        sys.exit(1)

    output_files = []
    for idx, img_url in enumerate(image_urls):
        if img_url.startswith("http"):
            try:
                img_req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(img_req, timeout=60) as img_resp:
                    img_data = img_resp.read()
            except Exception as e:
                print(f"ERROR: Failed to download image: {e}", file=sys.stderr)
                continue
        else:
            import base64
            try:
                img_data = base64.b64decode(img_url)
            except Exception as e:
                print(f"ERROR: Failed to decode base64: {e}", file=sys.stderr)
                continue

        ext = ".png"
        out_path = os.path.join(out_dir, f"generated_{idx}{ext}")
        with open(out_path, "wb") as f:
            f.write(img_data)
        output_files.append(out_path)

    if not output_files:
        print("ERROR: No images saved", file=sys.stderr)
        sys.exit(1)

    result = {"files": output_files}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
