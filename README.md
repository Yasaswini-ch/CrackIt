# ⚗️ CrackIt
> **Big equations, broken into small pieces.**

Built for my brother, a diploma student in petrochemical engineering who finds heavy maths boring.
CrackIt takes an engineering equation and breaks it into small, friendly parts, with a petrochemical
plant example every time, and lets you play with the numbers live.

---

## What it does

Type an equation name (or pick a quick card, or upload a photo of your notes) and CrackIt shows:

1. **The formula**, rendered properly (Ergun's viscous and inertial terms are colour-labelled)
2. **What it's for**, with a real plant example
3. **Crack the Symbols**, a table of every symbol, its meaning and its unit, plus an **Interactive Focus** picker for any one symbol
4. **Worked example**, small round numbers, one step per line
5. **Try it live**, a calculator pre-filled with the worked-example values. Change a number and the answer updates instantly
6. **What happens if...?**, one sentence on how changing a variable affects the result
7. **Try this**, a practice question. Type your answer and the local model checks it

There is also a **History** screen to reopen anything you cracked in the current session.

### Built-in equations

| Equation | Topic |
|----------|-------|
| Ergun Equation | Packed-bed pressure drop |
| Q = mCpΔT | Heat duty |
| Bernoulli | Pipe flow |
| Raoult's Law | Vapor-liquid equilibrium |
| Reynolds Number | Flow regime |
| Fick's Law | Diffusion |
| Darcy–Weisbach | Pipe friction losses |
| Ideal Gas Law | Gas behaviour |
| Arrhenius Equation | Reaction kinetics |
| Antoine Equation | Vapor pressure |
| LMTD | Heat exchanger design |

The explanations, worked examples and calculators are written by hand and computed in Python, so
they work offline and give the same correct numbers every time. The local model is used only for
checking typed practice answers and for reading equations from photos.

---

## Requirements

- Python 3.9+
- [Ollama](https://ollama.com) running locally with `gemma3:4b` pulled (needed for answer-checking and photo upload; everything else works without it)

```bash
ollama pull gemma3:4b
```

---

## Setup

```bash
git clone <your-repo>
cd crackit

pip install -r requirements.txt   # needs Gradio 6

ollama serve                      # in a separate terminal

python app.py
```

Then open **http://localhost:7860** in your browser.

---

## Usage

| Input | What to do |
|-------|-----------|
| Equation box | Type a name such as `Bernoulli`, `Q = mCpΔT`, `vapor pressure`, or `lmtd`. A live formula preview appears when it matches |
| Quick Start cards | Click any card to open that equation |
| Photo upload | Upload a photo of a known equation. The local model identifies it |
| Try it live | Edit the numbers under "Try it live" to see results update |
| Practice answer | Type your attempt under "Try This" and press Check Answer |

If the text doesn't match a built-in equation, CrackIt tells you and shows the Ergun Equation instead.

---

## How the model is used

- **Model:** `gemma3:4b` (open-weight, runs fully on your laptop via Ollama)
- **Why open-source AI?** It runs offline with zero data leaving your machine. A closed API would need internet, cost money per query, and potentially log your homework. With an open-weight model you can fine-tune it later for specific petrochemical curricula.
- **Used for:** checking typed practice answers and identifying an equation from a photo. If Ollama isn't running, the app says so and the rest keeps working.

---

## Adding an equation

Everything lives in `app.py`:

1. Add an entry to `EQUATION_INFO` (tag, LaTeX, purpose, symbols, worked example, what-if, practice question)
2. Add a calculator function and register it in `CALCS` (inputs with defaults, plus a function that returns the results)
3. Optionally add search words to `ALIASES`

Its quick-start card and calculator then appear automatically.

---

## Project structure

```
crackit/
├── app.py            # UI, equation data, calculators and model calls (single file)
├── run_tests.py      # standalone prompt test against the local model
├── requirements.txt
└── README.md
```

---

## Built for the Hacktoberfest 2026 Weekend Challenge
*Theme: Build for a Friend · Open-source AI at the core*

Made with ❤️ using [Gradio](https://gradio.app) + [Ollama](https://ollama.com) + [Gemma 3](https://ai.google.dev/gemma)
