# 🎯 Niche Radar Skill

Systematic niche discovery and validation pipeline for finding green-market opportunities.

## Structure

```
niche-radar-skill/
├── SKILL.md                  ← Инструкции для AI-агента (Antigravity формат)
├── README.md                 ← Этот файл
├── scripts/
│   ├── check_traffic.py      ← Оценка трафика конкурента (бесплатные сигналы)
│   ├── expand_keywords.py    ← Расширение сидов через Google Autocomplete
│   ├── score_niche.py        ← SERP + трафик → Disruption Score (0-100)
│   └── rank_niches.py        ← Оркестратор: полный пайплайн + MD-отчёт
└── references/
    ├── scoring.md            ← Формула Disruption Score
    ├── traffic_signals.md    ← 10 бесплатных сигналов трафика
    ├── idea_validation.md    ← Взвешенный скорер идей (11 критериев)
    └── competitor_db.md      ← База 40+ конкурентов по 4 нишам
```

## Quick Start

```bash
pip install requests beautifulsoup4 lxml

# Полный пайплайн
python scripts/rank_niches.py --seed "vibe coding testing" --depth 2

# Проверить трафик конкурента
python scripts/check_traffic.py --domain "problemsifter.com"

# Оценить одну нишу
python scripts/score_niche.py --keyword "AI code security"
```

## Использование в AI-агентах

### Antigravity
Скопировать папку в `~/.gemini/antigravity/skills/niche-radar/`

### Другие агенты (Claude Desktop, Cursor, OpenClaw, Cline)
Добавить содержимое `SKILL.md` в system prompt агента. Скрипты вызываются как обычные CLI-команды.

## API Keys
Не нужны. Все скрипты используют бесплатные публичные источники.
