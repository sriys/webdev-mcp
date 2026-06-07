#!/usr/bin/env python3
"""
Web Development Tools MCP Server

Provides documentation search and fetching for:
  - GSAP (GreenSock Animation Platform)
  - React
  - React Three Fiber (R3F)
  - Lenis (smooth scroll)
  - Barba.js (page transitions)
  - Spline (3D for the web)
  - Osmo Supply (creative web resources)
"""

from __future__ import annotations

import json
import re
from enum import Enum
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, ConfigDict, Field
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Server init
# ---------------------------------------------------------------------------
mcp = FastMCP("webdev_tools_mcp")

# ---------------------------------------------------------------------------
# Library catalogue
# ---------------------------------------------------------------------------
LIBRARIES: dict[str, dict] = {
    "gsap": {
        "name": "GSAP (GreenSock Animation Platform)",
        "home": "https://gsap.com/docs/v3/",
        "search": "https://gsap.com/search/?q={query}",
        "description": "Professional-grade JavaScript animation library",
    },
    "react": {
        "name": "React",
        "home": "https://react.dev/reference/react",
        "search": "https://react.dev/search?q={query}",
        "description": "JavaScript library for building user interfaces",
    },
    "r3f": {
        "name": "React Three Fiber",
        "home": "https://r3f.docs.pmnd.rs/getting-started/introduction",
        "search": "https://r3f.docs.pmnd.rs/search?q={query}",
        "description": "React renderer for Three.js",
    },
    "lenis": {
        "name": "Lenis",
        "home": "https://lenis.darkroom.engineering/",
        "search": "https://lenis.darkroom.engineering/",
        "description": "Lightweight, robust, and performant smooth-scroll library",
    },
    "barba": {
        "name": "Barba.js",
        "home": "https://barba.js.org/docs/getstarted/intro/",
        "search": "https://barba.js.org/search?q={query}",
        "description": "Fluid, smooth transitions between website pages",
    },
    "spline": {
        "name": "Spline",
        "home": "https://docs.spline.design/",
        "search": "https://docs.spline.design/",
        "description": "3D design tool for the web",
    },
    "osmo": {
        "name": "Osmo Supply",
        "home": "https://www.osmo.supply/",
        "search": "https://www.osmo.supply/",
        "description": "Creative web development resources and components",
    },
}

# GSAP quick-access paths
GSAP_SECTIONS: dict[str, str] = {
    "core":        "https://gsap.com/docs/v3/GSAP/",
    "timeline":    "https://gsap.com/docs/v3/GSAP/Timeline/",
    "tween":       "https://gsap.com/docs/v3/GSAP/Tween/",
    "scrolltrigger": "https://gsap.com/docs/v3/Plugins/ScrollTrigger/",
    "draggable":   "https://gsap.com/docs/v3/Plugins/Draggable/",
    "flip":        "https://gsap.com/docs/v3/Plugins/Flip/",
    "motionpath":  "https://gsap.com/docs/v3/Plugins/MotionPathPlugin/",
    "scrollto":    "https://gsap.com/docs/v3/Plugins/ScrollToPlugin/",
    "text":        "https://gsap.com/docs/v3/Plugins/TextPlugin/",
    "observer":    "https://gsap.com/docs/v3/Plugins/Observer/",
    "splittext":   "https://gsap.com/docs/v3/Plugins/SplitText/",
    "custombounce":"https://gsap.com/docs/v3/Plugins/CustomBounce/",
    "ease":        "https://gsap.com/docs/v3/Eases/",
    "utils":       "https://gsap.com/docs/v3/GSAP/gsap.utils/",
    "ticker":      "https://gsap.com/docs/v3/GSAP/gsap.ticker/",
}

