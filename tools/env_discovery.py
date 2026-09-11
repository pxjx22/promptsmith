#!/usr/bin/env python3
"""
Environment Discovery Tool for Promptsmith
Discovers installed skills, plugins, and MCP servers across Claude Code,
OpenAI Codex, Google Antigravity (Gemini CLI), and OpenCode environments.
Outputs human-readable summaries, structured JSON, or prompt-injectable context blocks.
"""

import argparse
import glob
import json
import os
import re
import sys

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore


def parse_yaml_frontmatter(text: str) -> dict:
    """Extract key-value pairs and multiline strings from YAML frontmatter."""
    data = {}
    if not text.startswith("---"):
        return data
    parts = text.split("---", 2)
    if len(parts) < 3:
        return data
    lines = parts[1].splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            # Check for YAML multiline fold indicators: >, >-, |, |-
            if val in (">", ">-", ">+", "|", "|-", "|+", ""):
                val_lines = []
                i += 1
                while i < len(lines) and (lines[i].startswith("  ") or lines[i].startswith("\t") or not lines[i].strip()):
                    if lines[i].strip():
                        val_lines.append(lines[i].strip())
                    i += 1
                data[key] = " ".join(val_lines)
                continue
            else:
                data[key] = val.strip("\"' ")
        i += 1
    return data


