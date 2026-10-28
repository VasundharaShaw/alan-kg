# Plan: ALAN literature mining for the Q1 knowledge graph

Q1 (Hölker et al. 2021): How to harmonize light measurement methods across disciplinary boundaries?

Scope: Oct 2024 to Oct 2026, English only, OpenAlex and Europe PMC.
Output: Table A (titles + abstracts, all papers), Table B (full text, open-access papers).

## How we know when it is enough

1. The graph answers the questions in questions.md.
   Write the expected answers first, then check the graph reproduces them.
2. The vocabulary stops growing.
   Count new methods, quantities and units found per round; stop when a round adds very little.
3. The matching error is acceptable.
   Read 30-50 random abstracts by hand; count what the word lists missed and got wrong.

## One round

a. Scan with the current word lists (vocab/terms.py).
b. Review papers with no matches and frequent words that are not on the lists.
c. Add the missing terms to vocab/terms.py.
d. Re-scan, run the three checks, log the round (date, new terms, error rate).

## Rounds log

| Round | Date | New terms | Papers with no match | Error rate |
|-------|------|-----------|----------------------|------------|
| 1     |      |           |                      |            |