# React key sections
REACT_SECTIONS: dict[str, str] = {
    "hooks":       "https://react.dev/reference/react/hooks",
    "usestate":    "https://react.dev/reference/react/useState",
    "useeffect":   "https://react.dev/reference/react/useEffect",
    "useref":      "https://react.dev/reference/react/useRef",
    "usecontext":  "https://react.dev/reference/react/useContext",
    "usememo":     "https://react.dev/reference/react/useMemo",
    "usecallback": "https://react.dev/reference/react/useCallback",
    "usereducer":  "https://react.dev/reference/react/useReducer",
    "components":  "https://react.dev/reference/react/components",
    "apis":        "https://react.dev/reference/react/apis",
    "learn":       "https://react.dev/learn",
    "dom":         "https://react.dev/reference/react-dom",
}

# R3F key sections
R3F_SECTIONS: dict[str, str] = {
    "intro":       "https://r3f.docs.pmnd.rs/getting-started/introduction",
    "canvas":      "https://r3f.docs.pmnd.rs/api/canvas",
    "objects":     "https://r3f.docs.pmnd.rs/api/objects",
    "hooks":       "https://r3f.docs.pmnd.rs/api/hooks",
    "events":      "https://r3f.docs.pmnd.rs/api/events",
    "drei":        "https://drei.pmnd.rs/",
    "performance": "https://r3f.docs.pmnd.rs/advanced/performance",
    "typescript":  "https://r3f.docs.pmnd.rs/tutorials/typescript",
    "v8":          "https://r3f.docs.pmnd.rs/getting-started/migration-guides",
}

# Barba.js key sections
BARBA_SECTIONS: dict[str, str] = {
    "intro":       "https://barba.js.org/docs/getstarted/intro/",
    "install":     "https://barba.js.org/docs/getstarted/install/",
    "transitions": "https://barba.js.org/docs/advanced/transitions/",
    "hooks":       "https://barba.js.org/docs/advanced/hooks/",
    "views":       "https://barba.js.org/docs/advanced/views/",
    "plugins":     "https://barba.js.org/docs/plugins/intro/",
    "router":      "https://barba.js.org/docs/plugins/router/",
    "prefetch":    "https://barba.js.org/docs/plugins/prefetch/",
}

# ---------------------------------------------------------------------------
# Shared HTTP helpers
# ---------------------------------------------------------------------------

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


async def _fetch_and_clean(url: str, max_chars: int = 8000) -> str:
    """Fetch a URL, strip nav/footer, return trimmed plain text."""
    async with httpx.AsyncClient(follow_redirects=True, headers=_HEADERS) as client:
        resp = await client.get(url, timeout=20.0)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Drop noise elements
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "aside", "noscript", "svg", "form"]):
        tag.decompose()

    # Prefer semantic content containers
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find(attrs={"role": "main"})
        or soup.find(class_=re.compile(r"\b(content|docs|article|prose|main)\b", re.I))
        or soup.body
    )

    raw = (main or soup).get_text(separator="\n", strip=True)

    # Collapse blank lines
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    cleaned = "\n".join(lines)

    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars] + (
            f"\n\n… [truncated at {max_chars} chars — fetch a more specific page for details]"
        )

    return cleaned


