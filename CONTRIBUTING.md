# Contributing

Thank you for helping make Indian personal-data testing better.

## Good first contributions
- Review or improve the Hindi, Hinglish or Odia templates in `nakli/templates.py`
- Add templates for a new language
- Add an adapter for a detector you use

## Ground rules
- Never add real personal data, real people's names or real identifiers.
- Do not commit large generated datasets; tests should generate data from a seed.
- Keep the core free of outside dependencies.

## Setup
```bash
pip install -e ".[dev]"
pytest -q
```

Please open an issue before a large change, so we can agree on the approach first.