def parse_skill_file(path: str) -> dict:
    """Parse a SKILL.md file to extract name and description."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(8192)
        fm = parse_yaml_frontmatter(content)
        name = fm.get("name")
        desc = fm.get("description")

        if not name:
            parent_name = os.path.basename(os.path.dirname(path))
            name = parent_name if parent_name not in ("skills", "commands") else os.path.basename(os.path.dirname(os.path.dirname(path)))

        if not desc:
            for line in content.splitlines():
                if line.startswith("# "):
                    desc = line[2:].strip()
                    break
        return {
            "name": name or os.path.basename(os.path.dirname(path)),
            "description": desc or "No description provided.",
            "path": path,
        }
    except Exception as e:
        return {
            "name": os.path.basename(os.path.dirname(path)),
            "description": f"Error reading skill: {e}",
            "path": path,
        }


def scan_skills(project_dir: str = None) -> list[dict]:
    """Scan and deduplicate all installed skills across AI harnesses and project workspace."""
    home = os.path.expanduser("~")
    by_name = {}

    scan_targets = [
        # Harness, category, glob pattern
        ("gemini", "plugin", os.path.join(home, ".gemini", "config", "plugins", "*", "skills", "*", "SKILL.md")),
        ("gemini", "plugin", os.path.join(home, ".gemini", "config", "plugins", "*", "skills", "SKILL.md")),
        ("gemini", "user", os.path.join(home, ".gemini", "config", "skills", "*", "SKILL.md")),
        ("gemini", "user", os.path.join(home, ".gemini", "skills", "*", "SKILL.md")),
        ("gemini", "builtin", os.path.join(home, ".gemini", "antigravity-cli", "builtin", "skills", "*", "SKILL.md")),
        ("claude", "user", os.path.join(home, ".claude", "skills", "*", "SKILL.md")),
        ("codex", "user", os.path.join(home, ".codex", "skills", "*", "SKILL.md")),
        ("opencode", "user", os.path.join(home, ".config", "opencode", "skills", "*", "SKILL.md")),
        ("opencode", "user", os.path.join(home, ".opencode", "skills", "*", "SKILL.md")),
    ]

    if project_dir and os.path.isdir(project_dir):
        scan_targets.extend([
            ("gemini", "project", os.path.join(project_dir, ".gemini", "skills", "*", "SKILL.md")),
            ("gemini", "project", os.path.join(project_dir, ".gemini", "config", "skills", "*", "SKILL.md")),
            ("claude", "project", os.path.join(project_dir, ".claude", "skills", "*", "SKILL.md")),
            ("codex", "project", os.path.join(project_dir, ".codex", "skills", "*", "SKILL.md")),
            ("opencode", "project", os.path.join(project_dir, ".config", "opencode", "skills", "*", "SKILL.md")),
            ("opencode", "project", os.path.join(project_dir, ".opencode", "skills", "*", "SKILL.md")),
        ])

    for harness, category, pattern in scan_targets:
        for file_path in glob.glob(pattern):
            info = parse_skill_file(file_path)
            s_name = info["name"]
            if not s_name:
                continue

            if s_name not in by_name:
                by_name[s_name] = {
                    "type": "skill",
                    "name": s_name,
                    "description": info["description"],
                    "harnesses": [harness],
                    "categories": [category],
                    "paths": [file_path],
                }
            else:
                entry = by_name[s_name]
                if harness not in entry["harnesses"]:
                    entry["harnesses"].append(harness)
                if category not in entry["categories"]:
                    entry["categories"].append(category)
                if file_path not in entry["paths"]:
                    entry["paths"].append(file_path)
                # If current description is better/longer than previous, use it
                if len(info["description"]) > len(entry.get("description", "")):
                    entry["description"] = info["description"]

    skills = list(by_name.values())
    skills.sort(key=lambda s: s["name"].lower())
    return skills


def scan_plugins(project_dir: str = None) -> list[dict]:
    """Scan all installed plugins across AI harnesses."""
    home = os.path.expanduser("~")
    plugins_by_name = {}

    # 1. Gemini plugins
    gemini_plugins_dir = os.path.join(home, ".gemini", "config", "plugins")
    if os.path.isdir(gemini_plugins_dir):
        for entry in os.listdir(gemini_plugins_dir):
            p_dir = os.path.join(gemini_plugins_dir, entry)
            if os.path.isdir(p_dir):
                manifest_path = os.path.join(p_dir, "plugin.json")
                name = entry
                desc = "Gemini CLI / Antigravity plugin"
                version = None
                if os.path.isfile(manifest_path):
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            m_data = json.load(f)
                            name = m_data.get("name", entry)
                            desc = m_data.get("description", desc)
                            version = m_data.get("version")
                    except Exception:
                        pass

                contained_skills = []
                for sk_file in glob.glob(os.path.join(p_dir, "skills", "**", "SKILL.md"), recursive=True):
                    sk_info = parse_skill_file(sk_file)
                    contained_skills.append(sk_info["name"])

                plugins_by_name[name] = {
                    "type": "plugin",
                    "name": name,
                    "description": desc,
                    "harnesses": ["gemini"],
                    "version": version,
                    "enabled": True,
                    "skills": contained_skills,
                    "path": p_dir,
                }

    # 2. Codex plugins from config.toml
    codex_toml = os.path.join(home, ".codex", "config.toml")
    if os.path.isfile(codex_toml) and tomllib:
        try:
            with open(codex_toml, "rb") as f:
                codex_data = tomllib.load(f)
                configured_plugins = codex_data.get("plugins", {})
                if isinstance(configured_plugins, dict):
                    for plug_id, plug_conf in configured_plugins.items():
                        is_enabled = plug_conf.get("enabled", True) if isinstance(plug_conf, dict) else True
                        if plug_id in plugins_by_name:
                            if "codex" not in plugins_by_name[plug_id]["harnesses"]:
                                plugins_by_name[plug_id]["harnesses"].append("codex")
                        else:
                            plugins_by_name[plug_id] = {
                                "type": "plugin",
                                "name": plug_id,
                                "description": f"Codex plugin ({'enabled' if is_enabled else 'disabled'})",
                                "harnesses": ["codex"],
                                "version": None,
                                "enabled": is_enabled,
                                "skills": [],
                                "path": codex_toml,
                            }
        except Exception:
            pass

    # 3. OpenCode plugins
    opencode_plugins_dir = os.path.join(home, ".config", "opencode", "plugins")
    if os.path.isdir(opencode_plugins_dir):
        for entry in os.listdir(opencode_plugins_dir):
            if entry.endswith((".js", ".ts", ".json")):
                p_path = os.path.join(opencode_plugins_dir, entry)
                name = os.path.splitext(entry)[0] if entry != "package.json" else "package-plugins"
                if name in plugins_by_name:
                    if "opencode" not in plugins_by_name[name]["harnesses"]:
                        plugins_by_name[name]["harnesses"].append("opencode")
                else:
                    plugins_by_name[name] = {
                        "type": "plugin",
                        "name": name,
                        "description": f"OpenCode plugin script ({entry})",
                        "harnesses": ["opencode"],
                        "version": None,
                        "enabled": True,
                        "skills": [],
                        "path": p_path,
                    }

    # 4. Claude Code plugins
    claude_settings_path = os.path.join(home, ".claude", "settings.json")
    if os.path.isfile(claude_settings_path):
        try:
            with open(claude_settings_path, "r", encoding="utf-8") as f:
                c_data = json.load(f)
                c_plugins = c_data.get("plugins", {})
                if isinstance(c_plugins, dict):
                    for p_name, p_val in c_plugins.items():
                        if p_name in plugins_by_name:
                            if "claude" not in plugins_by_name[p_name]["harnesses"]:
                                plugins_by_name[p_name]["harnesses"].append("claude")
                        else:
                            plugins_by_name[p_name] = {
                                "type": "plugin",
                                "name": p_name,
                                "description": "Claude Code plugin",
                                "harnesses": ["claude"],
                                "version": None,
                                "enabled": bool(p_val) if isinstance(p_val, bool) else True,
                                "skills": [],
                                "path": claude_settings_path,
                            }
        except Exception:
            pass

    plugins = list(plugins_by_name.values())
    plugins.sort(key=lambda p: p["name"].lower())
    return plugins


def scan_mcps(project_dir: str = None) -> list[dict]:
    """Scan and deduplicate configured and active Model Context Protocol (MCP) servers."""
    home = os.path.expanduser("~")
    mcps_by_name = {}

    # 1. Gemini / Antigravity active MCP directory
    gemini_mcp_dir = os.path.join(home, ".gemini", "antigravity-cli", "mcp")
    if os.path.isdir(gemini_mcp_dir):
        for server_name in sorted(os.listdir(gemini_mcp_dir)):
            s_dir = os.path.join(gemini_mcp_dir, server_name)
            if os.path.isdir(s_dir):
                tools = []
                doc_summary = None
                instr_file = os.path.join(s_dir, "instructions.md")
                if os.path.isfile(instr_file):
                    try:
                        with open(instr_file, "r", encoding="utf-8") as f:
                            doc_summary = f.readline().strip().lstrip("# ")
                    except Exception:
                        pass

                for j_file in sorted(os.listdir(s_dir)):
                    if j_file.endswith(".json"):
                        tool_path = os.path.join(s_dir, j_file)
                        tool_name = j_file[:-5]
                        tool_desc = ""
                        try:
                            with open(tool_path, "r", encoding="utf-8") as f:
                                t_data = json.load(f)
                                tool_name = t_data.get("name", tool_name)
                                tool_desc = t_data.get("description", "")
                        except Exception:
                            pass
                        tools.append({"name": tool_name, "description": tool_desc})

                desc = doc_summary or (f"MCP server with {len(tools)} tool(s)" if tools else "MCP server")
                mcps_by_name[server_name] = {
                    "type": "mcp",
                    "name": server_name,
                    "description": desc,
                    "harnesses": ["gemini"],
                    "enabled": True,
                    "tools": [t["name"] for t in tools],
                    "tool_details": tools,
                    "sources": [s_dir],
                }

    # 2. Gemini settings.json
    gemini_settings = os.path.join(home, ".gemini", "settings.json")
    if os.path.isfile(gemini_settings):
        try:
            with open(gemini_settings, "r", encoding="utf-8") as f:
                g_data = json.load(f)
                servers = g_data.get("mcpServers", {})
                for s_name in servers.keys():
                    if s_name in mcps_by_name:
                        if "gemini" not in mcps_by_name[s_name]["harnesses"]:
                            mcps_by_name[s_name]["harnesses"].append("gemini")
                    else:
                        mcps_by_name[s_name] = {
                            "type": "mcp",
                            "name": s_name,
                            "description": "Configured Gemini MCP server",
                            "harnesses": ["gemini"],
                            "enabled": True,
                            "tools": [],
                            "tool_details": [],
                            "sources": [gemini_settings],
                        }
        except Exception:
            pass

    # 3. Codex config.toml mcp_servers
    codex_toml = os.path.join(home, ".codex", "config.toml")
    if os.path.isfile(codex_toml) and tomllib:
        try:
            with open(codex_toml, "rb") as f:
                data = tomllib.load(f)
                c_servers = data.get("mcp_servers", {})
                for s_name, s_conf in c_servers.items():
                    is_enabled = s_conf.get("enabled", True) if isinstance(s_conf, dict) else True
                    desc = "Codex MCP server"
                    if isinstance(s_conf, dict):
                        if "command" in s_conf:
                            desc = f"Command: {s_conf['command']} {' '.join(s_conf.get('args', []))}".strip()
                        elif "url" in s_conf:
                            desc = f"Endpoint: {s_conf['url']}"

                    if s_name in mcps_by_name:
                        entry = mcps_by_name[s_name]
                        if "codex" not in entry["harnesses"]:
                            entry["harnesses"].append("codex")
                        if codex_toml not in entry["sources"]:
                            entry["sources"].append(codex_toml)
                    else:
                        mcps_by_name[s_name] = {
                            "type": "mcp",
                            "name": s_name,
                            "description": desc,
                            "harnesses": ["codex"],
                            "enabled": is_enabled,
                            "tools": [],
                            "tool_details": [],
                            "sources": [codex_toml],
                        }
        except Exception:
            pass

    # 4. Claude settings and mcp configs
    claude_mcp_files = [
        os.path.join(home, ".claude", "settings.json"),
        os.path.join(home, ".claude", "settings.local.json"),
        os.path.join(home, ".claude.json"),
    ]
    if project_dir:
        claude_mcp_files.extend([
            os.path.join(project_dir, ".claude", "mcp.json"),
            os.path.join(project_dir, "mcp.json"),
            os.path.join(project_dir, ".mcp.json"),
        ])

    for cf in claude_mcp_files:
        if os.path.isfile(cf):
            try:
                with open(cf, "r", encoding="utf-8") as f:
                    c_data = json.load(f)
                    servers = c_data.get("mcpServers", {})
                    for s_name, s_conf in servers.items():
                        desc = "Claude MCP server"
                        if isinstance(s_conf, dict):
                            if "command" in s_conf:
                                desc = f"Command: {s_conf['command']} {' '.join(s_conf.get('args', []))}".strip()
                            elif "url" in s_conf:
                                desc = f"Endpoint: {s_conf['url']}"

                        if s_name in mcps_by_name:
                            entry = mcps_by_name[s_name]
                            if "claude" not in entry["harnesses"]:
                                entry["harnesses"].append("claude")
                            if cf not in entry["sources"]:
                                entry["sources"].append(cf)
                        else:
                            mcps_by_name[s_name] = {
                                "type": "mcp",
                                "name": s_name,
                                "description": desc,
                                "harnesses": ["claude"],
                                "enabled": True,
                                "tools": [],
                                "tool_details": [],
                                "sources": [cf],
                            }
            except Exception:
                pass

    mcps = list(mcps_by_name.values())
    mcps.sort(key=lambda m: m["name"].lower())
    return mcps


def scan_environment(harness: str = None, item_type: str = None, project_dir: str = None) -> dict:
    """Aggregate all scanned environment components with optional filtering."""
    proj = project_dir or os.getcwd()
    skills = scan_skills(project_dir=proj)
    plugins = scan_plugins(project_dir=proj)
    mcps = scan_mcps(project_dir=proj)

    # Filter by harness if specified
    if harness and harness.lower() not in ("all", "*"):
        target_harness = harness.lower()
        skills = [s for s in skills if target_harness in [h.lower() for h in s["harnesses"]]]
        plugins = [p for p in plugins if target_harness in [h.lower() for h in p["harnesses"]]]
        mcps = [m for m in mcps if target_harness in [h.lower() for h in m["harnesses"]]]

    # Filter by item_type if specified
    if item_type and item_type.lower() not in ("all", "*"):
        t = item_type.lower()
        if t in ("skill", "skills"):
            plugins, mcps = [], []
        elif t in ("plugin", "plugins"):
            skills, mcps = [], []
        elif t in ("mcp", "mcps", "server", "servers"):
            skills, plugins = [], []

    return {
        "skills": skills,
        "plugins": plugins,
        "mcps": mcps,
        "counts": {
            "skills": len(skills),
            "plugins": len(plugins),
            "mcps": len(mcps),
            "total": len(skills) + len(plugins) + len(mcps),
        },
    }


def filter_by_query(data: dict, query: str) -> dict:
    """Filter scanned items by a keyword query across name, description, and tools."""
    if not query:
        return data
    q = query.lower()

    def matches(item: dict) -> bool:
        if q in item["name"].lower():
            return True
        if q in item.get("description", "").lower():
            return True
        for tool in item.get("tools", []):
            if q in tool.lower():
                return True
        for sk in item.get("skills", []):
            if q in sk.lower():
                return True
        for cat in item.get("categories", []):
            if q in cat.lower():
                return True
        return False

    filtered_skills = [s for s in data["skills"] if matches(s)]
    filtered_plugins = [p for p in data["plugins"] if matches(p)]
    filtered_mcps = [m for m in data["mcps"] if matches(m)]

    return {
        "skills": filtered_skills,
        "plugins": filtered_plugins,
        "mcps": filtered_mcps,
        "counts": {
            "skills": len(filtered_skills),
            "plugins": len(filtered_plugins),
            "mcps": len(filtered_mcps),
            "total": len(filtered_skills) + len(filtered_plugins) + len(filtered_mcps),
        },
    }


def format_summary(data: dict, show_tools: bool = True) -> str:
    """Format scanned capabilities as a readable terminal summary."""
    lines = []
    lines.append("================================================================================")
    lines.append("PROMPTSMITH ENVIRONMENT CAPABILITIES DISCOVERY")
    lines.append("================================================================================")
    counts = data["counts"]
    lines.append(f"Total Discovered: {counts['total']} ({counts['skills']} skills, {counts['plugins']} plugins, {counts['mcps']} MCP servers)")
    lines.append("")

    # 1. MCP Servers
    if data["mcps"]:
        lines.append(f"--- MCP Servers ({len(data['mcps'])}) ---")
        for m in data["mcps"]:
            harness_tags = ", ".join(m["harnesses"])
            status = "enabled" if m.get("enabled", True) else "disabled"
            status_str = f" [{status}]" if not m.get("enabled", True) else ""
            lines.append(f"  • {m['name']} ({harness_tags}){status_str}")
            desc = m.get("description", "")
            if desc:
                lines.append(f"    Description: {desc}")
            if show_tools and m.get("tools"):
                tools_str = ", ".join(m["tools"])
                lines.append(f"    Tools ({len(m['tools'])}): {tools_str}")
        lines.append("")

    # 2. Plugins
    if data["plugins"]:
        lines.append(f"--- Plugins ({len(data['plugins'])}) ---")
        for p in data["plugins"]:
            harness_tags = ", ".join(p["harnesses"])
            status = "enabled" if p.get("enabled", True) else "disabled"
            status_str = f" [{status}]" if not p.get("enabled", True) else ""
            lines.append(f"  • {p['name']} ({harness_tags}){status_str}")
            desc = p.get("description", "")
            if desc:
                lines.append(f"    Description: {desc}")
            if p.get("skills"):
                lines.append(f"    Provided skills: {', '.join(p['skills'])}")
        lines.append("")

    # 3. Skills
    if data["skills"]:
        lines.append(f"--- Skills ({len(data['skills'])}) ---")
        for s in data["skills"]:
            harness_tags = ", ".join(s["harnesses"])
            cats = f" [{', '.join(s.get('categories', []))}]" if s.get("categories") else ""
            lines.append(f"  • {s['name']} ({harness_tags}){cats}")
            desc = s.get("description", "")
            if desc:
                desc_clean = desc.replace("\n", " ").strip()
                if len(desc_clean) > 130:
                    desc_clean = desc_clean[:127] + "..."
                lines.append(f"    {desc_clean}")
        lines.append("")

    lines.append("================================================================================")
    return "\n".join(lines)


def format_prompt_context(data: dict, max_items: int = 40, show_tools: bool = True) -> str:
    """
    Format discovered capabilities into an XML block ready for prompt injection.
    Placed in <context> of a coding brief or system prompt so the executing agent
    knows what skills, plugins, and MCPs are available to call.
    """
    lines = []
    lines.append("<available_environment_capabilities>")
    lines.append("The following skills, plugins, and MCP servers are installed in the host environment.")
    lines.append("Reference or invoke them directly where relevant to accomplish the task:")

    has_content = False

    if data["skills"]:
        has_content = True
        lines.append("")
        lines.append("- Skills:")
        for s in data["skills"][:max_items]:
            desc = s.get("description", "").replace("\n", " ").strip()
            if len(desc) > 140:
                desc = desc[:137] + "..."
            harnesses = "/".join(s["harnesses"])
            lines.append(f"  - `{s['name']}` ({harnesses}): {desc}")

    if data["mcps"]:
        has_content = True
        lines.append("")
        lines.append("- MCP Servers & Tools:")
        for m in data["mcps"][:max_items]:
            if not m.get("enabled", True):
                continue
            harnesses = "/".join(m["harnesses"])
            desc = m.get("description", "").replace("\n", " ").strip()
            tool_list = m.get("tools", [])
            tool_suffix = f" (tools: {', '.join(tool_list[:8])}{'...' if len(tool_list) > 8 else ''})" if show_tools and tool_list else ""
            lines.append(f"  - `{m['name']}` ({harnesses}){tool_suffix}: {desc}")

    if data["plugins"]:
        has_content = True
        lines.append("")
        lines.append("- Plugins:")
        for p in data["plugins"][:max_items]:
            if not p.get("enabled", True):
                continue
            harnesses = "/".join(p["harnesses"])
            desc = p.get("description", "").replace("\n", " ").strip()
            lines.append(f"  - `{p['name']}` ({harnesses}): {desc}")

    if not has_content:
        lines.append("No active skills, plugins, or MCP servers detected.")

    lines.append("</available_environment_capabilities>")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Promptsmith Environment Discovery: check installed skills, plugins, and MCP servers"
    )
    parser.add_argument(
        "--harness",
        default="all",
        choices=["all", "claude", "codex", "gemini", "opencode", "project"],
        help="Filter by AI harness (default: all)",
    )
    parser.add_argument(
        "--type",
        default="all",
        choices=["all", "skill", "plugin", "mcp"],
        help="Filter by capability type (default: all)",
    )
    parser.add_argument(
        "-q", "--query", "--filter",
        dest="query",
        help="Search filter matching name, description, or tools",
    )
    parser.add_argument(
        "--format",
        default="summary",
        choices=["summary", "prompt", "json"],
        help="Output format: summary (readable), prompt (XML injection block), json (data)",
    )
    parser.add_argument(
        "--project-dir",
        default=None,
        help="Target project directory to inspect for local configurations (default: current working directory)",
    )
    parser.add_argument(
        "--no-tools",
        action="store_true",
        help="Omit detailed tool names from MCP server entries",
    )

    args = parser.parse_args()

    data = scan_environment(
        harness=args.harness,
        item_type=args.type,
        project_dir=args.project_dir,
    )

    if args.query:
        data = filter_by_query(data, args.query)

    if args.format == "json":
        print(json.dumps(data, indent=2))
    elif args.format == "prompt":
        print(format_prompt_context(data, show_tools=not args.no_tools))
    else:
        print(format_summary(data, show_tools=not args.no_tools))


if __name__ == "__main__":
    main()
