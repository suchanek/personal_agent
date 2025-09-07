import pathlib
import sys

try:
    import tomllib  # py311+
except ModuleNotFoundError:
    import tomli as tomllib  # py310/py39 fallback

p = pathlib.Path("pyproject.toml")
b = p.read_bytes()
cfg = tomllib.loads(b.decode())


def is_dict(x):
    return isinstance(x, dict)


problems = []

# 1) Core metadata that must be strings or list[str]
meta_checks = [
    ("tool.poetry.name", str),
    ("tool.poetry.version", str),
    ("tool.poetry.description", str),
    ("tool.poetry.license", (str, type(None))),
    ("tool.poetry.readme", (str, list, type(None))),
    ("tool.poetry.homepage", (str, type(None))),
    ("tool.poetry.repository", (str, type(None))),
    ("tool.poetry.documentation", (str, type(None))),
    ("tool.poetry.authors", list),
    ("tool.poetry.maintainers", (list, type(None))),
    ("tool.poetry.keywords", (list, type(None))),
    ("tool.poetry.classifiers", (list, type(None))),
    ("build-system.requires", list),
    ("build-system.build-backend", str),
]


def get(d, path):
    cur = d
    for k in path.split("."):
        if k not in cur:
            return None, False
        cur = cur[k]
    return cur, True


for path, typ in meta_checks:
    v, ok = get(cfg, path)
    if ok and not isinstance(v, typ):
        problems.append((path, f"expected {typ}, got {type(v)}"))


# 2) Dependencies: each value can be str OR table with specific scalar/list fields
def check_deps_section(section_name, deps):
    if not isinstance(deps, dict):
        problems.append((section_name, f"expected a table, got {type(deps)}"))
        return
    for pkg, val in deps.items():
        if isinstance(val, str):
            continue
        if not isinstance(val, dict):
            problems.append(
                (f"{section_name}.{pkg}", f"expected str or table, got {type(val)}")
            )
            continue
        # Allowed keys and types
        scalar_keys = {"version", "python", "source", "branch", "tag", "rev", "markers"}
        pathlike_keys = {"git", "url", "path"}
        bool_keys = {"optional"}
        list_keys = {"extras", "allow-prereleases"}

        for k, v in val.items():
            if k in scalar_keys and not isinstance(v, str):
                problems.append(
                    (f"{section_name}.{pkg}.{k}", f"expected str, got {type(v)}")
                )
            elif k in pathlike_keys and not isinstance(v, str):
                problems.append(
                    (f"{section_name}.{pkg}.{k}", f"expected str, got {type(v)}")
                )
            elif k in bool_keys and not isinstance(v, bool):
                problems.append(
                    (f"{section_name}.{pkg}.{k}", f"expected bool, got {type(v)}")
                )
            elif k in list_keys and not isinstance(v, list):
                problems.append(
                    (f"{section_name}.{pkg}.{k}", f"expected list, got {type(v)}")
                )
            # common mistake: dict for extras/markers/tag
            if k == "extras" and isinstance(v, dict):
                problems.append(
                    (f"{section_name}.{pkg}.extras", "must be list[str], not dict")
                )
            if k == "markers" and isinstance(v, dict):
                problems.append(
                    (
                        f"{section_name}.{pkg}.markers",
                        "must be a PEP 508 string, not dict",
                    )
                )
            if k == "tag" and isinstance(v, dict):
                problems.append(
                    (f"{section_name}.{pkg}.tag", "must be a string, not dict")
                )


# main deps
deps, ok = get(cfg, "tool.poetry.dependencies")
if ok:
    check_deps_section("tool.poetry.dependencies", deps)

# group deps
grp, ok = get(cfg, "tool.poetry.group")
if ok and isinstance(grp, dict):
    for gname, gval in grp.items():
        if isinstance(gval, dict) and "dependencies" in gval:
            check_deps_section(
                f"tool.poetry.group.{gname}.dependencies", gval["dependencies"]
            )

# plugins: values must be strings (entry points), not dicts
plug, ok = get(cfg, "tool.poetry.plugins")
if ok and isinstance(plug, dict):
    for ep_group, entries in plug.items():
        if not isinstance(entries, dict):
            problems.append(
                (
                    f"tool.poetry.plugins.{ep_group}",
                    f"expected table, got {type(entries)}",
                )
            )
            continue
        for name, target in entries.items():
            if not isinstance(target, str):
                problems.append(
                    (
                        f"tool.poetry.plugins.{ep_group}.{name}",
                        "must be 'pkg.module:Obj' string",
                    )
                )

# scripts: name -> "pkg.module:func" string
scripts, ok = get(cfg, "tool.poetry.scripts")
if ok and isinstance(scripts, dict):
    for name, target in scripts.items():
        if not isinstance(target, str):
            problems.append(
                (f"tool.poetry.scripts.{name}", "must be a string entry point")
            )

# URLs: key -> string
urls, ok = get(cfg, "tool.poetry.urls")
if ok and isinstance(urls, dict):
    for k, v in urls.items():
        if not isinstance(v, str):
            problems.append((f"tool.poetry.urls.{k}", "must be a string URL"))

# include/exclude may be list[str] or list[tables], flag dict-at-top-level
for key in ("tool.poetry.include", "tool.poetry.exclude"):
    v, ok = get(cfg, key)
    if ok and not isinstance(v, list):
        problems.append((key, f"expected list, got {type(v)}"))

if problems:
    print("Found potential schema/type issues:")
    for path, msg in problems:
        print(f" - {path}: {msg}")
    sys.exit(1)
else:
    print("No obvious schema/type issues found in common trouble spots.")
