# StressSense: presentation notes

- A script to talk from: team walkthrough + Friday update.
- Each step: **what we did → why → what we saw → what it means**.
- Every number comes from a real run (Colab on 23 Nov 2026 for raw data, laptop after that).
- **Show:** = what to put on screen.

---

## Step 0. What this project is

- 15 people wore sensors on chest + wrist during a lab study → the **WESAD** dataset.
- The study had them: calm, stressed, watching funny videos, meditating.
- Goal: look at **1 minute** of sensor data → say **"stressed" or "not stressed"**.
- If stressed → the app suggests something small: breathing exercise, short break, walk.
- **Not a medical tool.** No diagnosis. It spots body patterns that look like the lab's stress phase.

**Our four questions:**

| | In plain words | Status |
|---|---|---|
| RQ1 | Does it work on a new person it has never seen? | Answered |
| RQ2 | Does it work equally well for everyone, or fail for some? | Answered |
| RQ3 | If it fails for someone, can a little per-person calibration fix it? | Answered |
| RQ4 | Should the app sometimes stay quiet instead of always nudging? | Draft, needs rethink |

**The chain:** each step reads the previous step's file:

```
WESAD raw files (15 people, ~100 min each)
  -> 1-minute windows, ~99 numbers each        windows.parquet   (Part A)
  -> a stress score per window                  scores.csv        (Part A)
  -> a personal alarm line per person           RQ3               (Part B)
  -> act / watch / none per window              decisions.csv     (Part B, RQ4)
  -> a suggestion: breathing / break / walk                       (Part C)
```

- **Show:** the chain diagram.

---

## Step 1. The raw data: one person (S2)

