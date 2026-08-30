# CodeCortex v1.2.0 — two indexing bugs that silently drop `.tsx`/`.jsx` files

**RESOLVED in v1.2.1 (2026-08-30)** — both bugs described below are fixed upstream
(commit `e673c20`, "Fix .tsx/.jsx files being silently dropped from the index, set version
1.2.1"), which also independently fixes the same one-extension-per-language bug in
`reindex_file()` and `ParallelIndexer.parse_directory()`. OBEvolve's `tools/codecortex/` clone has
been updated to the `v1.2.1` tag and its local patches discarded — re-verified 2026-08-31: 124
`.tsx` files index cleanly, 0 parse errors. The rest of this document is kept as the original
report for reference.

**Found while indexing a React 19 + TypeScript (Vite) frontend paired with a Python/FastAPI
backend** (OBEvolve, a mixed-language monorepo). Both bugs were re-verified directly against a
fresh `pipx install codecortex==1.2.0` on 2026-08-31 — **still present in the latest published
release**, not something already fixed and just missed in an older local checkout.

**Severity: high.** Neither bug raises an error or a warning — `codecortex index` reports `0
errors` and a plausible-looking file count. The failure is silent: every `.tsx`/`.jsx` file in the
target is simply absent from the graph, which for a typical React+TypeScript project means the
entire component tree (frequently *most* of the frontend) is invisible to `query`/`impact`, with
nothing in the CLI output to suggest anything is wrong.

---

## Bug 1 — file walker only globs one hardcoded extension per language

**File:** `pipeline/context_builder.py`

The parser registry is keyed by a short language handle, not by file extension:

```python
parsers = {"py": PythonParser()}
...
parsers.update({"js": JavaScriptParser(), "ts": TypeScriptParser(), "php": PHPParser()})
```

That `parsers` dict is then used directly as the extension set for the source-file walk:

```python
discovered = list(
    walk_source_files(
        root,
        extensions=parsers.keys(),   # <-- {"py", "js", "ts", "php"} only
        ...
    )
)
```

`TypeScriptParser.extensions` is `[".ts", ".tsx"]` and `JavaScriptParser.extensions` is presumably
`[".js", ".jsx"]` (each parser already declares the full list it can handle), but `parsers.keys()`
only ever yields the bare language handles (`"ts"`, `"js"`), never the second extension each parser
actually supports. The walker globs `*.ts`/`*.js` and never looks for `*.tsx`/`*.jsx` at all.

**Fix applied locally:** build the extension→parser dispatch map from each parser's own
`.extensions` list instead of from the language-handle dict:

```python
ext_to_parser: dict[str, object] = {}
for p in parsers.values():
    for ext in p.extensions:
        ext_to_parser[ext.lstrip(".").lower()] = p

discovered = list(
    walk_source_files(
        root,
        extensions=ext_to_parser.keys(),
        ...
    )
)
```

(and dispatch parsing through `ext_to_parser` rather than `parsers` further down, wherever the
original code assumed one parser per bare language key).

---

## Bug 2 — `.tsx` files are parsed with the plain `typescript` tree-sitter grammar (no JSX)

**File:** `core/parsers/typescript_parser.py`

Even once bug 1 is fixed and `.tsx` files reach the parser, `TypeScriptParser` requests the
`"typescript"` tree-sitter grammar unconditionally, regardless of the file's actual extension:

```python
parser = get_parser("typescript")
```

`tree-sitter-typescript` ships two distinct grammars — `typescript` and `tsx` — because the plain
`typescript` grammar cannot parse JSX syntax. A `.tsx` file full of `<div>...</div>` mostly parses
as `ERROR` nodes under that grammar (tree-sitter doesn't reject invalid syntax outright, it just
produces a badly-formed tree), so even a `.tsx` file that *is* discovered ends up contributing
little or nothing usable to the graph.

**Fix applied locally:** pick the grammar variant by extension:

```python
grammar = "tsx" if file_path.endswith(".tsx") else "typescript"
parser = get_parser(grammar)
```

(`core/parsers/grammars.py` already registers `"tsx"` as a distinct grammar name — this fix uses
what's already available, it doesn't add a new dependency.)

---

## Repro

```bash
mkdir -p repro/src && cd repro
cat > src/Widget.tsx <<'EOF'
export function Widget({ label }: { label: string }) {
  return <div className="widget">{label}</div>
}
EOF
codecortex index . --mode cpg
# Files/nodes reported as if src/Widget.tsx doesn't exist; no error, no warning.
```

## Suggested fix location

Both patches are small (under 20 added lines combined) and self-contained to the two files above
— no new dependencies, no public API change. Happy to open a PR with these exact patches against
`main` if that's useful; they're currently only applied locally as a vendored patch on top of a
`v1.2.0` checkout, tracked in `CLAUDE.md` of the project that found them.
