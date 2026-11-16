"""LinkedIn publisher: text post (with link preview) on a profile or company page.

Uses LinkedIn's REST posts API with an OAuth 2.0 access token created once by
auth/linkedin_oauth.py. Scopes: openid profile w_member_social
(plus w_organization_social + r_organization_admin for a company page).
"""
from core import config
from core.http import request

API = "https://api.linkedin.com/rest/posts"
VERSION = "202506"


def _author(token):
    """urn:li:person:{sub} for a profile, or LINKEDIN_ORG_ID for a page."""
    org = config.env("LINKEDIN_ORG_ID")
    if org:
        return f"urn:li:organization:{org}"
    status, body = request("GET", "https://api.linkedin.com/v2/userinfo",
                           headers={"Authorization": f"Bearer {token}"})
    sub = (body or {}).get("sub") if isinstance(body, dict) else None
    return f"urn:li:person:{sub}" if sub else None


def post(post, media, dry_run=False):
    token = config.env("LINKEDIN_ACCESS_TOKEN")
    if not token:
        return {"ok": False, "skipped": True, "error": "LINKEDIN_ACCESS_TOKEN missing (run auth/linkedin_oauth.py once)"}
    if dry_run:
        return {"ok": True, "dry_run": True}

    author = _author(token)
    if not author:
        return {"ok": False, "error": "could not resolve LinkedIn author (token expired?)"}

    body = {
        "author": author,
        "commentary": media["caption"],
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED",
                         "targetEntities": [], "thirdPartyDistributionChannels": []},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    status, res = request(
        "POST", API, json_body=body,
        headers={
            "Authorization": f"Bearer {token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": VERSION,
        },
    )
    if status not in (200, 201):
        return {"ok": False, "error": str(res)[:250]}

    urn = res if isinstance(res, str) else str(res)
    # the post URN comes back in the x-restli-id header; the helper keeps JSON only
    return {"ok": True, "id": urn[-60:] if urn else None,
            "link": "https://www.linkedin.com/in/gahonsh-company-b05528311/recent-activity/all/"}
