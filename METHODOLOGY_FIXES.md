# Ticket: Make Report Methodology 100% Data-Driven, DRY, Config-Only

## Goal
Render the Methodology section using the exact run inputs (languages, locations, contexts, models, token limits, command) with zero hardcoded literals or duplicated logic, so reports stay accurate for any config/property.

## Why
- `core/report_header.py:24-113` hardcodes language fallback (`lang = force_language or "en"`), token limits (`2000`), and canned CLI examples without `--config`/providers.
- Location/context logic is reimplemented instead of reusing `PromptGenerator` helpers, risking drift.
- Methodology shows a single system context and location even for mixed-language runs; Check A/B text omits actual brand/domain matching rules.
- `generate_report` in `core/runner.py` always calls `get_system_context("de")`, decoupled from actual packets.

## Scope
Fix the Methodology rendering pipeline to pull everything from run artifacts/config, eliminate duplicated logic, and align text with real parsing behavior.

---

## SPECIFIC CHANGES REQUIRED

### 1. Store Original CLI Command in RunState

**File**: `core/run_state.py`
**Line**: 12-22 (RunState dataclass)

**Problem**: No field exists to capture the original CLI command used to start the run.

**Solution**: Add `cli_command: str = ""` field to `RunState` dataclass:
```python
@dataclass
class RunState:
    run_id: str
    domain: str
    max_queries: int
    started_at: str
    completed_queries: List[int]
    total_queries: int
    status: str
    providers: List[str] = field(default_factory=lambda: config.default_providers)
    completed_providers: Dict[str, List[str]] = field(default_factory=dict)
    cli_command: str = ""  # NEW: Store original command
```

---

### 2. Capture CLI Command at Startup

**File**: `run.py`
**Lines**: 91-94 (main function)

**Problem**: The original `sys.argv` is never persisted.

**Solution**: Capture and store the command when creating a new run:
```python
def main() -> int:
    global _desktop_flag
    args = parse_args()
    _desktop_flag = args.desktop

    # Capture original command for methodology
    cli_command = "python " + " ".join(sys.argv)
    # ... pass cli_command to run_new() and run_add_to_existing()
```

**Also update** `run_new()` and `run_add_to_existing()` in `core/runner.py` to accept and save `cli_command` parameter.

---

### 3. Fix Hardcoded Token Limit for Prompt Generation

**File**: `core/report_header.py`
**Line**: 70

**Problem**: Shows `2000` tokens but actual limit in `core/llm_openai.py:75` is `8000`:
```python
max_completion_tokens=8000  # llm_openai.py line 75
```

**Current (WRONG)**:
```python
<tr><td>Prompt Generation</td><td>{config.openai_prompt_model}</td><td>-</td><td>2000</td></tr>
```

**Solution**: Either:
- A) Add `max_output_tokens_prompt` to config (preferred for DRY)
- B) Or use constant: `{config.max_output_tokens_prompt or 8000}`

---

### 4. Fix CLI Command Display (Use Real Command)

**File**: `core/report_header.py`
**Lines**: 52-65

**Problem**: Shows canned generic command without `--config`, providers, or custom name:
```python
python run.py --max-queries {max_queries}  # WRONG - missing critical args
```

**Solution**: Accept and display `cli_command` from RunState:
```python
def render_methodology(domain: str, ctx: str, run_id: str = "",
                       offset: int = 0, max_queries: int = 0,
                       cli_command: str = "") -> str:  # NEW param
    # ...
    actual_cmd = cli_command or f"python run.py --config <config> --max-queries {max_queries}"
    # Display actual_cmd in the "This run" box
```

---

### 5. Fix Check A Description (Match Actual Parser Logic)

**File**: `core/report_header.py`
**Line**: 106

**Problem**: Description doesn't match `check_answer_visibility()` in `core/relevancy_parser.py:29-40`:
```python
# ACTUAL LOGIC (relevancy_parser.py:29-40):
def check_answer_visibility(answer_text, domain, domain_base, brand_names):
    text_lower = answer_text.lower()
    domain_lower = domain.lower().replace("www.", "")
    if domain_lower in text_lower:
        return True
    for brand in brand_names:
        if brand.lower() in text_lower:
            return True
    return False
```

**Current (INCOMPLETE)**:
```html
<td>Case-insensitive search for "{domain}" in the full answer text</td>
```

**Solution**:
```html
<td>Case-insensitive search for domain (<code>{domain}</code>) OR any brand name
(<code>{', '.join(config.brand_names)}</code>) in the full answer text</td>
```

---

### 6. Fix Check B Description (Match Actual Parser Logic)

**File**: `core/report_header.py`
**Line**: 107

**Problem**: Description doesn't mention subdomain matching in `check_domain_presence()` from `core/relevancy_parser.py:68-84`:
```python
# ACTUAL LOGIC (relevancy_parser.py:74-78):
def _is_match(candidate: str) -> bool:
    cand = candidate.replace("www.", "").lower()
    if config.domain_match_strategy == "exact":
        return cand == target_clean
    return cand == target_clean or cand.endswith(f".{target_clean}")  # subdomain match!
```

**Current (INCOMPLETE)**:
```html
<td>Parse JSON domain list, find position of {domain} (rank 1-10 or not found)</td>
```

**Solution**:
```html
<td>Parse JSON domain list, find position of <code>{domain}</code> using {config.domain_match_strategy}
matching (exact match or subdomain match like <code>sub.{domain}</code>). Rank 1-10 or not found.</td>
```

---

### 7. Fix Language/Context for Mixed-Language Runs

