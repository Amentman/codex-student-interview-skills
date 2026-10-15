#!/usr/bin/env python3
"""Reorder Feishu Bitable view field display order (visible_fields, base/v3 endpoint).

Usage:
  python3 reorder_view.py --token <tenant_access_token> \
    --app <app_token> --table <table_id> --view <view_id> \
    --order "公司,投递岗位,城市,..."   # full ordered list of visible field names

Endpoint note: the view field-display API lives under base/v3
(PUT .../views/{view_id}/visible_fields). The bitable/v1 PUT /views/{id}
and /views/{id}/visible_fields endpoints return 404.
"""
import argparse, json, sys, urllib.request, urllib.error

API = "https://open.feishu.cn/open-apis"

def req(method, url, token, body=None):
    r = urllib.request.Request(url, method=method,
        data=json.dumps(body).encode() if body is not None else None)
    r.add_header("Authorization", "Bearer " + token)
    r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"http_error": e.code, "body": e.read().decode()[:300]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", required=True)
    ap.add_argument("--app", required=True)
    ap.add_argument("--table", required=True)
    ap.add_argument("--view", required=True)
    ap.add_argument("--order", required=True, help="comma separated full field order")
    args = ap.parse_args()
    order = [f.strip() for f in args.order.split(",") if f.strip()]

    url = f"{API}/base/v3/bases/{args.app}/tables/{args.table}/views/{args.view}/visible_fields"
    d = req("PUT", url, args.token, {"visible_fields": order})
    if d.get("code") == 0:
        print("reordered:", d.get("data"))
    else:
        print("FAIL:", json.dumps(d, ensure_ascii=False)[:400])
        sys.exit(1)

if __name__ == "__main__":
    main()
