# TODO (ai-relevancy-checker)

- [x] Unify `max_queries`/`gsc_days` configuration: CLI now defers to config values (with explicit overrides) instead of hardcoded defaults.
- [x] Remove hidden defaults/fallbacks for prompt mode/providers: invalid prompt modes error out and providers must be explicitly configured (no silent fallbacks).
- [x] Externalize magic timeouts/retries: timeouts, retries, retry delays, and stuck thresholds live in config; execution uses these values.
- [x] Make GSC fetch limits/config explicit: row limits, dimensions, and auth paths are config-driven and validated.
- [x] Eliminate language fallbacks: language detection now errors without explicit indicators/default; no silent German fallback.
- [x] Centralize prompt/system text: domain-list prompts, system contexts, and report UI labels are sourced from config.
- [x] Tighten domain match rules: exact/subdomain matching is configurable; substring matches removed.
- [x] Respect config in debug path: debug query path pulls country/page/metrics from config and uses configured domain prompt suffix.

New follow-ups
- [ ] Allow partial/deep overrides for nested dict config values (e.g., `report_text`, `answer_system_contexts`) to prevent accidental full replacement when only tweaking one label.
- [ ] Externalize remaining report copy (chart labels, methodology prose, JS messages) into config to complete UI text configurability.
