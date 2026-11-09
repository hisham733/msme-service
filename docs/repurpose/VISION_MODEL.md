# VISION_MODEL — the eye that reads the pictures

> **Vendored here (`D40` / `T-050`, 2026-11-06).** This is the upstream engine document.
> In this repository the engine lives in `msme/repurpose/engine/` and runs in-process on :8899;
> `config.local.json`, the `:8765` dashboard and `python -m pipeline.*` commands no longer apply.
> Use `python -m msme.repurpose.engine.<module>` and `/repurpose.html`; paths come from
> `msme/paths.py`.

*Model specification for the image-selection skill (deliverable: "document the spec, characteristics and
function of the model you select"). Every number here was measured on this laptop, not estimated.
Decision: **D-010**. Rulebook: `pipeline/IMAGE_GUIDE.md`. Probe evidence:
`C:\Users\mgowy\imgmodel_probe\MODEL_TEST_REPORT.md`.*

---

## 1. What it does in this project

One job: given a picture, say **what is in it** — so the skill can decide without ever guessing from a
filename. For each image it returns

```json
{"kind":"people|logo|graph|event-visual|product|junk",
 "people":3,                        // how many people are visible
 "capture":"photo|crop-art|screenshot|render|scanned",
 "text_in_image":"none|some|heavy",
 "subject":"three people holding iced orange drinks in front of a rednote backdrop",
 "caption_facts":"three people, orange cups, Tealive backdrop"}
```

`kind` drives the ladder rung, `people` breaks ties inside the people rung, `subject` is what the
caption is written from, and `caption_facts` is the guard against a caption inventing detail.

## 2. The model selected

**DeepSeek `deepseek-flash` — the model the pipeline already uses for the prose — in vision mode.**

| attribute | value |
|---|---|
| provider / model id | DeepSeek · `deepseek-flash` (served as DeepSeek-V4.1-Flash-1017) |
| endpoint | `https://api.deepseek.com/chat/completions` (already in `config.json`) |
| input | chat message content array: a text part + `{"type":"image_url","image_url":{"url":"data:image/jpeg;base64,…"}}` |
| image prep | longest side 768 px, JPEG q82 — a 15 MB original becomes ~75 KB base64 |
| temperature | 0 |
| calls per release folder | **1** (all candidates in one call, each image its own part with an `id`) |
| cache | keyed `model｜prompt_version｜sha256(bytes)` in `analysis/imageeval/vision_cache.json` — a re-run costs nothing |
| code | `pipeline/vision.py` |
| licence / terms | DeepSeek API terms; no model weights to license, nothing runs locally |

**Why this one.** It needed no new dependency, no GPU, no weights, no licence review, and no second
vendor — the pipeline was already calling this endpoint for the article text. Verified before building
on it: it correctly answered "three people in this photograph" for the Tealive target image.

**Measured throughput:** 5 images in 12.2 s (one folder, single call) · 110 supplied images across 20
folders in 89 s (3 folders in parallel) · 32 TARGET featured images in 23 s. Costs are per new file
only — the cache absorbs everything after the first pass, which is what makes re-scoring the skill on 30
articles free.

## 3. Why not a local model — measured, not assumed

A full probe was run on 65 hand-labelled project images (`MODEL_TEST_REPORT.md`). Summary:

| candidate | measured verdict |
|---|---|
| **CLIP ViT-B-32** (`laion2b_s34b_b79k`, open_clip) | **93.8%** class accuracy alone, **95.4%** in a cascade; 107 ms/image — the best local option |
| + OpenCV **YuNet** faces | 227 KB, Apache-2.0, **15 ms**, face presence **23/23, zero false positives** |
| + torchvision FasterRCNN-MobileNetV3-320 | 74 MB, BSD-3, exact person counts on groups ≤12, under-counts crowds |
| CLIP ViT-B-16 | 1,740 ms/image **and** less accurate (87.7%) — rejected |
| RetinaNet-ResNet50-FPN-v2 | 4,093 ms/image for **identical** accuracy — rejected |
| ImageNet classifiers (MobileNet/EfficientNet/ViT) | 41–45%; **1 of 13 logos** right — structurally cannot separate a logo from a chart — rejected |
| OpenCV Haar/LBP cascades | **do not exist** on opencv-python 5.0.0.93 (`cv2.CascadeClassifier` raises `AttributeError`, no XMLs ship) |
| insightface `buffalo_l` | 193 ms, 2 false faces, packs are **non-commercial** — rejected for a client project |
| `derronqi/yolov8-face` | **GPL-3.0** — a real licence risk for a client deliverable; avoid |

So a local model is **not needed** and was not adopted. It stays documented below as the offline
fallback, because "the API is down" is not a reason to guess at pictures.

## 4. Fallback path — if the API is unavailable

```powershell
"C:\Users\mgowy\AppData\Local\Programs\Python\Python312\python.exe" -m pip install open_clip_torch
```

- CLIP: open_clip arch `ViT-B-32`, pretrained `laion2b_s34b_b79k` — 577.1 MB, downloaded on first use.
- Faces: `face_detection_yunet_2023mar.onnx` — 232,589 B. **Download from
  `https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/…`** —
  `raw.githubusercontent.com` serves a 131-byte LFS pointer and fails silently.
- Persons: `torchvision.models.detection.fasterrcnn_mobilenet_v3_large_320_fpn` +
  `FasterRCNN_MobileNet_V3_Large_320_FPN_Weights.DEFAULT` — 74.2 MB.
- Measured: 124 ms/image for class+faces (300 images ≈ 38 s), 284 ms/image with person boxes.

**There is no maintained, permissively-licensed, ready-to-run CPU logo detector.** LogoDet-3K ships no
weights (training dataset, Google-Drive only); `satojkovic/DeepLogo2` (MIT) publishes no logo weights;
`nuwandda/yolov7-logo-detection` (BSD-3) ships only base YOLOv7 and expects you to train. Zero-shot CLIP
already gets 13/13 on this project's flat logos — buy a logo *detector* only if you need *which brand,
where in the photo*.

## 5. Two traps — one of which this project fell into

**Trap 1 — a byte/pixel "junk" filter is unsafe.** A sensible-looking rule ("small **and** wide", or
"small **and** few colours") dropped the probe's accuracy 0.938 → 0.785 and flipped 8 logos and 2 people
photographs into junk. The reason is not subtle once measured: **a logo wordmark on flat white and an
email signature strip are statistically the same image.**

> **This project had that bug.** `imgselect.py` gated junk at `MIN_BYTES = 10_000`. The smallest
> published TARGET featured image is **2,423 B** (SME Malaysia's logo) — the gate would have discarded
> exactly that kind of asset had it arrived as a loose file. Fixed 2026-10-23: the gate now drops only
> degenerate files (`< 2,000 B`, `< 64 px` long side, `< 3,000 px²`) and **every other junk decision is
> made by the model**. Re-measured after the fix: match 83.3% (up from 80.0%), so the safe gate is also
> the better one.

**Trap 2 — a face-size threshold is a trap.** Crowd photographs — the most valuable people images in
this corpus (CAEXPO 40 people, REHDA 150) — carry faces of 11–19 px. Any threshold that rejects
"incidental" faces also rejects the crowds. Do not add one.

## 6. Known limits — say these out loud

1. **There are no charts in this project.** All 192 images under `analysis\`, `Files_from_MSME\` and
   `DLW\` were searched; every "analysis-looking" featured image is a flat wordmark. Our own 110
   vision tags contain **0 graphs**. So the rule "a graph is never the key visual" (D-008) is enforced
   by code but **untested against MSME's real charts** — the probe measured the graph class on 8
   Wikimedia charts + 5 rendered ones (CLIP 13/13, including a striped data table), which is evidence
   for the *model*, not for MSME's material. This is the honest answer to their question 1.
2. **No brand identification beyond what is legible.** The model reads a wordmark's own text ("MRCA",
   "PIKOM", "Global Electronics Association") and that is what the rename uses. It cannot tell you which
   brand appears inside a photograph unless the logo is legible in the pixels.
3. **No face identity, by design.** It counts people and describes the scene; it never names anyone. A
   name enters a caption only if the release supplies it (MSME question 4).
4. **The model can be wrong about a crowd.** Person counts above ~40 are approximations; the rung
   decisions were measured to be right 96.7% of the time, not 100%.

## 7. How to verify this yourself in five minutes

1. **Does the model actually see?** Pick any published article's featured image and run
   `python -m pipeline.vision "<path to a jpg>"` — it prints one line per image: kind, people, subject.
   Check it against what you see. If it says "three people" and you count three, the eye works.
2. **Is the cache honest?** Delete `analysis/imageeval/vision_cache.json`, run
   `python tools\imgtag.py`, and the tags should come back the same. Re-run it a second time: it should
   report the same count in ~0 s (cache hit).
3. **Is the score real?** `python tools\imgeval.py --detail` prints one line per article:
   `PASS/fail · article · picked rung vs TARGET rung · why`. Open any `fail` line's article on
   malaysiasme.com.my and judge it yourself — the six residuals are classified in
   `pipeline\IMAGE_GUIDE.md` §5.
4. **Spot-check a caption:** `python -m pipeline.imgselect --folder "<name>" --caption` prints the
   caption next to the file it belongs to; compare with the picture.

If a manual check disagrees with the machine, the machine is wrong — record it and re-run `imgeval`.

## 8. Where it plugs in

```
pipeline/vision.py     the eye (this document)
pipeline/harvest.py    mines .pdf/.docx so the eye has more to look at
pipeline/imgselect.py  the ladder that consumes the tags, and writes the ## Images block
pipeline/llm_step.py   injects that block; the prose model no longer picks pictures (D-010)
tools/imgeval.py       scores the whole thing against TARGET
```
