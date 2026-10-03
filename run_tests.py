import sys
import requests
import json

# Ensure stdout handles UTF-8
sys.stdout.reconfigure(encoding='utf-8')

SYSTEM = (
    "You explain engineering equations to a diploma student who finds maths boring. "
    "Be short, concrete, and friendly. Always use petrochemical plant examples. "
    "Never exceed 150 words. Use plain-text formulas, no LaTeX. "
    "Do NOT use Greek symbols (write rho as rho, delta as d). "
    "Follow the 4-part format exactly:\n"
    "1. What it's for: ONE sentence with a petrochemical example.\n"
    "2. Symbols: each symbol in plain words, one line each.\n"
    "3. Worked example: small round numbers, 3-5 steps, one line per step.\n"
    "4. Try this: one practice question.\n"
    "If the student types an answer, check it and explain any mistake in 2 sentences max. "
    "If an image is unreadable or the equation is unclear, say so in one sentence "
    "and ask him to retype it instead of guessing."
)

equations = ["Q = m * Cp * dT", "Bernoulli's equation", "Raoult's law"]

for eq in equations:
    print(f"\n{'='*60}\nEQUATION: {eq}\n{'='*60}")
    resp = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "gemma3:4b",
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": eq}
            ],
            "stream": False
        },
        timeout=180
    )
    content = resp.json().get("message", {}).get("content", "")
    print(content)
    words = len(content.split())
    print(f"\n[Word count: {words} | Limit: 150]")
