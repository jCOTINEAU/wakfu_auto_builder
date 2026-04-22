# Scenario runner — damage Monte-Carlo

Monte-Carlo simulator for spell sequences in Wakfu. Define a caster, a target,
a list of spell steps, and the tool rolls crit / parade / stochastic rounding
N times and produces aggregate statistics.

## Run

```bash
python scenario.py test_data/scenarios/test_1.json
```

## Scenario JSON format

```json
{
  "iterations": 10000,
  "seed": 42,
  "level": 50,

  "caster": {
    "elemental_mastery": 274,
    "back_mastery": 223,
    "melee_mastery": 290,
    "critical_chance": 100,
    "damage_inflicted": 100
  },

  "target": {
    "elemental_resistance": 0,
    "parade_chance": 0
  },

  "steps": [
    {
      "name": "Klepto dos",
      "spell": "Sram/klepto",
      "orientation": "back"
    }
  ]
}
```

### Top-level fields

| Field | Type | Notes |
|-------|------|-------|
| `iterations` | int | Monte-Carlo iterations (default 1000) |
| `seed` | int \| null | RNG seed for reproducibility |
| `level` | int | Spell level, applied to all string-ref spells |
| `spells_dir` | string | Override directory for spell JSONs (default `test_data/classes`) |
| `caster` | object | See `CasterStats` in [damage_calculator.py](damage_calculator.py) |
| `target` | object | See `TargetStats` in [damage_calculator.py](damage_calculator.py) |
| `steps` | array | Sequence of spell casts |
| `thresholds` | array of int | Values `X` to report `P(total >= X)` |

### Step fields

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | Display name |
| `spell` | string \| object | `"Class/id"` (loaded from JSON) **or** inline object |
| `orientation` | string | `"front"` / `"side"` / `"back"` (default `"front"`) |
| `caster_modifiers` | object | Delta ints applied to base `CasterStats` for this step |
| `target_modifiers` | object | Delta ints applied to base `TargetStats` for this step |
| `spell_modifiers` | object | Overrides on the loaded `Spell` (bonus fields, is_melee, ...) |

### Modifiers

- `caster_modifiers` / `target_modifiers` : **always start from the base**. Not cumulative across steps.
- `spell_modifiers` : applied **after** the spell is loaded from JSON. Useful for per-cast buffs like `bonus_base_percent`, `bonus_damage_inflicted`, `bonus_mastery`, or changing `is_melee`.

## Spell JSON format

Located at `test_data/classes/<Class>/<id>.json`.

```json
{
  "id": "klepto",
  "name": "Klepto",
  "description": "",
  "metadata": {
    "description": "",
    "cost_ap": 2
  },
  "damage_per_level": [
    {
      "level": 50,
      "damage_non_crit": 14,
      "damage_crit": 17
    }
  ]
}
```

The loader reads `damage_per_level[level]` to fill the `Spell` base and crit_base.
Optional fields `is_melee`, `is_indirect`, `can_crit` may be declared in
`metadata` (otherwise defaults apply: `is_melee=true`, rest neutral).

## Examples

### test_1.json — simple crit hit

Caster with 100% crit, mid masteries, klepto in the back.

```bash
python scenario.py test_data/scenarios/test_1.json
```

Expected output: ~377 damage per hit (deterministic since 100% crit + single spell).

### example.json — two inline spells

Two spells with bonus modifiers and face / back orientation.

```bash
python scenario.py test_data/scenarios/example.json
```

## Output

Default (pretty print in terminal):
- **Per-step stats**: min / avg / max / median for each spell
- **Total scenario**: same stats, summed over all steps per iteration
- **Histogram**: distribution of total damage (ASCII bars)
- **Thresholds** (optional): probability of total >= each threshold

With `--json` (structured output for tooling):
```bash
python scenario.py test_data/scenarios/test_1.json --json > run1.json
```
Outputs a JSON with `total_damages` (raw list), `total_summary`, per-step data,
and thresholds. Consumed by `compare.py`.

## Comparing scenarios (visualisation)

Produce an interactive HTML report comparing 2+ scenarios:

```bash
python scenario.py test_data/scenarios/test_1.json --json > /tmp/run1.json
python scenario.py test_data/scenarios/test_2.json --json > /tmp/run2.json
python compare.py /tmp/run1.json /tmp/run2.json -o comparison.html
```

Open `comparison.html` in a browser. You get :
- **Superposed histograms** of total damage per scenario, with min / median / avg / max vertical markers
- **Damage guarantee curve** : `P(total >= X)` for each scenario — hover any X to see the probability
- Colors auto-assigned, legend for scenario names

Dependencies: `pip install plotly`.