**What we did**
- Opened one person's file first. Before building anything, know what you have.
- Ran: `python scripts/inspect_wesad.py S2` (on Colab; the dataset is 2.5 GB).
- People are S2–S11 and S13–S17. (S1 and S12 don't exist in WESAD.)

**What's in one file (`S2.pkl`)**
- `subject` → the name ("S2")
- `signal` → the sensor recordings, split into `chest` and `wrist`
- `label` → which phase the person was in, at every moment

**The sensors**

| Device | Sensor | Measures | Readings per second (Hz) | S2's readings |
|---|---|---|---|---|
| Chest | ECG | Heart's electrical signal (mV) | 700 | 4,255,300 |
| Chest | EDA | Sweat: skin conductance (µS) | 700 | 4,255,300 |
| Chest | EMG | Muscle tension | 700 | 4,255,300 |
| Chest | Resp | Breathing: chest stretch | 700 | 4,255,300 |
| Chest | Temp | Skin temperature (°C) | 700 | 4,255,300 |
| Chest | ACC | Movement, 3 directions (g) | 700 | 4,255,300 x 3 |
| Wrist | BVP | Pulse (blood flow) | 64 | 389,056 |
| Wrist | EDA | Sweat | 4 | 24,316 |
| Wrist | TEMP | Skin temperature | 4 | 24,316 |
| Wrist | ACC | Movement, 3 directions | 32 | 194,528 x 3 |

- Chest = lab chest strap, very fast. Wrist = smartwatch-like (Empatica E4), slower.
- "Hz" = readings per second.

**Check: do both devices cover the same time?**
- Chest: 4,255,300 ÷ 700 = **6,079 s**
- Wrist pulse: 389,056 ÷ 64 = **6,079 s**
- Wrist sweat: 24,316 ÷ 4 = **6,079 s**
- → Same 101 minutes on every sensor → we can cut **the same minute** out of all of them.

**What the raw readings look like** (S2, chest, one row = 1/700 s = 0.0014 s)

| time (s) | ECG | EDA | Resp | Temp | ACC_x | label |
|---|---|---|---|---|---|---|
| 0.0000 | 0.021 | 5.25 | -1.15 | 30.12 | 0.96 | 0 (setup) |
| 0.0014 | 0.020 | 5.27 | -1.12 | 30.13 | 0.93 | 0 |
| ... | | | | | | |
| 2273.5457 | -0.012 | 1.28 | -1.22 | 31.21 | 0.88 | **2 (stress)** |
| 2273.5471 | -0.002 | 1.25 | -1.20 | 31.22 | 0.88 | 2 |

- 4,255,300 rows for S2. One row per 1/700 of a second.
- **ECG:** one value means nothing alone. A heartbeat = a spike roughly every 0.8 s → you need many
  readings to find beats → one reason for 1-minute windows.
- **ACC about 0.9–1.0** = about 1 g = gravity → the device is held still and upright.

**The labels for S2** (count ÷ 700 ÷ 60 = minutes)

| Code | Phase | What the person did | Labels | Minutes |
|---|---|---|---|---|
| 1 | Baseline | Sat and read a magazine | 800,800 | 19.1 |
| 2 | **Stress** | Speech + mental arithmetic in front of judges (Trier Social Stress Test) | 430,500 | 10.3 |
| 3 | Amusement | Watched funny videos | 253,400 | 6.0 |
| 4 | Meditation | Two guided meditations | 537,599 | 12.8 |
| 0, 6, 7 | In between | Setup, instructions, questionnaires | 2,233,001 | 53.2 |

- Worked example: stress = 430,500 ÷ 700 = 615 s = **10.3 min**.
- S2's stress starts at row 1,591,482 → ÷ 700 = 2,273.5 s → **minute 37.9**.

**S2's session, minute by minute** (where the label changes; blips under 20 s skipped)

| Minutes | Phase | Length (min) |
|---|---|---|
| 0.0 – 5.1 | in between (sensors put on) | 5.1 |
| **5.1 – 24.2** | **baseline** | **19.1** |
| 24.2 – 37.9 | in between (instructions, likely speech preparation) | 13.7 |
| **37.9 – 48.1** | **stress** | **10.2** |
| 48.1 – 68.3 | in between + "ignore" (short questionnaires) | 20.2 |
| **68.3 – 74.8** | **meditation 1** | 6.5 |
| 74.8 – 79.4 | in between | 4.6 |
| **79.4 – 85.4** | **amusement** | 6.0 |
| 85.4 – 91.6 | in between + "ignore" | 6.2 |
| **91.6 – 97.9** | **meditation 2** | 6.3 |
| 97.9 – 101.3 | in between | 3.4 |

- Every phase length matches the label counts above → the labels are consistent.
- **Not everyone had the same order.** From the windows data (first stress window number):
  - S2, S3, S6, S9, S11, S14, S16 → stress early (about window #36).
  - S4, S5, S7, S8, S10, S13, S15, S17 → stress later (about window #60), so amusement probably came first.
  - Good: the model can't just learn "stress is always the 3rd thing".
- **Baseline is always first, for everyone** → why "learn your calm in the first 5 minutes" works
  in this dataset (Step 7).

**What we noticed**
- **More than half the recording (53 of 101 min) is "in between"** → thrown away. Only phases 1–4 are kept.
- **Surprise: sweat was lower at stress (1.28) than at the very start (5.25).**
  - Looks wrong: stress should mean more sweat.
  - Reason: at the start the sensor had just been put on and was settling; sweat levels drift
    over a session and differ a lot between people.
  - **Lesson: one raw reading means nothing.** Compare within a minute (averages, bursts) and
    against the person's own normal → why we use windows (Step 2) and personal baselines (Step 7).
- **Skin temperature creeps up: 30.1 °C → 31.2 °C** by minute 38.
  - Skin warms slowly during a session.
  - Caveat: a model could confuse "later in the session" with "stressed".
- **Everyone did the same study in the same order, with baseline first** → about 1 in 5 minutes is
  stress for everyone. A lab fact, not real life. It matters in Step 7.

**Decision: what counts as "stressed"**
- **Stress vs everything else.** Stress = 1; baseline, amusement and meditation = 0.
- Why: the app only needs one decision, "nudge or not". Binary is also how WESAD is most often
  reported, so it's easy to compare.
- Tricky case: amusement. Laughing also speeds up the heart.

**Where the data comes from**
- Official WESAD page, University of Siegen (2.5 GB zipped). We checked the link matches.
- Rules: scientific, non-commercial use only. Must cite: Schmidt et al., *Introducing WESAD*, ICMI 2018.
- Safety: the files are Python "pickles", which can run code when opened → only use the official copy.

**The code**
- `src/data_model/load_wesad.py` → opens a person's file; turns 3-direction movement into one
  "how much movement" number.
- `scripts/inspect_wesad.py` → prints the layout so we can check the code's assumptions.

- **Show:** the S2 sensor table + S2's timeline.

---

## Step 2. Cutting recordings into one-minute windows

**Why windows at all**
- A model can't learn from a 100-minute recording in one go.
- It needs many small examples of the same size, each with a right answer.
- Analogy: cut a movie into 1-minute clips → write a summary card per clip ("heart rate 94,
  sweating, breathing fast") + the answer (stressed or not) → the model learns from the cards.

**How we cut them** (`src/data_model/preprocess.py`)
1. Put a **60-second ruler** at the start.
2. Look at the labels under it: 60 x 700 = **42,000 labels**. Find the most common phase.
3. **Keep** the window only if that phase is real (1–4) **and** covers **≥ 90%** of the minute.
4. Answer: **1 if stress, 0 if not**.
5. Turn the minute into ~99 numbers (Step 3).
6. **Slide 30 s forward**, repeat. Then repeat for all 15 people.

**Why these settings** (`config.example.yaml`, section `windows:`)

| Setting | Value | Why |
|---|---|---|
| Length | 60 s | Heart-rate variability needs about a minute of beats. The WESAD paper also used 60 s. |
| Step | 30 s (50% overlap) | Twice as many windows; matters with only 15 people. Catch: neighbours share 30 s → near-twins (comes back in Step 5). |
| Purity | 90% | Half calm, half stressed = no honest answer. One window = one thing, one emotion. |

**What we got** (opened `handoff/windows.parquet` by hand)
- **1,377 windows x 104 columns** = 5 info columns (person, window number, start time, phase,
  answer) + **99 numbers**.
- **87–95 windows per person, 19–23 of them stress.** Similar for everyone (same study).
- S2's first kept window starts at **second 330 (5.5 min)**, not 0.
  - Baseline starts at 5.1 min. A window starting at 5.0 min would be about 10% setup → below
    the 90% rule → dropped. The next one, at 5.5 min, is fully baseline → kept.
- `window_id` counts **kept** windows only → window 0 = 330 s, window 1 = 360 s, ...

| Phase | Windows | Share |
|---|---|---|
| Baseline | 562 | 41% |
| Meditation | 345 | 25% |
| Stress | 307 | 22% |
| Amusement | 163 | 12% |

- **307 stressed vs 1,070 not stressed** → only about 1 in 5 is stress.
- → Why the model gets "balanced" class weights (Step 4) and why we grade with balanced accuracy (Step 5).

**Sanity check with the math**
- S2 was stressed for 10.3 min.
- 1-minute windows starting every 30 s that fit fully inside: 0:00, 0:30, ..., 9:00 = **19 windows**.
- The code printed `S2: 87 windows (19 stress)` → **math and code agree**.

- **Show:** the sliding-window picture (ruler moves 30 s; mixed windows dropped).

---

## Step 3. Turning each minute into 99 numbers ("features")

**What we did**
- For every window, every sensor → a set of summary numbers.
- Code: `src/data_model/features.py` (basic numbers) + `src/data_model/physio.py` (body-specific
  numbers, using the neurokit2 library).
- Names say where each number came from: `chest_ecg_hr_mean` = chest, heartbeat sensor, average heart rate.

**Why hand-made numbers and not deep learning**
- Only 15 people, about 1,400 windows → far too little for a neural network to learn from raw signals.
- Hand-made numbers are explainable ("sweat went up") and are the standard approach for WESAD.

**Part 1: 8 basic numbers for every sensor** (10 sensors x 8 = **80**)

| Number | Plain meaning | Toy example: readings 2, 3, 3, 4, 8 |
|---|---|---|
| mean | average | (2+3+3+4+8) ÷ 5 = **4.0** |
| std | how much it wobbles around the average | **≈ 2.1** |
| min / max | lowest / highest | **2 / 8** |
| range | max − min | **6** |
| median | middle value when sorted | **3** |
| iqr | spread of the middle half (ignores extremes) | **1** (3 to 4) |
| slope | rising or falling over the minute (straight-line fit) | **positive** |

**Part 2: 19 body-specific numbers**

| Sensor | Extra | Numbers |
|---|---|---|
| Chest ECG, wrist BVP (heart) | +4 each | `hr_mean` beats per minute; `hr_std` how much the heart rate changes in the minute; `hrv_rmssd`, `hrv_sdnn` how uneven the gaps between beats are |
| Chest + wrist EDA (sweat) | +4 each | `scl_mean` slow background sweat level; `phasic_mean` fast part; `scr_count` number of sweat bursts; `scr_amp_mean` average burst size |
| Chest Resp (breathing) | +3 | `rate_mean` breaths per minute; `rate_std`; `amp_mean` breath depth |

- **Total: 80 + 4 + 4 + 4 + 4 + 3 = 99.** Chest 59, wrist 40.
- Per sensor: ECG 12, chest EDA 12, BVP 12, wrist EDA 12, Resp 11, and 8 each for chest ACC, EMG,
  Temp, wrist ACC, wrist TEMP.

**Heart-rate variability (HRV), the math in words**
- Find every heartbeat. Measure the gaps between beats, e.g. 0.80 s, 0.85 s, 0.78 s.
- **RMSSD:** difference between each gap and the next → square them → average → square root.
- **SDNN:** how spread out all the gaps are (standard deviation).
- Relaxed heart = uneven gaps = **high** HRV. Stressed heart ticks like a metronome = **low** HRV.
- Needs about a minute of beats → another reason for 60-second windows.

**What we checked by hand:** S2's averages per phase

| Number | Baseline | Stress | Amusement | Meditation | Reading |
|---|---|---|---|---|---|
| Heart rate, chest (`chest_ecg_hr_mean`) | 72.1 | **76.8** | 66.7 | 67.1 | Stress = fastest heart |
| Sweat level, wrist (`wrist_eda_scl_mean`) | 0.26 | **0.86** | 0.21 | 0.20 | **3–4x higher** under stress, clearest signal |
| Sweat level, chest (`chest_eda_scl_mean`) | **1.97** | 1.77 | 0.74 | 0.71 | Baseline higher than stress (!) |
| Breaths per minute (`chest_resp_rate_mean`) | 21.6 | **16.3** | 21.3 | 15.7 | Slower under stress (!) |
| Skin temp, chest (`chest_temp_mean`) | **28.9** | 31.2 | 32.2 | 31.7 | Baseline lowest (!) |
| Heart rate, wrist (`wrist_bvp_hr_mean`) | 74.0 | 71.0 | 70.8 | 67.3 | Wrist misses the stress jump (!) |

**What we noticed (the "!" rows)**
- **Chest sweat highest at baseline** → baseline comes first while the sensor is still settling
  (remember 5.25 at second 0). Drift, not stress.
- **Breathing slower under stress** → S2 was giving a speech; talking changes breathing.
- **Temperature lowest at baseline** → skin warms over the session; baseline is first. Temperature
  tracks **time**, not stress.
- **Wrist heart rate misses the jump** → the wrist pulse sensor is noisier, especially when hands
  move while talking.
- **Big lesson: no single number cleanly says "stress".** Some rise; some are fooled by time or
  talking. **That's why we use a model**: it combines all 99 and learns which patterns together
  mean stress. A rule like "heart rate > 75" would not work.

**Empty values**
- Only breathing rate (mean, std) is ever empty: **10 of 1,377 windows (0.7%)**. No clean breaths
  were found in those minutes.
- The model fills them with the typical (median) value from the training people (Step 4).

- **Show:** the 8-numbers toy table + S2's per-phase table.

---

## Step 4. The model: how a stress score is made (`scores.csv`)

**What the model is:** a **random forest** = 200 small decision trees that each vote "stress" or
"not stress". Code: `src/data_model/classifier.py` + `src/data_model/evaluate.py`.

**One tree = a chain of yes/no questions about the 99 numbers**

```
                 Is wrist sweat burst size > X ?
                 /                          \
               no                           yes
               /                              \
   Is heart rate > Y ?                Is chest movement > Z ?
     /         \                         /            \
"not stress"  "stress"            "not stress"      "stress"
```

- The tree isn't written by hand. It **learns its questions** from training windows: at each step
  it picks the question that best separates stress windows from calm ones.

**Why 200 trees (a "forest")**
- One tree can be fooled by quirks in its data.
- Each of the 200 trees learns from a **random sample** of the windows and may only look at a
  **random handful** of the 99 numbers at each question → 200 slightly different opinions.
- **Score = share of trees voting "stress".** 44 of 200 → 0.22.
  (Technically each tree gives a small probability and they're averaged; "share of votes" is the
  right way to think about it.)
- **Called "stressed" if score ≥ 0.5.**

**Three small steps before voting** (in `classifier.py`)
1. **Fill empty values** with the median of the training people (the 10 breathing gaps).
2. **Rescale** all numbers to a similar range. Trees don't need it; harmless.
3. **Balanced class weights:** only 1 in 5 training windows is stress → stress windows count
   extra, otherwise the forest learns "always say calm" (right 78% of the time, useless).

**The fair test: leave-one-person-out**
- To score S14, train on the **other 14 people only**. S14 is a complete stranger, like a new
  app user.
- Repeat for each of the 15 people → every window gets a score from a model that never saw that person.

**Why a random forest** (and not something else)

| Option | Why / why not |
|---|---|
| **Random forest** (chosen) | Works well on small tables of numbers; handles odd, non-linear patterns; barely needs tuning (so no risk of tuning on the test person); gives a score from 0 to 1; tells us which numbers matter |
| Deep learning | Needs far more than 15 people; hard to explain |
| Gradient boosting (LightGBM) | Often a bit better, but needs tuning → more leakage risk. Removed as unused. |
| Simple linear model | Easy, but can't capture "high sweat AND high heart rate" combinations as well. Could be added as a baseline comparison. |

- Settings: 200 trees, balanced weights, **seed 42** (fixes the randomness → same 200 trees every run).
- Known weakness: forest scores aren't true probabilities ("0.7" isn't exactly a 70% chance). It
  matters for the gate in RQ4.

**What we checked by hand:** trained on 14 people (1,283 windows), tested on S14 (94 windows)

| S14 window | Real phase | Trees voting stress | Score | Called | scores.csv |
|---|---|---|---|---|---|
| 10 | baseline | **0 of 200** | 0.000 | not stressed (correct) | 0.0 |
| 38 | **stress** | **44 of 200** | 0.220 | not stressed (**missed**) | 0.22 |

- Our hand-built model gives **exactly** the scores in `scores.csv` → reproduced.
- The stressed minute gets 44 votes vs 0 for the calm one → the model **does** notice, just not
  enough to cross 0.5. That's the S14 story (Steps 5 and 7).

**What the forest relies on most** ("importance" = how much a number helped separate stress from
calm; all 99 add up to 1)

| Rank | Number | Meaning | Importance |
|---|---|---|---|
| 1 | `chest_acc_iqr` | chest movement, how varied | 0.101 |
| 2 | `chest_acc_std` | chest movement, how jumpy | 0.081 |
| 3 | `wrist_bvp_hr_std` | wrist heart rate, how much it changes | 0.067 |
| 4 | `chest_ecg_hr_mean` | heart rate | 0.060 |
| 5 | `wrist_eda_range` | wrist sweat, lowest to highest | 0.056 |
| 6 | `wrist_eda_scr_amp_mean` | wrist sweat bursts, size | 0.048 |
| 7 | `wrist_eda_std` | wrist sweat, how jumpy | 0.032 |
| 8 | `wrist_eda_median` | wrist sweat, typical level | 0.026 |

- **Top 2 are movement**: people gesture and shift during the speech.
- **But** removing all movement barely changes performance (Step 6). Movement is **useful but not
  needed**: without it, heart rate and sweat carry the same information.
- 4 of the top 8 are **wrist sweat** → matches Step 3 (wrist sweat 3x higher under stress for S2).
- Caveat: this kind of importance slightly favours numbers with many distinct values; read it as
  "roughly what matters", not an exact ranking.

**The output file `handoff/scores.csv`**
- One row per window x test type (fair / random) x sensor set (wrist / chest / all).
- 1,377 x 2 x 3 = **8,262 rows**. Columns: person, window, test type, sensors, real answer, score.

- **Show:** one tree drawing → "200 trees vote" → S14's two windows (0 vs 44 votes).

---

## Step 5. The report card: RQ1 and RQ2

**What we ran:** `python scripts/run_pipeline.py --stage metrics`
- Reads `handoff/scores.csv` → grades every person → saves `artifacts/metrics_per_subject.csv`
  (90 grades = 15 people x 2 tests x 3 sensor sets) and `artifacts/metrics_summary.csv` (6 lines).
- Code: `per_subject_metrics` and `summarize` in `src/data_model/evaluate.py`.

### Definitions

**LOSO = Leave One Subject Out (the fair test)**
- Take one person out → train on the other 14 → score the person left out.
- Repeat for all 15 people → 15 models.
- Every window is scored by a model that **never saw that person**, like a brand-new app user.
- This is our **headline** result.

**Random split (the unfair test, for contrast only)**
- Shuffle all 1,377 windows from everyone into 5 groups; train on 4, test on 1; repeat.
- A window's near-twin neighbour (they share 30 s, Step 2) is often in training → the model
  partly "recognises" the person → looks better than it really is.
- We only report it to **show** how much it flatters the model.

**Balanced accuracy ("does the alarm ring at the right times?")**
- Uses the 0.5 line: score ≥ 0.5 = "stressed".
- = (share of stressed minutes caught + share of calm minutes left alone) ÷ 2.
- Example: 10 minutes, 2 stressed, 8 calm. Caught 1 of 2 = 50%. Left alone 7 of 8 = 87.5%.
  Balanced accuracy = (50% + 87.5%) ÷ 2 = **0.69**.
- Why not plain accuracy? A lazy model that always says "calm" is right 8 of 10 = 80%, but
  catches 0% of stress. Balanced: (0% + 100%) ÷ 2 = **0.50** → exposed as useless.
- **0.5 = useless, 1.0 = perfect.**

**AUROC ("does the model know stress from calm at all?")**
- Ignores the 0.5 line completely. Only asks: do stressed minutes get **higher scores** than calm ones?
- How: take every pair (one stressed minute, one calm minute). Stressed scored higher → 1 point;
  tie → ½; lower → 0. AUROC = points ÷ number of pairs.
- Example: stressed scores 0.9, 0.6, 0.3; calm scores 0.1, 0.2, 0.4, 0.6 → 3 x 4 = 12 pairs.
  0.9 beats all 4 → 4. 0.6 beats 3, ties 1 → 3.5. 0.3 beats 2 → 2. Total 9.5 ÷ 12 = **0.79**.
- Meaning: pick a random stressed and a random calm minute → 79% of the time the stressed one
  scores higher.
- **0.5 = coin flip, 1.0 = stressed always scores higher.**
- In one line: balanced accuracy checks the **alarm**; AUROC checks the **detector**.

**mean / worst / std**
- **mean** = the average person. **worst** = the weakest single person. **std** = how unequal
  people are (bigger = more unequal).

### The result

| Test | Sensors | Avg bal. acc | **Worst bal. acc** | Spread (std) | Avg AUROC | Worst AUROC |
|---|---|---|---|---|---|---|
| **Fair (LOSO)** | **all** | **0.90** | **0.50** (S14) | 0.14 | 0.995 | 0.95 (S9) |
| Fair (LOSO) | chest | 0.85 | 0.55 (S10) | 0.15 | 0.990 | 0.95 |
| Fair (LOSO) | wrist | 0.85 | 0.50 (S14) | 0.13 | 0.982 | 0.90 |
| Unfair (random) | all | **0.98** | 0.88 | 0.03 | 1.000 | 1.00 |
| Unfair (random) | chest | 0.98 | 0.89 | 0.03 | 0.999 | 1.00 |
| Unfair (random) | wrist | 0.96 | 0.85 | 0.04 | 0.997 | 0.98 |

**Per person, fair test, all sensors** (balanced accuracy)

| Person | S14 | S15 | S2 | S9 | S10 | S4 | S13 | S17 | S3 | S8 | S11 | S7 | S5 | S6 | S16 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Bal. acc | **0.50** | 0.76 | 0.79 | 0.82 | 0.89 | 0.92 | 0.93 | 0.95 | 0.97 | 0.98 | 0.99 | 0.99 | 1.00 | 1.00 | 1.00 |

### How we know S14 is the worst (run it live)

`--stage metrics` prints only the summary (worst = 0.500, no name). The per-person grades are
saved in `artifacts/metrics_per_subject.csv`. To see them, worst first:

```
python -c "
import pandas as pd
m = pd.read_csv('artifacts/metrics_per_subject.csv').query(\"split=='loso' and sensor_config=='all'\")
print(m.sort_values('balanced_acc')[['subject_id','n','pos_rate','balanced_acc','auroc']].round(3).to_string(index=False))
"
```

| Person | Windows (n) | Share stress | Balanced acc | AUROC |
|---|---|---|---|---|
| **S14** | 94 | 0.223 | **0.500** | **1.000** |
| S15 | 93 | 0.226 | 0.762 | 0.993 |
| S2 | 87 | 0.218 | 0.789 | 1.000 |
| S9 | 91 | 0.220 | 0.825 | **0.948** |
| S10 | 95 | 0.232 | 0.886 | 0.998 |
| S4 | 90 | 0.211 | 0.921 | 1.000 |
| S13 | 93 | 0.226 | 0.929 | 0.995 |
| S17 | 93 | 0.247 | 0.949 | 0.996 |
| S3 | 89 | 0.225 | 0.975 | 1.000 |
| S8 | 91 | 0.231 | 0.976 | 1.000 |
| S11 | 93 | 0.226 | 0.986 | 1.000 |
| S7 | 92 | 0.207 | 0.993 | 1.000 |
| S16 | 92 | 0.217 | 1.000 | 1.000 |
| S5 | 92 | 0.217 | 1.000 | 1.000 |
| S6 | 92 | 0.217 | 1.000 | 1.000 |

- Every person has ~22% stress windows (share stress 0.21–0.25) → same study for everyone.
- **S14's row is the whole story:** balanced accuracy 0.500 (alarm never rings) next to AUROC
  1.000 (detector perfect).
- **S9 is different:** the lowest AUROC (0.948) → its stressed and calm scores overlap → the
  model genuinely struggles there (comes back in Step 7: S9 can't be rescued by a line).
- 9 of 15 people have AUROC 1.000.

- S14: catches **0%** of their stress, leaves **100%** of calm alone → (0 + 100) ÷ 2 = 0.50.
- S15, S2, S9: miss about half their stress.
- Almost all mistakes are **missed stress**, not false alarms: calm is left alone 97–100% of the time for everyone.

### What it means

- **RQ1 (new people):** the unfair test says 0.98; the fair test says **0.90**. The honest
  number for a new user is 0.90. The gap comes from near-twin windows.
- **RQ2 (everyone equal?):** no. Average 0.90 hides S14 at **0.50**. People are 4x more unequal on
  the fair test (spread 0.14 vs 0.03).
- **The surprise:** AUROC is near 1.0 for everyone, even S14 (1.00). The model **knows** stress
  from calm for every person; **the 0.5 line is just in the wrong place** for some. → RQ3 (Step 7).
- **Sensors:** wrist only 0.85 ≈ chest only 0.85 < all 0.90 → a smartwatch alone is almost as
  good as the lab setup. And different people fail on different sensors (S14: chest 0.95 but all 0.50).
- **Small samples:** each person has only ~20 stress windows, so one window ≈ 5 points of
  "stress caught". Per-person numbers are noisy.

- **Show:** chart 1 (fair vs unfair) and chart 2 (every person, S14 in orange).

---

## Step 6. The movement check: is the model fooled by movement?

**Why we did it**
- During the stress test people **talk and gesture**; in the other phases they mostly **sit still**.
- Worry: the model might learn a lazy shortcut, **"moving = stressed"**. Useless in real life
  (walking to the bus isn't stress).
- Also: movement was the forest's **top** number (Step 4). Suspicious, so we tested it.

**What we did**
- Trained the model twice per sensor set, both with the fair test (LOSO):
  - **with movement**: all numbers (all sensors: 99)
  - **without movement**: minus the 16 movement numbers (8 chest + 8 wrist) → all sensors: 83
- First on Colab (official file `handoff/movement_check.csv`), then turned into a script:
  `python scripts/run_movement_check.py` (about 30 s on a laptop).
- Bonus check in the script: the "with movement" scores vs `scores.csv` → **identical on Colab**
  (difference 0.0000) → we reproduced the teammate's results exactly from raw data.

**The result** (official Colab run, balanced accuracy and AUROC, average person)

| Sensors | Bal. acc with → without | AUROC with → without | Worst AUROC with → without |
|---|---|---|---|
| **all** | 0.899 → **0.888** | 0.995 → **0.998** | 0.948 → **0.987** |
| chest | 0.854 → 0.852 | 0.990 → 0.987 | 0.947 → 0.938 |
| wrist | 0.854 → 0.860 | 0.982 → 0.983 | 0.897 → 0.874 |

- Worst person (balanced accuracy) stays 0.50 either way (S14).
- Laptop re-run: within ±0.003 of these (all: 0.886). Mac vs Colab rounding, same conclusion.

**What it means**
- **Removing all movement barely changes anything** → the model reads the **body's stress
  reaction** (heart rate, sweat), not people moving.
- Fits with Step 4: movement is the forest's favourite number, but **useful, not needed**.
  Without it, heart rate and sweat carry the same information.
- **S9 even improves** without movement (AUROC 0.948 → 0.992 per person) → for S9, movement was noise.
- **Caveat:** this rules out the movement **sensors**. Standing and talking also raise heart rate a
  bit by themselves; this data can't fully separate that.

- **Show:** chart 5 (with vs without movement, side by side).

---

## Step 7. RQ3: a personal alarm line for each person

**Why**
- Step 5: one alarm line (0.5) for everyone → S14's stressed scores (~0.2) never reach it → worst
  person **0.50**.
- But AUROC ≈ 1.0 for everyone → the model **knows**; the line is in the wrong place for some people.
- RQ3 question: **can a little per-person calibration rescue the worst person and make people
  more equal?** (The goal isn't a higher average; it's the worst person and the spread.)

**What we ran:** `python scripts/run_reliability.py --stage rq3`
- Code: `src/reliability/baseline.py` (rewritten), runner in `scripts/run_reliability.py`.
- Input: fair-test (LOSO) scores, all sensors, from `handoff/scores.csv`.
- Output: `artifacts/rq3_per_person.csv`, `artifacts/rq3_summary.csv`.

### The three methods

**1. One line for everyone (`global`)**: the "before"
- Stressed if **score ≥ 0.5**.
- S14: stressed scores ~0.2 → never → missed.

**2. Personal calm baseline, no questions (`label-free`)**: our team's idea
- **baseline(person)** = average score of their **first 10 windows** (≈ first 5 min of wearing).
- **rise** = score − baseline(person).
- Stressed if **rise ≥ R**.
- **R is the same for everyone (0.15)** and is chosen using the **other 14 people only**: try
  R = 0.05, 0.10 ... 0.40 and keep the one that works best on them. The person being graded never
  helps choose it.
- S14: baseline = 0.005 → personal line = 0.005 + 0.15 = **0.155**. Stressed minute 0.22 →
  rise 0.215 ≥ 0.15 → **caught**. Calm minute 0.00 → rise −0.005 → left alone.
- Assumption: the first minutes of wearing are calm. True in WESAD (baseline always first).
  Real app: "wear it during a calm moment first".
- Why first 5 minutes and not all calm windows? Using all the real calm labels means using the
  answers we're grading with (cheating), and nobody tells a real app which minutes are calm. We
  tested both: same result (0.94 vs 0.94), so the honest version costs nothing.
- Why R isn't just a guessed number like 0.30: S14's stress only rises ~0.20 above their calm →
  a +0.30 rule still misses them (0.55). Let the data choose → 0.15.

**How the calm level is "learned"**: not machine learning, just an average of the model's scores
- S14's first 10 scores: 0.015, 0, 0, 0, 0.01, 0.025, 0, 0, 0, 0 → average **0.005** → line **0.155**
- S11's first 10 scores: 0.09, 0.045, 0.075, 0.055, 0.05, 0.055, 0.23, 0.135, 0.11, 0.065 →
  average **0.091** → line **0.24**
- Uses the model's **scores**, not raw heart rate or sweat. No labels used.

**How R = 0.15 was chosen** (trial and error; average grade over all 15 people for each R)

| R | 0.05 | 0.10 | **0.15** | 0.20 | 0.25 | 0.30 | 0.35 | 0.40 |
|---|---|---|---|---|---|---|---|---|
| Avg grade | 0.918 | 0.943 | **0.949** | 0.930 | 0.920 | 0.917 | 0.903 | 0.896 |

- Too small → rings at tiny bumps (false alarms). Too big → small-stress people (S14) never cross it.
- Fair version used in the results: for each person, R is picked on the **other 14 only**. It came
  out **0.15 for all 15 people** → stable, doesn't depend on who's left out.
- **Chart 6** (`artifacts/figures/fig6_rq3_choosing_R.png`, made by `scripts/make_figures.py`) shows the test:
  - Left: **0.15 is best for both the average person (0.949) and the worst person (0.839)**. The
    worst person collapses above 0.20 (0.71 at 0.20, 0.55 from 0.30), because small-stress
    people like S14 stop crossing their line.
  - Right: as R grows, **stress caught falls** (0.98 → 0.80) and **calm left alone rises**
    (0.85 → 0.99). The two lines **cross at 0.15** (both ≈ 0.95) → the balance point.

**3. Ask the person a few times (`label-budgeted k`)**
- The person tells us **k stressed** and **k calm** moments (k = 1, 2, 3, 5).
- **line(person)** = (average score of their stressed examples + average score of their calm
  examples) ÷ 2.
- Stressed if **score ≥ line(person)**.
- S14 with k = 1: stressed example ~0.2, calm example ~0.0 → line ≈ **0.1** → stressed caught,
  calm left alone.
- Fair rules: the asked-about windows **and their direct neighbours** (near-twins, Step 2) are
  left out of grading. Which moments are asked is random → **repeated 30 times**, averaged.

**What k means**
- k = 1 → 1 stressed + 1 calm answer. k = 2 → 2 + 2 (each group averaged first), and so on.
- S14 with k = 2, e.g. stressed 0.18 and 0.25 → 0.215; calm 0.00 and 0.03 → 0.015 →
  line = (0.215 + 0.015) ÷ 2 = 0.115.
- More answers → a more reliable picture of your typical stress and calm. But the gain is small:
  worst person 0.83 (k = 1) → 0.86 (k = 5).

**Why halfway?**
- It's "which group are you closer to?". S14's stress looks like ~0.2, their calm ~0.0.
- The halfway point (0.1) is exactly the border: above it you look more like your stressed self,
  below it more like your calm self.
- No R needed: the app has seen **both** your calm and your stress, so it can place the line itself.

**Why we need this method at all**
- RQ3 asks about **three** kinds of calibration (team plan): none (method 1), without asking the
  person (method 2), and **by asking the person a little** (method 3, a "label budget").
- Real-world question: *"If the app asked just once or twice 'are you stressed right now?', how
  much better would it get?"*
- We can't test that for real: no users, no app, no new data.

**How it works without real answers: a simulation**
- Story: in a real app, S14 taps "yes, stressed" once and "no, calm" once → the app puts their
  line halfway.
- We don't have the real S14 to ask. But WESAD already knows which minutes were truly stressed
  (the labels). So we **play the user**:
  - pick a random minute where S14 was really stressed → pretend S14 tapped "yes" then;
  - pick a random minute where S14 was really calm → pretend S14 tapped "no" then;
  - their scores set the line.
- Don't grade on those minutes (like a teacher who told you the answer to question 5 can't grade
  you on question 5), or on their near-twin neighbours.
- Repeat 30 times with different random minutes (like rolling dice 30 times, not once), average.
- Code: `budget_line()` picks the answers and sets the line; `_graded_mask()` removes the asked
  windows + neighbours; `evaluate_rq3()` repeats 30 times (all in `src/reliability/baseline.py`).

**Three simulated tries for S14, by hand** (k = 1)

| Try | Pretend "yes" at | Pretend "no" at | Line | Graded on | Grade |
|---|---|---|---|---|---|
| 1 | window 47 (score 0.18) | window 37 (0.00) | 0.092 | 78 windows | 1.000 |
| 2 | window 53 (0.16) | window 90 (0.00) | 0.080 | 78 windows | 1.000 |
| 3 | window 38 (0.22) | window 10 (0.00) | 0.110 | 79 windows | 1.000 |

- The line always lands in the gap between S14's calm (~0.0) and stress (~0.2).
- 78 graded = 94 − 10 warm-up − 6 (2 asked windows + their neighbours). Try 3: window 10's
  neighbour 9 was already warm-up → only 5 removed → 79.
- Over all 30 tries S14 averages **0.957**: some unlucky picks (e.g. a weak stressed minute at
  0.12) put the line slightly off.

**What the simulation tells us**

| Question | Answer |
|---|---|
| Does asking help the worst people? | Yes: S14 0.50 → 0.96 with one question each way |
| Does it fix method 2's false alarms? | Yes: S11 0.84 (method 2) → 0.98 |
| How many questions are enough? | One each way gets almost everything (worst 0.83; five each way: 0.86) |

- App-design take-away: asking once when stressed and once when calm is a tiny effort for the
  user and fixes both missed stress and false alarms.
- **Limitation:** simulated answers assume the user answers truthfully at a random moment. Real
  users might answer late or wrongly → real results could be a bit lower.

**Fair grading for all methods**
- First 10 windows per person = warm-up for method 2 → **not graded for any method**.
- Each person graded with balanced accuracy → average, worst, spread.

### The result

| Method | Average | **Worst** | Spread | Stress caught | Calm left alone |
|---|---|---|---|---|---|
| One line for everyone | 0.899 | **0.500** (S14) | 0.136 | 80.3% | 99.6% |
| **Personal baseline (no questions)** | **0.949** | **0.839** (S11) | **0.050** | **95.1%** | 94.7% |
| Ask 1 + 1 | 0.952 | 0.830 (S9) | 0.050 | 92.8% | 97.6% |
| Ask 2 + 2 | 0.955 | 0.835 (S15) | 0.053 | 92.5% | 98.6% |
| Ask 3 + 3 | 0.961 | 0.858 (S9) | 0.045 | 93.3% | 98.8% |
| Ask 5 + 5 | 0.961 | 0.861 (S15) | 0.047 | 93.2% | 98.9% |

**Per person** (balanced accuracy)

| Person | One line | Personal baseline | Ask 1+1 | Ask 5+5 |
|---|---|---|---|---|
| **S14** | **0.500** | **0.929** | 0.957 | **1.000** |
| S15 | 0.762 | 0.952 | 0.858 | 0.861 |
| S2 | 0.789 | 0.974 | 0.969 | 0.960 |
| S9 | 0.825 | 0.842 | 0.830 | 0.866 |
| S10 | 0.886 | 0.977 | 0.932 | 0.957 |
| S4 | 0.921 | 1.000 | 0.965 | 0.977 |
| S13 | 0.929 | 0.929 | 0.917 | 0.906 |
| S17 | 0.948 | 0.942 | 0.942 | 0.950 |
| S3 | 0.975 | 0.992 | 0.983 | 0.991 |
| S8 | 0.976 | 1.000 | 0.978 | 0.982 |
| S11 | 0.984 | **0.839** | 0.981 | 0.987 |
| S7 | 0.992 | 0.960 | 0.988 | 0.987 |
| S16 | 1.000 | 0.968 | 1.000 | 1.000 |
| S5 | 1.000 | 0.984 | 0.999 | 1.000 |
| S6 | 1.000 | 0.952 | 0.982 | 0.991 |

### What it means: three stories

1. **Rescued:** S14 0.50 → 0.93 / 1.00; S15 0.76 → 0.95; S2 0.79 → 0.97; S10 0.89 → 0.98. All
   "the line was in the wrong place" cases.
2. **Small cost:** with no questions, some good people get a bit worse through false alarms.
   S11 0.98 → 0.84: S11's line = 0.09 + 0.15 = 0.24, but S11's calm minutes score up to 0.58 →
   calm left alone drops from 97% to 68%. S11's calm scores by phase (typical / highest):
   baseline 0.06 / 0.36, funny videos **0.24** / 0.48, **meditation 0.26 / 0.58** → about half
   of S11's meditation minutes cross the line. (S11's stress is 0.74–0.98, very clear.) Asking once fixes it (0.98),
   because the app has then seen S11's real stress level: (0.94 + 0.06) ÷ 2 ≈ 0.50.
   - Lesson: without asking, we only know your calm, not how big **your** stress looks. The
     +0.15 is a compromise: too small for S11, right for S14.
3. **Can't be rescued:** S9 stays 0.83–0.87 in every method. S9's stressed and calm scores
   overlap (lowest AUROC, 0.95) → no line can separate them.
   - Lesson: personal lines fix "**the line is wrong**", not "**the model doesn't know**". S9
     needs a better model (e.g. per-person normalisation of the 99 numbers; S9 also improved
     without movement, Step 6).

### The RQ3 answer
- **Yes.** Personal calibration lifts the **worst person from 0.50 to about 0.84** and makes
  people **about 3x more equal** (spread 0.14 → 0.05). The average rises too (0.90 → 0.95).
- **Asking once each way is almost as good as asking five times**, and avoids hurting people who
  already worked well.

### What we tried that didn't work (worth mentioning)
- **"Learn your normal as you go"** (compare each minute with all your past minutes): **worse**
  (average ~0.78). Once stress starts, the stressed minutes enter the "past" → the app gets used
  to your stress and stops ringing. Like a smoke alarm that adjusts to the smoke.

### What we fixed from the first draft
- The draft's "no questions" version used each person's **whole recording**, including the
  future, to set their line → looked great (0.97) but is cheating.
- The draft's "ask the person" version took the **first 10 windows** as the asked moments. Those
  are always baseline → it **never saw a stressed example** (checked: 0 stress windows in the first
  10 for all 15 people; first stress window is #36–61). It also graded on those same windows.

### Honest limitations
- WESAD has baseline first and ~1 in 5 stress for everyone → easier than real life.
- R and the "first 5 minutes" assumption are lab-friendly; a real app needs a calm calibration moment.
- Per-person numbers rest on ~20 stress windows each → noisy.

- **Show:** chart 3 (S14's dots with both lines), chart 6 (how R = 0.15 was chosen), chart 4 (before/after per person).

---

## Step 8. What's not done yet: the gate (RQ4) and the app (Part C)

Both exist as **first drafts** (written by Avijeet). We ran them once; we haven't reworked them.

### The gate (RQ4): "should the app sometimes stay quiet?"

**What exists** (`src/reliability/gate.py`, run with `python scripts/run_reliability.py --stage compare`)
- Per minute: adjusted score ≥ **0.6** → **act** (suggest something); 0.45–0.6 → **watch** (unsure,
  wait); below → **none**.
- A comparison that counts **false alarms** (nudging a calm person) and **missed stress**.

**What's wrong with it**

| Problem | In plain words |
|---|---|
| 0.6 is typed in, not learned | Nobody tested whether 0.6 is a good value (like R before chart 6) |
| Not really "risk-controlled" | The plan wants a guarantee, e.g. "at most 5% false alarms". There is none |
| Unfair comparison | "Always act" is really "act at 0.5" on raw scores vs "gate at 0.6" on adjusted scores: two things change at once |
| The question needs a rethink | With one line for everyone, the model makes almost no false alarms (4 of 1,070 calm minutes) → a gate that silences nudges can only add missed stress |

**Why RQ3 makes RQ4 meaningful**
- Personal lines catch much more stress (80% → 95%) but add some false alarms (calm left alone
  99.6% → 94.7%, the S11 case).
- → The gate now has a real job: **cut those false alarms without losing the stress we gained.**

**What should be done** (owner B, milestone M4, Dec 11)
1. Compare 4 policies per person: **always nudge** (every minute), **one line (0.5)**, **personal
   line (RQ3)**, **personal line + gate**.
2. Grade each on: stress caught, false alarms, **nudges per hour**, worst person.
3. Choose the gate's threshold honestly: on the other 14 people, so false alarms stay under a target (e.g. 5%).
4. Simple gate idea to test: act only if **2 minutes in a row** are high (real stress lasts
   minutes; a laugh is a blip).
5. Note: forest scores aren't true probabilities ("0.7" ≠ 70%), so a threshold should be chosen
   from data, not assumed.

### The app (Part C): survey + suggestion

**What exists** (`src/recommender/`)
- `survey.py`: 3 questions (minutes free? can leave desk? preference?).
- `recommender.py`: rules → breathing exercise / short break / brief walk / mindfulness / nothing.
- `app.py`: a small demo website (Streamlit).
- Ran on the draft gate's decisions: 311 "act" → 311 x "brief walk" (we gave everyone "5 min free,
  can leave desk"); 1,066 x "no intervention".

**What should be done** (owner C, milestone M4, Dec 11)
1. Connect to the real `decisions.csv` once the gate is settled → the "signals in, suggestion
   out" demo.
2. Check the survey and suggestions against what the team designed (the status doc says these
   aren't the team's version yet).
3. Open the demo once: `streamlit run src/recommender/app.py`.
4. Be honest: WESAD has no data on whether a walk or breathing **helps** → no effectiveness claims. Prototype only.

---

## Step 9. What changed today, what we found, what's next

### Files changed on branch `nithya/rq3-and-friday`

| File | Change | Why |
|---|---|---|
| `src/reliability/baseline.py` | **Rewritten**: 3 honest RQ3 methods (one line, personal calm + R, ask k times), fair grading | The draft used future data, and its "ask" method never saw a stressed example |
| `scripts/run_reliability.py` | New `--stage rq3`; `--mock` writes to `artifacts/`; `--budget` default 1 | Run the RQ3 contest; fake data can't land in `handoff/` |
| `scripts/run_movement_check.py` | **New**: retrains with / without movement | The Colab test, saved so anyone can rerun it (~30 s) |
| `scripts/make_figures.py` | **New**: charts 1–6 | Friday visuals, rebuildable |
| `handoff/windows.parquet` | **New**: 1,377 x 104, from the Colab run | Nobody needs the 20-minute Colab step again |
| `handoff/movement_check.csv` | **New**: movement test scores (Colab) | Source for chart 5 |
| `requirements.txt` | Pinned the Colab versions; removed LightGBM and jupyterlab | Old pins couldn't install (neurokit2 vs numpy) and didn't match the scores |
| `config.example.yaml` | Removed unused `negatives` and `model.type` | Never read by the code |
| `src/data_model/classifier.py` | Removed the unused LightGBM option | Scores verified identical (difference 0.0) |
| `.gitignore` | Removed lines for folders that don't exist | Tidy |
| `README.md`, `scripts/run_pipeline.py` | Fixed paths (`handoff/`), Mac setup, Python 3.11–3.13 | Docs said `artifacts/`; setup was Windows-only |
| `notes/presentation_notes.md` | **New**: this file | Team walkthrough + Friday |

### What we found

- **Reproduced the teammate's results exactly** from raw data on Colab (difference 0.0000).
- **RQ1:** fair test 0.90 vs flattering random test 0.98.
- **RQ2:** worst person S14 at 0.50; spread 0.14 vs 0.03.
- **AUROC ≈ 1.0 for everyone** → the model knows; the line is wrong for some people.
- **Movement check:** without movement, 0.90 → 0.89 → the model reads the body, not movement.
- **RQ3:** personal lines → worst person 0.50 → ~0.84, spread 0.14 → 0.05; asking once is enough.
- **Bugs found and fixed:** RQ3 draft (future data; never saw a stressed example); `--mock`
  writing fake decisions into `handoff/`; `requirements.txt` uninstallable; outdated README paths.

### Reproducibility

- Seed 42 everywhere; `requirements.txt` = the exact Colab versions that made `scores.csv`.
- Colab reproduces `scores.csv` exactly. A Mac differs by at most 1–2 tree votes (≤ 0.02, mean
  0.0008) from processor rounding; conclusions unchanged.
- **The committed files in `handoff/` are the official numbers.**

### Open questions for the team

1. OK to keep `windows.parquet` and `movement_check.csv` committed in `handoff/`?
2. Colab notebook fixes: download path (`artifacts/` → `handoff/`), checkout `main`, drop the
   unofficial fallback WESAD link. Who does it?
3. Who is A / B / C? (I'm happy to take B: RQ3 + RQ4.)

### Next steps

1. **RQ4 gate** (Step 8): fair 4-policy comparison, honest threshold, "2 minutes in a row" idea.
2. Regenerate the real `decisions.csv` → connect the app → end-to-end demo (M4, Dec 11).
3. Optional: personal normalisation of the 99 numbers (might help S9); finer R grid (0.01 steps).
4. Report: one section per RQ, using charts 1–6.

### Commands cheat sheet (laptop, in order)

```
python -m pytest -q                                  # format checks
python scripts/run_pipeline.py --stage metrics       # RQ1/RQ2 report card
python scripts/run_movement_check.py --out artifacts/movement_check_local.csv   # movement test (~30 s)
python scripts/run_reliability.py --stage rq3        # RQ3 contest
python scripts/run_reliability.py --stage compare    # RQ4 draft
python scripts/run_recommender.py --mock --minutes 5 --can-leave-desk   # app rules (fake decisions)
python scripts/make_figures.py                       # charts 1–6 -> artifacts/figures/
```