**File**: `core/report_header.py`
**Lines**: 28-41

**Problem**: Always defaults to `lang = config.force_language or "en"`, ignoring actual packet languages.

**Also File**: `core/runner.py`
**Line**: 222

**Problem**: Always uses hardcoded `"de"`:
```python
ctx = PromptGenerator().get_system_context("de")  # ALWAYS "de"!
```

**Solution - Part A** (report_header.py): Accept languages/contexts from packets:
```python
def render_methodology(domain: str, contexts: dict[str, str], run_id: str = "",
                       offset: int = 0, max_queries: int = 0,
                       languages_used: list[str] = None,
                       cli_command: str = "") -> str:
    # Display ALL languages used with their contexts
    langs = languages_used or [config.force_language or config.default_language or "en"]
    # For each lang, show its system context
```

**Solution - Part B** (runner.py): Extract actual languages from packets:
```python
def generate_report(openai_res, gemini_res, run_id, ...):
    # Get languages from cached packets
    cache = PromptCache(config.base_dir / "state" / "prompts")
    packets = cache.load(run_id)
    languages_used = list(set(p.language_code for p in packets))

    # Build contexts for all languages
    gen = PromptGenerator()
    contexts = {lang: gen.get_system_context(lang) for lang in languages_used}
```

---

### 8. DRY Location Clause Building

**File**: `core/report_header.py`
**Lines**: 29-41

**Problem**: Duplicates `PromptGenerator._location_parts()` logic from `core/prompt_generator.py:134-138`:
```python
# prompt_generator.py (THE SOURCE OF TRUTH):
def _location_parts(self, language: str) -> tuple[str, str]:
    city = (self.city_de if language == "de" else self.city_en).strip()
    country = (self.country_de if language == "de" else self.country_en).strip()
    return city, country
```

**Current (DUPLICATED in report_header.py)**:
```python
city = city_de if lang == "de" else city_en
country = country_de if lang == "de" else country_en
location_phrase = city.strip() or country
location_clause = f"{city}, {country}" if city and country...
```

**Solution**: Use `PromptGenerator` directly:
```python
from .prompt_generator import PromptGenerator

def render_methodology(...):
    gen = PromptGenerator()
    for lang in languages_used:
        location = gen.get_location_string(lang)  # Already exists!
        ctx = gen.get_system_context(lang)
```

---

### 9. Pass Run Metadata to Report Generator

**File**: `core/runner.py`
**Function**: `generate_report()` (line 215)

**Problem**: Doesn't pass packet-derived data to report generator.

**Solution**: Load packets and pass extracted metadata:
```python
def generate_report(openai_res, gemini_res, run_id, offset=0, max_queries=0,
                    desktop=False, output_name=None, cli_command="") -> int:
    # Load packets for language extraction
    cache = PromptCache(config.base_dir / "state" / "prompts")
    packets = cache.load(run_id)

    # Extract actual languages used
    languages_used = sorted(set(p.language_code for p in packets)) if packets else ["de"]

    # Build per-language contexts
    gen = PromptGenerator()
    contexts = {lang: gen.get_system_context(lang) for lang in languages_used}

    # Pass to report generator
    report_gen = ReportGenerator(
        config.domain,
        run_id=run_id,
        offset=offset,
        max_queries=max_queries,
        languages_used=languages_used,
        contexts=contexts,
        cli_command=cli_command
    )
```

---

## IMPLEMENTATION CHECKLIST

- [ ] **run_state.py**: Add `cli_command: str = ""` field to RunState
- [ ] **run.py**: Capture `sys.argv` and pass to runner functions
- [ ] **runner.py**: Accept `cli_command` param, pass to state/report
- [ ] **runner.py:222**: Remove hardcoded `"de"`, extract languages from packets
- [ ] **report_header.py:28-41**: Remove duplicated location logic, use PromptGenerator
- [ ] **report_header.py:55**: Display actual CLI command (not canned example)
- [ ] **report_header.py:70**: Fix token limit from `2000` to `8000` (or config value)
- [ ] **report_header.py:106**: Update Check A description to include brand_names
- [ ] **report_header.py:107**: Update Check B description to mention subdomain matching
- [ ] **report_generator.py**: Accept new params (languages_used, contexts, cli_command)

---

## VALIDATION

After implementation, verify:

1. **Run a mixed-language config** (e.g., queries in both DE and EN):
   - Methodology should list BOTH languages with their respective contexts/locations

2. **Run with custom CLI args**:
   ```bash
   python run.py -c configs/wien.gv.at.config.json -n 50 --offset 10 -p openai -d --name "test-run"
   ```
   - Methodology should show the EXACT command used

3. **Grep check** - No hardcoded values should remain:
   ```bash
   grep -n "2000" core/report_header.py  # Should return nothing
   grep -n '"de"' core/runner.py | grep get_system_context  # Should return nothing
   ```

4. **Check A/B descriptions** should match the actual logic in `core/relevancy_parser.py`

---

## FILES AFFECTED

| File | Changes |
|------|---------|
| `core/run_state.py:12-22` | Add `cli_command` field |
| `run.py:91-163` | Capture argv, pass cli_command |
| `core/runner.py:32-95, 215-257` | Accept cli_command, extract languages from packets |
| `core/report_header.py:24-113` | All methodology fixes |
| `core/report_generator.py` | Accept new params |

---

## PRIORITY

**HIGH** - Report accuracy is critical for client deliverables. Hardcoded values cause confusion and distrust when methodology doesn't match actual behavior.
