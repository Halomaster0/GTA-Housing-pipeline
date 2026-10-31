from pathlib import Path
for p in [Path('src/ai/planner.py'), Path('docs/build-plan.md'), Path('.env')]:
    lines = p.read_text(encoding='utf-8', errors='ignore').split('\n')
    print(f"=== {p} ===")
    for i, line in enumerate(lines, 1):
        low = line.lower()
        if 'openrouter' in low or 'anthropic' in low or 'base_url' in low or 'claude' in low or 'api' in low:
            if any(x in low for x in ('openrouter','anthropic','claude','base_url','api_key','router','end')):
                print(i, line[:160])
