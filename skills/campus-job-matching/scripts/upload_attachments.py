#!/usr/bin/env python3
"""Upload JD screenshots (公司-岗位.png) into a Feishu Bitable attachment field.

Usage:
  python3 upload_attachments.py \
    --token <tenant_access_token> \
    --app <app_token> --table <table_id> --field <attachment_field_name> \
    --shots-dir <local_dir_of_pngs> \
    [--match-file <json: {filename: {company, position}}>] \
    [--skip <filename1,filename2>]

Rules:
- Field must be an attachment field (type 17). It will be auto-created if missing.
- Screenshot filename convention: 公司-岗位.png. Records are matched by
  company substring + position keyword. If --match-file is given it wins.
- Never silently mis-assign: any shot with 0 or >1 matches is reported, not written.
"""
import argparse, json, os, sys, uuid, urllib.request, urllib.error

API = "https://open.feishu.cn/open-apis"

def req(method, url, token, body=None, multipart=None):
    if multipart is not None:
        data, ctype = multipart
    else:
        data = json.dumps(body).encode() if body is not None else None
        ctype = "application/json"
    r = urllib.request.Request(url, method=method, data=data)
    r.add_header("Authorization", "Bearer " + token)
    r.add_header("Content-Type", ctype)
    try:
        with urllib.request.urlopen(r) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"http_error": e.code, "body": e.read().decode()[:300]}

def make_multipart(fields, filepath, filename):
    boundary = uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    with open(filepath, "rb") as f:
        content = f.read()
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\nContent-Type: image/png\r\n\r\n".encode() + content + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"

def upload(token, app, path):
    fn = os.path.basename(path)
    mp = make_multipart({"file_name": fn, "parent_type": "bitable_file",
                         "parent_node": app, "size": str(os.path.getsize(path))}, path, fn)
    d = req("POST", f"{API}/drive/v1/files/upload_all", token, multipart=mp)
    if d.get("code") == 0:
        return d["data"]["file_token"]
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", required=True)
    ap.add_argument("--app", required=True)
    ap.add_argument("--table", required=True)
    ap.add_argument("--field", required=True, help="attachment field name, auto-created if missing")
    ap.add_argument("--shots-dir", required=True)
    ap.add_argument("--match-file", default=None)
    ap.add_argument("--skip", default="")
    args = ap.parse_args()

    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    shots = [f for f in sorted(os.listdir(args.shots_dir))
             if f.endswith(".png") and f not in skip]
    match_map = json.load(open(args.match_file, encoding="utf-8")) if args.match_file else None

    base = f"{API}/bitable/v1/apps/{args.app}/tables/{args.table}"

    # ensure field exists
    fd = req("GET", f"{base}/fields?page_size=100", args.token)
    fld = {f["field_name"]: f for f in fd.get("data", {}).get("items", [])}
    if args.field not in fld:
        rr = req("POST", f"{base}/fields", args.token, {"field_name": args.field, "type": 17})
        if rr.get("code") != 0:
            print("create field FAIL:", rr); sys.exit(1)
        print("created field:", args.field)

    # upload all shots
    tokens = {}
    for fn in shots:
        ft = upload(args.token, args.app, os.path.join(args.shots_dir, fn))
        if ft:
            tokens[fn] = ft
        else:
            print("upload FAIL:", fn)
    print("uploaded:", len(tokens), "/", len(shots))

    # pull records
    records, page_token = [], ""
    while True:
        url = f"{base}/records?page_size=100" + (("&page_token=" + page_token) if page_token else "")
        d = req("GET", url, args.token)
        records.extend(d["data"]["items"])
        if d["data"].get("has_more") and d["data"].get("page_token"):
            page_token = d["data"]["page_token"]
        else:
            break
    nonempty = [r for r in records if r["fields"].get("公司")]
    print("records:", len(nonempty))

    def match(fn, rec):
        comp = rec["fields"].get("公司", "")
        pos = rec["fields"].get("投递岗位", "")
        if match_map and fn in match_map:
            m = match_map[fn]
            return m.get("公司") in comp and m.get("position") in pos
        head = fn.split("-", 1)[0]
        rest = fn.split("-", 1)[1].replace(".png", "") if "-" in fn else ""
        if not head or not rest:
            return False
        return head in comp and rest[:4] in pos  # heuristic: company + position keyword

    updates, unmatched = [], []
    for fn, ft in tokens.items():
        hit = [r for r in nonempty if match(fn, r)]
        if len(hit) == 1:
            updates.append({"record_id": hit[0]["record_id"],
                            "fields": {args.field: [{"file_token": ft, "name": fn}]}})
        else:
            unmatched.append(fn + (f" (multi={len(hit)})" if hit else " (no match)"))
    print("matched:", len(updates), "| unmatched:", unmatched or "none")

    for i in range(0, len(updates), 100):
        rr = req("POST", f"{base}/records/batch_update", args.token, {"records": updates[i:i+100]})
        print("batch", i // 100, ":", rr.get("code"), rr.get("msg"))
    print("done")

if __name__ == "__main__":
    main()
