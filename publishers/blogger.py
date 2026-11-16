"""Blogger publisher: free blog post on the owner's blog (Google OAuth)."""
from core import config
from core.http import request


def _token():
    refresh = config.env("GOOGLE_REFRESH_TOKEN")
    cid = config.env("GOOGLE_CLIENT_ID")
    secret = config.env("GOOGLE_CLIENT_SECRET")
    if not (refresh and cid and secret):
        return None
    status, body = request("POST", "https://oauth2.googleapis.com/token", data={
        "client_id": cid, "client_secret": secret,
        "refresh_token": refresh, "grant_type": "refresh_token"})
    return (body or {}).get("access_token") if isinstance(body, dict) else None


def post(post, media, dry_run=False):
    blog_id = config.env("BLOGGER_BLOG_ID")
    token = _token()
    if not (blog_id and token):
        return {"ok": False, "skipped": True, "error": "BLOGGER_BLOG_ID or Google OAuth missing"}
    if dry_run:
        return {"ok": True, "dry_run": True}

    html = (f"<p>{post['body']}</p>"
            f"<p><a href=\"{config.env('SITE_URL', 'https://gahonsh-blip.github.io')}\">"
            f"See the work</a></p>")
    payload = {"kind": "blogger#post", "title": post["headline"], "content": html}
    status, body = request(
        "POST", f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts/",
        json_body=payload, headers={"Authorization": f"Bearer {token}"})
    if not isinstance(body, dict) or not body.get("id"):
        return {"ok": False, "error": str(body)[:250]}
    return {"ok": True, "id": body["id"], "link": body.get("url")}