def _error(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        code = e.response.status_code
        msgs = {
            404: "Page not found (404). The docs URL may have moved — try a different section.",
            403: "Access denied (403). The site may be blocking automated requests.",
            429: "Rate-limited (429). Wait a moment then try again.",
        }
        return f"Error: {msgs.get(code, f'HTTP {code}')}"
    if isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out — the docs server is slow. Try again."
    return f"Error: {type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
# Pydantic input models
# ---------------------------------------------------------------------------

class LibraryName(str, Enum):
    gsap   = "gsap"
    react  = "react"
    r3f    = "r3f"
    lenis  = "lenis"
    barba  = "barba"
    spline = "spline"
    osmo   = "osmo"


class FetchPageInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    url: str = Field(
        ...,
        description=(
            "Full documentation URL to fetch. "
            "E.g. 'https://gsap.com/docs/v3/Plugins/ScrollTrigger/'"
        ),
        min_length=10,
    )
    max_chars: Optional[int] = Field(
        default=8000,
        description="Maximum characters to return (default 8000)",
        ge=500,
        le=24000,
    )


class LibraryOverviewInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    library: LibraryName = Field(
        ...,
        description=(
            "Library to get overview for. "
            "One of: gsap, react, r3f, lenis, barba, spline, osmo"
        ),
    )


class GsapSectionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    section: str = Field(
        ...,
        description=(
            "GSAP section/plugin to fetch. "
            "Options: core, timeline, tween, scrolltrigger, draggable, flip, "
            "motionpath, scrollto, text, observer, splittext, ease, utils, ticker. "
            "Or pass any custom GSAP docs path like 'gsap.to'."
        ),
        min_length=2,
    )


class ReactSectionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    section: str = Field(
        ...,
        description=(
            "React section to fetch. "
            "Options: hooks, usestate, useeffect, useref, usecontext, usememo, "
            "usecallback, usereducer, components, apis, learn, dom. "
            "Or pass a specific hook/component name like 'useTransition'."
        ),
        min_length=2,
    )


class R3fSectionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    section: str = Field(
        ...,
        description=(
            "R3F section to fetch. "
            "Options: intro, canvas, objects, hooks, events, drei, "
            "performance, typescript, v8. "
            "Or pass any R3F concept like 'useFrame', 'useThree'."
        ),
        min_length=2,
    )


class BarbasSectionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    section: str = Field(
        ...,
        description=(
            "Barba.js section to fetch. "
            "Options: intro, install, transitions, hooks, views, plugins, router, prefetch."
        ),
        min_length=2,
    )


class SearchDocsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(
        ...,
        description="What to search for (e.g. 'scrolltrigger pin', 'useFrame camera', 'smooth scroll momentum')",
        min_length=2,
        max_length=200,
    )
    library: Optional[LibraryName] = Field(
        default=None,
        description=(
            "Restrict search to one library. "
            "Leave blank to search across all 7 libraries. "
            "One of: gsap, react, r3f, lenis, barba, spline, osmo"
        ),
    )


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool(
    name="webdev_list_libraries",
    annotations={
        "title": "List Supported Web Dev Libraries",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def webdev_list_libraries() -> str:
    """List all web development libraries supported by this MCP server.

    Returns a catalogue of the 7 supported libraries with their names,
    documentation URLs, and descriptions. Use this to discover what
    libraries are available before fetching specific documentation.

    Returns:
        str: JSON array of library objects with keys: id, name, home, description
    """
    result = [
        {
            "id": key,
            "name": val["name"],
            "home": val["home"],
            "description": val["description"],
        }
        for key, val in LIBRARIES.items()
    ]
    return json.dumps(result, indent=2)


@mcp.tool(
    name="webdev_fetch_page",
    annotations={
        "title": "Fetch Web Dev Docs Page",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def webdev_fetch_page(params: FetchPageInput) -> str:
    """Fetch and return the text content of any documentation page URL.

    Use this to retrieve any specific page from GSAP, React, R3F, Lenis,
    Barba.js, Spline, or Osmo Supply documentation. The page is stripped
    of navigation, footers, scripts, and styles — only the main content
    is returned as clean plain text.

    Args:
        params (FetchPageInput):
            - url (str): Full URL of the documentation page to fetch
            - max_chars (Optional[int]): Max characters to return (default 8000)

    Returns:
        str: Clean plain-text content of the page, or an error message
    """
    try:
        return await _fetch_and_clean(params.url, params.max_chars or 8000)
    except Exception as e:
        return _error(e)


@mcp.tool(
    name="webdev_get_library_overview",
    annotations={
        "title": "Get Library Overview / Home Docs",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def webdev_get_library_overview(params: LibraryOverviewInput) -> str:
    """Get the overview or home documentation page for a supported library.

    Fetches the main entry-point documentation page for the requested library —
    e.g. the GSAP v3 overview, React reference home, R3F introduction, etc.
    Good first stop when you need to understand a library's API surface.

    Args:
        params (LibraryOverviewInput):
            - library (LibraryName): One of gsap, react, r3f, lenis, barba, spline, osmo

    Returns:
        str: Plain-text overview of the library docs, or an error message
    """
    lib = LIBRARIES[params.library.value]
    try:
        content = await _fetch_and_clean(lib["home"])
        header = f"# {lib['name']} — Documentation Overview\nURL: {lib['home']}\n\n"
        return header + content
    except Exception as e:
        return _error(e)


@mcp.tool(
    name="webdev_gsap_get_docs",
    annotations={
        "title": "Get GSAP Section / Plugin Docs",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def webdev_gsap_get_docs(params: GsapSectionInput) -> str:
    """Fetch GSAP documentation for a specific section or plugin.

    Resolves short section names to their canonical GSAP docs URLs.
    For unknown names, attempts to find the page at gsap.com/docs/v3/.

    Args:
        params (GsapSectionInput):
            - section (str): Section/plugin name.
              Known: core, timeline, tween, scrolltrigger, draggable, flip,
              motionpath, scrollto, text, observer, splittext, ease, utils, ticker.
              Unknowns are searched at https://gsap.com/docs/v3/{section}/

    Returns:
        str: Documentation text for the requested GSAP section, or error
    """
    key = params.section.lower().replace(" ", "").replace("-", "").replace(".", "")
    url = GSAP_SECTIONS.get(key)

    if url is None:
        # Try direct path on gsap docs
        url = f"https://gsap.com/docs/v3/GSAP/gsap.{params.section}/"

    try:
        content = await _fetch_and_clean(url)
        header = f"# GSAP — {params.section}\nURL: {url}\n\n"
        return header + content
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            # Fall back to main docs
            fallback = GSAP_SECTIONS["core"]
            try:
                content = await _fetch_and_clean(fallback)
                return (
                    f"Section '{params.section}' not found. "
                    f"Showing core GSAP docs instead.\nURL: {fallback}\n\n"
                    + content
                )
            except Exception as e2:
                return _error(e2)
        return _error(e)
    except Exception as e:
        return _error(e)


@mcp.tool(
    name="webdev_react_get_docs",
    annotations={
        "title": "Get React API Docs",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def webdev_react_get_docs(params: ReactSectionInput) -> str:
    """Fetch React documentation for a specific section, hook, or component.

    Resolves shorthand section names or specific hook/component names to their
    canonical react.dev URLs. Unknown names are looked up under /reference/react/.

    Args:
        params (ReactSectionInput):
            - section (str): Section name or hook/component.
              Known shortcuts: hooks, usestate, useeffect, useref, usecontext,
              usememo, usecallback, usereducer, components, apis, learn, dom.
              Any React API name like 'useTransition', 'Suspense', 'createContext'
              is also accepted.

    Returns:
        str: Documentation text for the requested React section, or error
    """
    key = params.section.lower().replace(" ", "").replace("-", "")
    url = REACT_SECTIONS.get(key)

    if url is None:
        # Try hook/component name directly
        url = f"https://react.dev/reference/react/{params.section}"

    try:
        content = await _fetch_and_clean(url)
        header = f"# React — {params.section}\nURL: {url}\n\n"
        return header + content
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            fallback = REACT_SECTIONS["hooks"]
            try:
                content = await _fetch_and_clean(fallback)
                return (
                    f"'{params.section}' not found. "
                    f"Showing React Hooks reference instead.\nURL: {fallback}\n\n"
                    + content
                )
            except Exception as e2:
                return _error(e2)
        return _error(e)
    except Exception as e:
        return _error(e)


@mcp.tool(
    name="webdev_r3f_get_docs",
    annotations={
        "title": "Get React Three Fiber Docs",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def webdev_r3f_get_docs(params: R3fSectionInput) -> str:
    """Fetch React Three Fiber (R3F) documentation for a specific section.

    Resolves shorthand names to canonical R3F docs URLs, or searches
    r3f.docs.pmnd.rs for unknown section names.

    Args:
        params (R3fSectionInput):
            - section (str): R3F section name.
              Known: intro, canvas, objects, hooks, events, drei,
              performance, typescript, v8.
              Also accepts API names like 'useFrame', 'useThree', 'extend'.

    Returns:
        str: Documentation text for the requested R3F section, or error
    """
    key = params.section.lower().replace(" ", "").replace("-", "")
    url = R3F_SECTIONS.get(key)

    if url is None:
        # Try searching under api/ or tutorials/
        url = f"https://r3f.docs.pmnd.rs/api/{params.section.lower()}"

    try:
        content = await _fetch_and_clean(url)
        header = f"# React Three Fiber — {params.section}\nURL: {url}\n\n"
        return header + content
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            fallback = R3F_SECTIONS["intro"]
            try:
                content = await _fetch_and_clean(fallback)
                return (
                    f"'{params.section}' not found. "
                    f"Showing R3F introduction instead.\nURL: {fallback}\n\n"
                    + content
                )
            except Exception as e2:
                return _error(e2)
        return _error(e)
    except Exception as e:
        return _error(e)


@mcp.tool(
    name="webdev_barba_get_docs",
    annotations={
        "title": "Get Barba.js Docs",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def webdev_barba_get_docs(params: BarbasSectionInput) -> str:
    """Fetch Barba.js documentation for a specific section.

    Resolves shorthand names to canonical barba.js.org doc URLs.

    Args:
        params (BarbasSectionInput):
            - section (str): Barba.js section name.
              Options: intro, install, transitions, hooks, views,
              plugins, router, prefetch.

    Returns:
        str: Documentation text for the requested Barba.js section, or error
    """
    key = params.section.lower().replace(" ", "").replace("-", "")
    url = BARBA_SECTIONS.get(key)

    if url is None:
        url = f"https://barba.js.org/docs/advanced/{params.section.lower()}/"

    try:
        content = await _fetch_and_clean(url)
        header = f"# Barba.js — {params.section}\nURL: {url}\n\n"
        return header + content
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            fallback = BARBA_SECTIONS["intro"]
            try:
                content = await _fetch_and_clean(fallback)
                return (
                    f"'{params.section}' not found. "
                    f"Showing Barba.js intro instead.\nURL: {fallback}\n\n"
                    + content
                )
            except Exception as e2:
                return _error(e2)
        return _error(e)
    except Exception as e:
        return _error(e)


@mcp.tool(
    name="webdev_search_docs",
    annotations={
        "title": "Search Web Dev Docs",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def webdev_search_docs(params: SearchDocsInput) -> str:
    """Search documentation across all (or one) supported web dev library.

    Uses DuckDuckGo's HTML search with site: filtering to find relevant
    documentation pages. Returns a list of matching URLs and titles that
    you can then fetch with webdev_fetch_page.

    Args:
        params (SearchDocsInput):
            - query (str): Search terms (e.g. 'pin sections on scroll', 'useFrame lerp')
            - library (Optional[LibraryName]): Restrict to one library, or omit for all 7

    Returns:
        str: JSON array of {title, url, snippet} objects for matching docs pages
    """
    lib_sites: dict[str, str] = {
        "gsap":   "gsap.com/docs",
        "react":  "react.dev",
        "r3f":    "r3f.docs.pmnd.rs",
        "lenis":  "lenis.darkroom.engineering",
        "barba":  "barba.js.org/docs",
        "spline": "docs.spline.design",
        "osmo":   "osmo.supply",
    }

    if params.library:
        site_filter = f"site:{lib_sites[params.library.value]}"
        search_query = f"{params.query} {site_filter}"
    else:
        sites = " OR ".join(f"site:{s}" for s in lib_sites.values())
        search_query = f"{params.query} ({sites})"

    ddg_url = f"https://html.duckduckgo.com/html/?q={httpx.URL(search_query)}"

    try:
        async with httpx.AsyncClient(follow_redirects=True, headers=_HEADERS) as client:
            resp = await client.get(ddg_url, timeout=15.0)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        results = []

        for result in soup.select(".result")[:10]:
            title_el = result.select_one(".result__title a")
            snippet_el = result.select_one(".result__snippet")
            link_el = result.select_one(".result__url")

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            # DuckDuckGo wraps URLs — extract real URL
            if "uddg=" in href:
                import urllib.parse
                parsed = urllib.parse.urlparse(href)
                qs = urllib.parse.parse_qs(parsed.query)
                href = qs.get("uddg", [href])[0]

            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            display_url = link_el.get_text(strip=True) if link_el else href

            results.append({"title": title, "url": href, "snippet": snippet, "display_url": display_url})

        if not results:
            return json.dumps({"message": f"No results found for '{params.query}'", "results": []})

        return json.dumps({"query": params.query, "count": len(results), "results": results}, indent=2)

    except Exception as e:
        return _error(e)


@mcp.tool(
    name="webdev_gsap_list_sections",
    annotations={
        "title": "List GSAP Documentation Sections",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def webdev_gsap_list_sections() -> str:
    """List all available GSAP documentation sections and their URLs.

    Use this to discover which GSAP plugins and core sections are directly
    accessible via webdev_gsap_get_docs before fetching content.

    Returns:
        str: JSON object mapping section names to their documentation URLs
    """
    return json.dumps(GSAP_SECTIONS, indent=2)


@mcp.tool(
    name="webdev_lenis_get_docs",
    annotations={
        "title": "Get Lenis Smooth Scroll Docs",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def webdev_lenis_get_docs() -> str:
    """Fetch the complete Lenis smooth scroll library documentation.

    Lenis is a lightweight smooth-scroll library. This tool fetches the
    official documentation including installation, options, API methods,
    and integration examples.

    Returns:
        str: Plain-text Lenis documentation content, or error message
    """
    url = "https://lenis.darkroom.engineering/"
    try:
        content = await _fetch_and_clean(url, max_chars=10000)
        header = f"# Lenis — Smooth Scroll Documentation\nURL: {url}\n\n"
        return header + content
    except Exception as e:
        # Fallback to GitHub README
        try:
            gh_url = "https://raw.githubusercontent.com/darkroomengineering/lenis/main/README.md"
            async with httpx.AsyncClient(follow_redirects=True) as client:
                resp = await client.get(gh_url, timeout=15.0)
                resp.raise_for_status()
            header = f"# Lenis — README (GitHub)\nURL: {gh_url}\n\n"
            return header + resp.text[:10000]
        except Exception as e2:
            return _error(e2)


@mcp.tool(
    name="webdev_spline_get_docs",
    annotations={
        "title": "Get Spline 3D Docs",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def webdev_spline_get_docs() -> str:
    """Fetch Spline documentation including the web viewer/runtime API.

    Spline is a 3D design tool for the web. This tool fetches the official
    docs covering the Spline viewer, runtime API for React/vanilla JS,
    events, variables, and export options.

    Returns:
        str: Plain-text Spline documentation content, or error message
    """
    url = "https://docs.spline.design/"
    try:
        content = await _fetch_and_clean(url, max_chars=10000)
        header = f"# Spline — Documentation\nURL: {url}\n\n"
        return header + content
    except Exception as e:
        return _error(e)


@mcp.tool(
    name="webdev_spline_get_runtime_api",
    annotations={
        "title": "Get Spline Runtime/Viewer API",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def webdev_spline_get_runtime_api() -> str:
    """Fetch the Spline runtime API reference (for embedding Spline scenes in web apps).

    Returns documentation on the @splinetool/runtime and @splinetool/react-spline
    packages, including how to load scenes, listen to events, trigger animations,
    control objects, and use variables.

    Returns:
        str: Spline runtime API documentation as plain text, or error message
    """
    urls = [
        "https://docs.spline.design/doc/web-export/docId:VDdQ0rVX-MCiZhcGvnWaR",
        "https://raw.githubusercontent.com/splinetool/react-spline/main/README.md",
    ]

    for url in urls:
        try:
            if url.endswith(".md"):
                async with httpx.AsyncClient(follow_redirects=True, headers=_HEADERS) as client:
                    resp = await client.get(url, timeout=15.0)
                    resp.raise_for_status()
                return f"# Spline Runtime API (GitHub README)\nURL: {url}\n\n{resp.text[:10000]}"
            else:
                content = await _fetch_and_clean(url, max_chars=10000)
                return f"# Spline — Runtime/Viewer API\nURL: {url}\n\n{content}"
        except Exception:
            continue

    return (
        "Could not fetch Spline runtime API docs directly. "
        "Try fetching these URLs manually with webdev_fetch_page:\n"
        "- https://docs.spline.design/\n"
        "- https://github.com/splinetool/react-spline"
    )


@mcp.tool(
    name="webdev_osmo_get_resources",
    annotations={
        "title": "Get Osmo Supply Resources",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def webdev_osmo_get_resources() -> str:
    """Fetch the Osmo Supply homepage to discover available creative web resources.

    Osmo Supply provides components, utilities, and creative code resources
    for web developers. This tool fetches the current catalogue from
    osmo.supply so you can browse and discover what's available.

    Returns:
        str: Osmo Supply resource listing as plain text, or error message
    """
    url = "https://www.osmo.supply/"
    try:
        content = await _fetch_and_clean(url, max_chars=10000)
        header = f"# Osmo Supply — Creative Web Resources\nURL: {url}\n\n"
        return header + content
    except Exception as e:
        return _error(e)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# OAuth routes — added directly onto the MCP app so its lifespan is preserved
# ---------------------------------------------------------------------------
import secrets as _secrets
import time as _time
from starlette.requests import Request as _Request
from starlette.responses import JSONResponse as _JSONResponse, RedirectResponse as _RedirectResponse


@mcp.custom_route("/", methods=["GET"])
async def root(request: _Request) -> _JSONResponse:
    return _JSONResponse({
        "name": "webdev-tools",
        "description": "MCP server for GSAP, React, R3F, Lenis, Barba.js, Spline, Osmo Supply",
        "mcp_endpoint": "/mcp",
    })


@mcp.custom_route("/.well-known/oauth-authorization-server", methods=["GET"])
async def oauth_metadata(request: _Request) -> _JSONResponse:
    base = str(request.base_url).rstrip("/")
    return _JSONResponse({
        "issuer": base,
        "authorization_endpoint": f"{base}/authorize",
        "token_endpoint": f"{base}/token",
        "registration_endpoint": f"{base}/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "code_challenge_methods_supported": ["S256"],
    })


@mcp.custom_route("/register", methods=["POST"])
async def register(request: _Request) -> _JSONResponse:
    """Dynamic client registration (RFC 7591) — accepts any client."""
    body = await request.json()
    client_id = _secrets.token_urlsafe(16)
    client_secret = _secrets.token_urlsafe(32)
    return _JSONResponse({
        "client_id": client_id,
        "client_secret": client_secret,
        "client_name": body.get("client_name", "claude"),
        "redirect_uris": body.get("redirect_uris", []),
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "client_secret_post",
    }, status_code=201)


@mcp.custom_route("/authorize", methods=["GET"])
async def authorize(request: _Request) -> _RedirectResponse:
    """Immediately grant a code — no real login needed for a personal server."""
    params = dict(request.query_params)
    redirect_uri = params.get("redirect_uri", "")
    state = params.get("state", "")
    code = _secrets.token_urlsafe(24)
    sep = "&" if "?" in redirect_uri else "?"
    return _RedirectResponse(f"{redirect_uri}{sep}code={code}&state={state}", status_code=302)


@mcp.custom_route("/token", methods=["POST"])
async def token(request: _Request) -> _JSONResponse:
    """Issue a long-lived bearer token — no verification needed for personal use."""
    tok = _secrets.token_urlsafe(32)
    return _JSONResponse({
        "access_token": tok,
        "token_type": "bearer",
        "expires_in": 3600 * 24 * 365,
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import os
    import uvicorn

    parser = argparse.ArgumentParser(description="Web Dev Tools MCP Server")
    parser.add_argument("--http", action="store_true", help="Run as HTTP server (remote MCP)")
    parser.add_argument("--port", type=int, default=None, help="HTTP port (default: 7771)")
    parser.add_argument("--host", type=str, default=None, help="Host to bind")
    args = parser.parse_args()

    if args.http:
        port = args.port or int(os.environ.get("PORT", 7771))
        host = args.host or ("0.0.0.0" if os.environ.get("PORT") else "127.0.0.1")
        app = mcp.streamable_http_app()
        uvicorn.run(app, host=host, port=port)
    else:
        mcp.run()
