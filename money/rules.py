"""Ordered first-match-wins categorization rules over normalized descriptions.

Loader is deliberately hostile (§2.1.5):
- any rule naming a category not in the taxonomy → hard fail
- any earlier rule shadowing a later one (earlier match a substring of a
  later match, with guards no stricter) → hard fail — the E-TRANSFER IN /
  TRANSFER ordering lesson, enforced forever
- no match at categorize time → "Uncategorized", never a guess
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

UNCATEGORIZED = "Uncategorized"
RULE_KEYS = {"match", "category", "sign", "account", "min_abs", "max_abs"}


@dataclass(frozen=True)
class Rule:
    match: str
    category: str
    sign: str | None = None
    account: str | None = None
    min_abs: float | None = None
    max_abs: float | None = None

    def guards(self) -> tuple:
        return (self.sign, self.account, self.min_abs, self.max_abs)

    def applies(self, description_upper: str, amount: float, account: str) -> bool:
        if self.match.upper() not in description_upper:
            return False
        if self.sign == "+" and amount <= 0:
            return False
        if self.sign == "-" and amount >= 0:
            return False
        if self.account is not None and self.account != account:
            return False
        if self.min_abs is not None and abs(amount) < self.min_abs:
            return False
        if self.max_abs is not None and abs(amount) > self.max_abs:
            return False
        return True


def _guards_no_stricter(earlier: Rule, later: Rule) -> bool:
    """True when every row the later rule could see also passes the earlier
    rule's guards — i.e. the earlier rule genuinely shadows the later one."""
    if earlier.sign is not None and earlier.sign != later.sign:
        return False
    if earlier.account is not None and earlier.account != later.account:
        return False
    if earlier.min_abs is not None or earlier.max_abs is not None:
        return False  # amount-banded rules are treated as non-shadowing
    return True


def load_rules(path: Path) -> tuple[list[str], list[Rule]]:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    categories = data.get("categories") or []
    if UNCATEGORIZED not in categories:
        raise SystemExit(f"{path}: taxonomy must include {UNCATEGORIZED!r}")
    raw_rules = data.get("rules") or []
    rules: list[Rule] = []
    for i, raw in enumerate(raw_rules):
        unknown = set(raw) - RULE_KEYS
        if unknown:
            raise SystemExit(f"{path}: rule {i + 1} has unknown keys {sorted(unknown)}")
        if not raw.get("match") or not str(raw["match"]).strip():
            raise SystemExit(f"{path}: rule {i + 1} has an empty match")
        if raw.get("sign") not in (None, "+", "-"):
            raise SystemExit(f"{path}: rule {i + 1} sign must be '+' or '-'")
        category = raw.get("category")
        if category not in categories:
            raise SystemExit(
                f"{path}: rule {i + 1} ({raw['match']!r}) names unknown "
                f"category {category!r} — not in the taxonomy"
            )
        rules.append(
            Rule(
                match=str(raw["match"]),
                category=category,
                sign=raw.get("sign"),
                account=raw.get("account"),
                min_abs=raw.get("min_abs"),
                max_abs=raw.get("max_abs"),
            )
        )
    # Shadow-rule check: an earlier broad rule must never make a later,
    # more specific rule unreachable.
    for i, earlier in enumerate(rules):
        for later in rules[i + 1 :]:
            if (
                earlier.match.upper() in later.match.upper()
                and _guards_no_stricter(earlier, later)
            ):
                raise SystemExit(
                    f"{path}: rule {earlier.match!r} (row {i + 1}) shadows the "
                    f"later rule {later.match!r} — every row the later rule "
                    f"would match hits the earlier one first. Reorder them "
                    f"(most specific first)."
                )
    return categories, rules


def categorize(
    description: str, amount: float, account: str, rules: list[Rule]
) -> str:
    d = description.upper()
    for rule in rules:
        if rule.applies(d, amount, account):
            return rule.category
    return UNCATEGORIZED
