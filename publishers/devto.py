"""dev.to publisher: article post with the day's card as cover image."""
from core import config
from core.http import request


def post(post, media, dry_run=False):
    key = config.env("DEVTO_API_KEY")
    if not key:
        return {"ok": False, "skipped": True, "error": "DEVTO_API_KEY missing"}
    if dry_run:
        return {"ok": True, "dry_run": True}

    body = (
        f"{post['body']}\n\n"
        f"**What we build:** websites, Flutter apps, Node.js and Laravel backends, "
        f"and the dashboards that keep them honest.\n\n"
        f"**Where:** Bundu, Ranchi, India. Remote for clients anywhere.\n\n"
        f"[See the work]({config.env('SITE_URL', 'https://gahonsh-blip.github.io')})\n"
    )
    article = {
        "article": {
            "title": post["headline"],
            "published": True,
            "body_markdown": body,
            "tags": ["webdev", "flutter", "node", "india"],
            "description": post["body"][:140],
        }
    }
    if media.get("image_url"):
        article["article"]["main_image"] = media["image_url"]
    if media.get("image_url"):
        article["article"]["canonical_url"] = config.env("SITE_URL", "https://gahonsh-blip.github.io")

    status, res = request("POST", "https://dev.to/api/articles",
                          json_body=article, headers={"api-key": key})
    if not isinstance(res, dict) or not res.get("id"):
        return {"ok": False, "error": str(res)[:250]}
    return {"ok": True, "id": res["id"], "link": res.get("url")}
