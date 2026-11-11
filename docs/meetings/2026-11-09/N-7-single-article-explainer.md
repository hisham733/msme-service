# N-7 — one live article explained point by point

_Reference article: **“MATRADE-Led Malaysia Pavilion Secures RM453 Million in Export Deals at SEMICON
West 2026”** — published 23 October 2026._
Live page: <https://www.malaysiasme.com.my/matrade-led-malaysia-pavilion-secures-rm453-million-in-export-deals-at-semicon-west-2026/>

Why this article: it is a clean **normal release** that already follows the N-7 shape — **9 paragraphs,
4 chunks, 3 headings, 1 image, median 41 words per paragraph**. It is the model to copy.

---

## A. The article, top to bottom (as it appears on the page)

```
HEADLINE : MATRADE-Led Malaysia Pavilion Secures RM453 Million in Export Deals at SEMICON West 2026

PARAGRAPH 1 (75 words) : "KUALA LUMPUR, 22 OCTOBER 2026 – Malaysia's participation in the SEMICON West
                          2026 trade exhibition has resulted…"
PARAGRAPH 2 (33 words) : "This achievement reflects strong international demand for Malaysia's electronics…"
PARAGRAPH 3 (41 words) : "These capabilities push Malaysian companies to capitalise on emerging opportunities…"

HEADING 1 : "Exploring Opportunities in Global Microelectronics and Semiconductor Ecosystem"
PARAGRAPH 4 (45 words) : "MATRADE strengthened strategic industry linkages through meetings with SEMI…"
PARAGRAPH 5 (30 words) : "MATRADE has opened gateways to potential avenues for Malaysian companies…"

HEADING 2 : "Accelerating Malaysia's Semiconductor Exports"
PARAGRAPH 6 (53 words) : "Dato' Indera Abu Bakar Yusof, Chief Executive Officer of MATRADE said, 'MATRADE's…'"
IMAGE     : CEO-MATRADE-YBhg.-Dato-Indera-Abu-Bakar-Yusof-681x1024.jpg
PARAGRAPH 7 (46 words) : "'These efforts support the aspirations of the New Industrial Master Plan 2030…'"

HEADING 3 : "Strengthening Malaysian Exporter and SMEs"
PARAGRAPH 8 (35 words) : "Through geopolitical uncertainties, intensifying global competition…"
PARAGRAPH 9 (30 words) : "Through targeted trade promotion and industry engagements, MATRADE continues…"
```

---

## B. The four things the rule talks about — pointed at in this article

### 1. What is a "heading" (H2)?
The **three bold section titles** above: “Exploring Opportunities…”, “Accelerating Malaysia's…”, and
“Strengthening Malaysian Exporter and SMEs”. On the page they are larger lines that break the article
into parts. **This article has exactly 3 — inside the rule's 1–3.**

### 2. What is a "paragraph"?
Each block of running text — **P1 through P9** above. The rule wants them **short, about 2–3 lines**.
Here they run **30–75 words**, mostly 30–50 (median **41**). That matches the live style.

### 3. What is a "chunk"?
A chunk is **a group of 2–3 paragraphs that belong together**. Headings are *labels*, not chunks. In
this article the chunks are:

| Chunk | Paragraphs | Where it sits |
|---|---|---|
| **Chunk 1** | P1 + P2 + P3 (3 paragraphs) | the opening, before the first heading |
| **Chunk 2** | P4 + P5 (2 paragraphs) | under “Exploring Opportunities…” |
| **Chunk 3** | P6 + P7 (2 paragraphs) | under “Accelerating Malaysia's Semiconductor Exports” |
| **Chunk 4** | P8 + P9 (2 paragraphs) | under “Strengthening Malaysian Exporter and SMEs” |

**Count the chunks, not the headings → 4 chunks.** That is the rule's target. (Note: 4 chunks but only
3 headings — which is exactly why the old "3–8 headings" rule is the wrong lever.)

### 4. What about the image?
There is **one image** — the CEO portrait (`CEO-MATRADE-…-681x1024.jpg`), placed inside **chunk 3**,
right after the CEO's quote. **1 image is the normal case**, and this article does it correctly. (The
rule’s cap is 6; this one needs only 1.)

---

## C. Does this article follow the new rule?

| Point | Rule | This article | Verdict |
|---|---|---|---|
| Chunks | 4–5 chunks (8–15 paragraphs) | **4 chunks / 9 paragraphs** | ✅ follows |
| Headings | 1–3 H2 | **3 H2** | ✅ follows |
| Paragraph length | ~35–75 words (target ~50–60) | median **41**; one at **75** | ✅ inside the band; P1 is at the top |
| Images | 1 normal, 6 max | **1** | ✅ follows (normal) |
| Feature? | long profile/interview = exempt | a normal release, not a feature | ✅ must obey the 4–5 rule — and does |

**The only nit:** paragraph 1 is **75 words** — the very top of the allowed band (the target is closer
to 50–60). If anything were changed, that one paragraph would be tightened; everything else is already
the shape the rule wants.

---

## D. What the rule changes vs. how the engine works today

The current engine **counts headings** and insists on **3–8 H2**. On this article that happens to
match (3 headings) — but the logic is wrong: it would *add* headings to a short release and split it
into the same shape regardless of how many paragraphs the story really has.

The new rule instead says:

- **Count chunks** (groups of 2–3 paragraphs): this article has **4** → good.
- Keep **headings light** (1–3): this article has **3** → good.
- Keep **paragraphs short** (~2–3 lines): this article does → good.
- Use **1 image normally** (6 max): this article has 1 → good.

So the change is not cosmetic — it makes the engine reproduce **this** page’s shape, instead of
counting headings and over-structuring short releases.
