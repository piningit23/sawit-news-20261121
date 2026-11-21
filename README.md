# news-image-20261121

One image summing up the world news of **Saturday 21 November 2026**:
a newspaper front page, "THE WORLD TODAY".

## What the image shows

- Masthead with the date: SATURDAY 21 NOVEMBER 2026.
- Lead story: a Russian missile landing in Poland; PM Tusk calls it a
  deliberate provocation.
- Seven more panels: the Kryvyi Rih strike, Houthi missiles at Riyadh,
  the Wall Street tech rout, Trump's data-centre tax threat, Denmark's
  expulsion of a Russian attache over an assassination plot, EUR 1bn
  more EU arms aid for Ukraine, and New York's plan to close Rikers
  Island by 2032.
- A simple world map with the eight panel stories numbered on it.
- "World in Brief": 14 more stories (summit fallout, US Senate,
  sanctions, UK-EU deal, Gaza, COP31, weather, sport).
- 22 stories in total. Every story is verified in SOURCES.md.

## How to run

Python 3.13, standard library only, no network:

```
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py
```

Writes `/output/entry.png` by default (1024x1024 PNG, deterministic:
two runs produce byte-identical output).

## License

MIT (see LICENSE).
