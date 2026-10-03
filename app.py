import gradio as gr
import requests
import base64
import re
import html
import math

# ── Config ─────────────────────────────────────────────────────────────────────
MODEL_NAME = "gemma3:4b"
OLLAMA_URL = "http://localhost:11434"

EQUATION_INFO = {
    "Ergun Equation": {
        "tag": "Packed Bed Flow",
        "latex": r"$$\frac{\Delta P}{L} = \frac{150\mu(1-\epsilon)^2 v_s}{\epsilon^3 d_p^2} + \frac{1.75\rho(1-\epsilon)v_s^2}{\epsilon^3 d_p}$$",
        "for": "Predicts the pressure drop through a packed bed, such as catalyst beds used in petrochemical reactors and hydrotreaters.",
        "symbols": [
            ("ΔP", "Pressure drop", "Pa"),
            ("L", "Bed length", "m"),
            ("μ", "Fluid viscosity", "Pa·s"),
            ("ε", "Bed void fraction", "—"),
            ("d_p", "Particle diameter", "m"),
            ("v_s", "Superficial velocity", "m/s"),
            ("ρ", "Fluid density", "kg/m³")
        ],
        "worked": "1. Bed length L = 2 m, void fraction ε = 0.4\n2. Superficial gas velocity vs = 0.5 m/s, viscosity μ = 2e-5 Pa·s\n3. Catalyst particle diameter dp = 3 mm (0.003 m), density ρ = 1.2 kg/m³\n4. Viscous term = 150*(2e-5)*(0.6^2)*(0.5) / (0.4^3 * 0.003^2) = 937.5 Pa/m\n5. Inertial term = 1.75*1.2*0.6*(0.5^2) / (0.4^3 * 0.003) = 1,640.6 Pa/m\n6. Total ΔP = (937.5 + 1,640.6) * 2 = 5,156 Pa",

        "whatif": "Smaller catalyst particles (dp ↓) create a substantially higher pressure drop due to the dp² term in the viscous denominator, increasing compressor power.",
        "trythis": "If catalyst particle diameter doubles from 3 mm to 6 mm while keeping all other variables constant, by what factor does the viscous pressure drop decrease?"
    },
    "Q = mCpΔT": {
        "tag": "Heat Transfer & Energy Balance",
        "latex": r"$$Q = m \cdot C_p \cdot \Delta T$$",
        "for": "Calculates the heat duty required to heat or cool process streams in reboilers, condensers, and shell-and-tube exchangers.",
        "symbols": [
            ("Q", "Heat duty (rate of heat transfer)", "kW or J/s"),
            ("m", "Mass flow rate", "kg/s"),
            ("C_p", "Specific heat capacity", "kJ/(kg·K)"),
            ("ΔT", "Temperature difference (T_out - T_in)", "°C or K")
        ],
        "worked": "1. Crude oil flow rate m = 10 kg/s\n2. Specific heat Cp = 2.0 kJ/(kg·K)\n3. Temperature rise ΔT = (150°C - 30°C) = 120 K\n4. Q = 10 * 2.0 * 120 = 2,400 kW (2.4 MW)\n5. Reboiler must supply at least 2.4 MW of steam heat.",
        "whatif": "If mass flow rate doubles (m → 2m), reboiler steam consumption doubles linearly (Q ∝ m).",
        "trythis": "Calculate heat duty (Q in kW) to heat 5 kg/s of water (Cp = 4.2 kJ/kg·K) from 20°C to 80°C."
    },
    "Bernoulli": {
        "tag": "Fluid Dynamics & Pipe Flow",
        "latex": r"$$P_1 + \frac{1}{2}\rho v_1^2 + \rho g h_1 = P_2 + \frac{1}{2}\rho v_2^2 + \rho g h_2$$",
        "for": "Determines pressure and velocity changes in plant piping, pump discharge lines, and orifice flowmeters.",
        "symbols": [
            ("P", "Static fluid pressure", "Pa or N/m²"),
            ("ρ", "Fluid density", "kg/m³"),
            ("v", "Fluid flow velocity", "m/s"),
            ("g", "Gravitational acceleration (9.81)", "m/s²"),
            ("h", "Pipe elevation / height", "m")
        ],
        "worked": "1. Naphtha line at elevation h1 = h2 (horizontal pipe)\n2. Initial velocity v1 = 2 m/s at P1 = 300 kPa\n3. Constriction causes v2 = 4 m/s (density ρ = 750 kg/m³)\n4. ΔP = 0.5 * 750 * (4² - 2²) = 0.5 * 750 * 12 = 4.5 kPa drop\n5. Final pressure P2 = 300 - 4.5 = 295.5 kPa.",
        "whatif": "When pipe diameter constricts, fluid velocity increases and static pressure drops (Venturi effect).",
        "trythis": "If fluid velocity increases from 1 m/s to 3 m/s in a horizontal pipe (ρ = 1000 kg/m³), what is the pressure decrease in Pa?"
    },
    "Raoult's Law": {
        "tag": "Vapor-Liquid Equilibrium",
        "latex": r"$$P_i = x_i \cdot P_i^\star$$",
        "for": "Predicts equilibrium vapor compositions on trays of crude distillation and hydrocarbon fractionation columns.",
        "symbols": [
            ("P_i", "Partial vapor pressure of component i", "kPa"),
            ("x_i", "Liquid mole fraction of component i", "mol/mol"),
            ("P_i^*", "Saturation vapor pressure of pure i", "kPa"),
            ("P_total", "Total system pressure (Σ P_i)", "kPa")
        ],
        "worked": "1. Benzene-Toluene mixture at 80°C\n2. Liquid mole fraction of benzene x_B = 0.4\n3. Pure benzene vapor pressure P_B* = 100 kPa\n4. Partial pressure P_B = 0.4 * 100 = 40 kPa\n5. Overhead vapor is enriched in the more volatile benzene.",
        "whatif": "Adding non-volatile residue lowers solvent vapor pressure in direct proportion to liquid mole fraction.",
        "trythis": "If component A has x_A = 0.3 and pure saturation vapor pressure 60 kPa, what is its partial pressure in the column overhead?"
    },
    "Reynolds Number": {
        "tag": "Transport Phenomena & Flow Regime",
        "latex": r"$$Re = \frac{\rho \cdot v \cdot D}{\mu}$$",
        "for": "Classifies whether hydrocarbon flow in refinery pipelines is smooth (laminar) or turbulent (turbulent flow Re > 4000).",
        "symbols": [
            ("Re", "Reynolds number", "Dimensionless"),
            ("ρ", "Fluid density", "kg/m³"),
            ("v", "Mean fluid velocity", "m/s"),
            ("D", "Internal pipe diameter", "m"),
            ("μ", "Dynamic fluid viscosity", "Pa·s")
        ],
        "worked": "1. Heavy oil (ρ = 900 kg/m³, μ = 0.09 Pa·s) flowing in D = 0.1 m pipe\n2. Flow velocity v = 1 m/s\n3. Re = (900 * 1 * 0.1) / 0.09 = 90 / 0.09 = 1,000\n4. Re < 2100 → Flow is strictly laminar.",
        "whatif": "Higher oil temperatures lower dynamic viscosity (μ ↓), triggering a transition to turbulent flow (Re ↑).",
        "trythis": "If water (ρ = 1000 kg/m³, μ = 0.001 Pa·s) flows at 2 m/s through a 0.05 m pipe, what is the Reynolds number and flow regime?"
    },
    "Fick's Law": {
        "tag": "Mass Transfer & Diffusion",
        "latex": r"$$J = -D_{AB} \frac{\partial C_A}{\partial x}$$",
        "for": "Calculates the molecular diffusion rate of gases in catalytic pellets and gas absorption columns.",
        "symbols": [
            ("J", "Diffusion flux", "mol/(m²·s)"),
            ("D_AB", "Diffusion coefficient / diffusivity", "m²/s"),
            ("C_A", "Concentration of diffusing species", "mol/m³"),
            ("x", "Diffusion distance / thickness", "m")
        ],
        "worked": "1. Gas diffusion across stagnant film thickness Δx = 0.001 m\n2. Diffusivity D_AB = 1.5e-5 m²/s\n3. Concentration drop ΔC = (20 - 5) = 15 mol/m³\n4. Flux J = 1.5e-5 * (15 / 0.001) = 0.225 mol/(m²·s).",
        "whatif": "Thinner boundary layers (Δx ↓) drastically increase the rate of mass transfer into the catalyst.",
        "trythis": "If the catalyst boundary film thickness is halved with the same concentration gradient, what happens to the diffusion flux J?"
    }
}

EQUATION_INFO.update({
    "Darcy–Weisbach": {
        "tag": "Pipe Friction Losses",
        "latex": r"$$\Delta P = f \cdot \frac{L}{D} \cdot \frac{\rho v^2}{2}$$",
        "for": "Predicts the pressure lost to friction in a straight pipe, used to size pumps and lines such as a naphtha transfer line between a tank and a column.",
        "symbols": [
            ("ΔP", "Pressure drop from friction", "Pa"),
            ("f", "Darcy friction factor", "—"),
            ("L", "Pipe length", "m"),
            ("D", "Internal pipe diameter", "m"),
            ("ρ", "Fluid density", "kg/m³"),
            ("v", "Mean fluid velocity", "m/s"),
        ],
        "worked": "1. Naphtha transfer line: L = 100 m, D = 0.1 m\n2. Velocity v = 2 m/s, density ρ = 750 kg/m³\n3. Friction factor f = 0.02 (typical commercial steel pipe)\n4. L/D = 100 / 0.1 = 1,000\n5. ρv²/2 = 750 * 4 / 2 = 1,500 Pa\n6. ΔP = 0.02 * 1,000 * 1,500 = 30,000 Pa (30 kPa)",
        "whatif": "Pumping twice as fast (v → 2v) quadruples the friction loss (ΔP ∝ v²), so pump power climbs very quickly with flow rate.",
        "trythis": "The same line now carries 4 m/s instead of 2 m/s (f unchanged). By what factor does the pressure drop change?",
    },
    "Ideal Gas Law": {
        "tag": "Gas Behaviour",
        "latex": r"$$PV = nRT$$",
        "for": "Links pressure, volume, temperature and amount of gas, for sizing flare headers, compressor suction drums and nitrogen purge systems at low-to-moderate pressure.",
        "symbols": [
            ("P", "Absolute pressure", "Pa"),
            ("V", "Gas volume", "m³"),
            ("n", "Amount of gas", "mol"),
            ("R", "Universal gas constant (8.314)", "J/(mol·K)"),
            ("T", "Absolute temperature", "K"),
        ],
        "worked": "1. Nitrogen purge vessel: n = 100 mol, T = 300 K, P = 200 kPa (200,000 Pa)\n2. Rearrange: V = nRT / P\n3. nRT = 100 * 8.314 * 300 = 249,420 J\n4. V = 249,420 / 200,000 = 1.247 m³",
        "whatif": "Heating gas in a closed, rigid vessel (V and n fixed) raises the pressure in direct proportion to absolute temperature (P ∝ T), which is why vessels need relief valves.",
        "trythis": "2 mol of gas sits at 400 K in a 0.01 m³ cylinder. What is the pressure in kPa?",
    },
    "Arrhenius Equation": {
        "tag": "Reaction Kinetics",
        "latex": r"$$k = A \cdot e^{-E_a / (R T)}$$",
        "for": "Shows how the reaction rate in a cracker or reformer climbs with temperature, which is why furnace outlet temperature is controlled so tightly.",
        "symbols": [
            ("k", "Rate constant", "1/s (first order)"),
            ("A", "Pre-exponential factor", "1/s"),
            ("E_a", "Activation energy", "J/mol"),
            ("R", "Universal gas constant (8.314)", "J/(mol·K)"),
            ("T", "Absolute temperature", "K"),
        ],
        "worked": "1. Cracking reaction: A = 1e10 1/s, Ea = 100,000 J/mol\n2. Reactor temperature T = 600 K\n3. Ea / (R*T) = 100,000 / (8.314 * 600) = 20.05\n4. e^(-20.05) = 1.97e-9\n5. k = 1e10 * 1.97e-9 = 19.7 1/s",
        "whatif": "A 20 K rise (600 → 620 K) nearly doubles k, because temperature sits in the exponent. Small temperature changes cause big rate changes.",
        "trythis": "If the reactor temperature rises from 600 K to 650 K with everything else unchanged, does k go up or down, and does it change linearly with T?",
    },
    "Antoine Equation": {
        "tag": "Vapor Pressure",
        "latex": r"$$\log_{10} P^{sat} = A - \frac{B}{C + T}$$",
        "for": "Gives the vapor pressure of a pure hydrocarbon at a given temperature, the starting point for distillation and storage-tank vent calculations.",
        "symbols": [
            ("P_sat", "Saturation vapor pressure", "mmHg"),
            ("T", "Temperature", "°C"),
            ("A", "Antoine constant (component-specific)", "—"),
            ("B", "Antoine constant (component-specific)", "—"),
            ("C", "Antoine constant (component-specific)", "—"),
        ],
        "worked": "1. Benzene: A = 6.90565, B = 1211.033, C = 220.79 (T in °C, P in mmHg)\n2. Temperature T = 80 °C\n3. C + T = 220.79 + 80 = 300.79\n4. log10(P) = 6.90565 - 1211.033 / 300.79 = 2.8795\n5. P = 10^2.8795 = 757.7 mmHg (101 kPa), benzene boils at about 80 °C",
        "whatif": "Raising the temperature increases vapor pressure steeply. When P_sat reaches the system pressure, the liquid boils.",
        "trythis": "Using the same benzene constants, would the vapor pressure at 60 °C be higher or lower than at 80 °C? Estimate it with the calculator.",
    },
    "LMTD": {
        "tag": "Heat Exchanger Design",
        "latex": r"$$\Delta T_{lm} = \frac{\Delta T_1 - \Delta T_2}{\ln(\Delta T_1 / \Delta T_2)}$$",
        "for": "Gives the average temperature driving force in a shell-and-tube exchanger, needed to size its area in Q = U·A·ΔT_lm, for example in a crude pre-heat train.",
        "symbols": [
            ("ΔT_lm", "Log-mean temperature difference", "K"),
            ("ΔT_1", "Temperature difference at one end", "K"),
            ("ΔT_2", "Temperature difference at the other end", "K"),
        ],
        "worked": "1. Crude pre-heat exchanger: hot end ΔT1 = 80 K, cold end ΔT2 = 40 K\n2. Difference = 80 - 40 = 40 K\n3. ln(80 / 40) = ln 2 = 0.693\n4. ΔT_lm = 40 / 0.693 = 57.7 K\n5. A plain average would say 60 K, the LMTD is slightly lower",
        "whatif": "If one end gets a very small ΔT (a close temperature approach), LMTD collapses and the exchanger needs far more surface area.",
        "trythis": "Hot end ΔT1 = 100 K and cold end ΔT2 = 50 K. What is the LMTD?",
    },
})


# ── Live calculators ───────────────────────────────────────────────────────────
# Each calculator: ordered inputs [(label, default)] and fn(*values) -> (rows, badge)
# rows = [(label, value, unit)], first row is the headline result.
def _ergun(L, e, dp, vs, mu, rho):
    if not 0 < e < 1:
        raise ValueError("Void fraction ε must be between 0 and 1.")
    if dp <= 0:
        raise ValueError("Particle diameter must be positive.")
    visc = 150 * mu * (1 - e) ** 2 * vs / (e ** 3 * dp ** 2)
    inert = 1.75 * rho * (1 - e) * vs ** 2 / (e ** 3 * dp)
    badge = "Inertial term dominates (turbulent-like)" if inert > visc else "Viscous term dominates (laminar-like)"
    return [("Total pressure drop ΔP", (visc + inert) * L, "Pa"), ("Viscous term", visc, "Pa/m"), ("Inertial term", inert, "Pa/m")], badge


def _heat(m, cp, dt):
    q = m * cp * dt
    return [("Heat duty Q", q, "kW"), ("In megawatts", q / 1000, "MW")], None


def _bernoulli(rho, v1, v2, p1):
    dp = 0.5 * rho * (v2 ** 2 - v1 ** 2) / 1000
    p2 = p1 - dp
    badge = "⚠ P₂ is negative: the liquid would flash or cavitate" if p2 < 0 else ("Pressure falls (fluid speeds up)" if dp > 0 else "Pressure rises (fluid slows down)" if dp < 0 else None)
    return [("Downstream pressure P₂", p2, "kPa"), ("Pressure change ΔP", -dp, "kPa")], badge


def _raoult(x, psat):
    if not 0 <= x <= 1:
        raise ValueError("Mole fraction must be between 0 and 1.")
    return [("Partial pressure Pᵢ", x * psat, "kPa")], None


def _reynolds(rho, v, d, mu):
    re_ = rho * v * d / mu
    badge = "Laminar flow" if re_ < 2100 else ("Transitional flow" if re_ <= 4000 else "Turbulent flow")
    return [("Reynolds number Re", re_, "")], badge


def _fick(d, dc, dx):
    if dx <= 0:
        raise ValueError("Film thickness must be positive.")
    return [("Diffusion flux |J|", d * dc / dx, "mol/(m²·s)")], "Flows from high to low concentration"


def _darcy(f, L, d, rho, v):
    if d <= 0:
        raise ValueError("Pipe diameter must be positive.")
    dp = f * (L / d) * rho * v ** 2 / 2
    return [("Pressure drop ΔP", dp / 1000, "kPa"), ("In pascals", dp, "Pa")], None


def _ideal_gas(n, t, p):
    if p <= 0 or t <= 0:
        raise ValueError("Pressure and temperature must be positive (absolute).")
    v = n * 8.314 * t / (p * 1000)
    return [("Gas volume V", v, "m³"), ("In litres", v * 1000, "L")], None


def _arrhenius(a, ea, t):
    if t <= 0:
        raise ValueError("Temperature must be positive (kelvin).")
    x = ea / (8.314 * t)
    return [("Rate constant k", a * math.exp(-x), "1/s"), ("Ea / (R·T)", x, "")], None


def _antoine(a, b, c, t):
    p = 10 ** (a - b / (c + t))
    return [("Vapor pressure P_sat", p, "mmHg"), ("In kilopascals", p * 0.133322, "kPa")], None


def _lmtd(dt1, dt2):
    if dt1 <= 0 or dt2 <= 0:
        raise ValueError("Both temperature differences must be positive.")
    lm = dt1 if math.isclose(dt1, dt2) else (dt1 - dt2) / math.log(dt1 / dt2)
    return [("Log-mean ΔT_lm", lm, "K"), ("Plain average", (dt1 + dt2) / 2, "K")], None


CALCS = {
    "Ergun Equation": {"inputs": [("Bed length L (m)", 2), ("Void fraction ε", 0.4), ("Particle diameter d_p (m)", 0.003),
                                  ("Superficial velocity v_s (m/s)", 0.5), ("Viscosity μ (Pa·s)", 2e-5), ("Density ρ (kg/m³)", 1.2)], "fn": _ergun},
    "Q = mCpΔT": {"inputs": [("Mass flow m (kg/s)", 10), ("Specific heat C_p (kJ/kg·K)", 2.0), ("Temperature rise ΔT (K)", 120)], "fn": _heat},
    "Bernoulli": {"inputs": [("Density ρ (kg/m³)", 750), ("Velocity v₁ (m/s)", 2), ("Velocity v₂ (m/s)", 4), ("Pressure P₁ (kPa)", 300)], "fn": _bernoulli},
    "Raoult's Law": {"inputs": [("Liquid mole fraction x", 0.4), ("Pure vapor pressure P* (kPa)", 100)], "fn": _raoult},
    "Reynolds Number": {"inputs": [("Density ρ (kg/m³)", 900), ("Velocity v (m/s)", 1), ("Pipe diameter D (m)", 0.1), ("Viscosity μ (Pa·s)", 0.09)], "fn": _reynolds},
    "Fick's Law": {"inputs": [("Diffusivity D_AB (m²/s)", 1.5e-5), ("Concentration drop ΔC (mol/m³)", 15), ("Film thickness Δx (m)", 0.001)], "fn": _fick},
    "Darcy–Weisbach": {"inputs": [("Friction factor f", 0.02), ("Pipe length L (m)", 100), ("Diameter D (m)", 0.1), ("Density ρ (kg/m³)", 750), ("Velocity v (m/s)", 2)], "fn": _darcy},
    "Ideal Gas Law": {"inputs": [("Amount n (mol)", 100), ("Temperature T (K)", 300), ("Pressure P (kPa)", 200)], "fn": _ideal_gas},
    "Arrhenius Equation": {"inputs": [("Pre-exponential A (1/s)", 1e10), ("Activation energy E_a (J/mol)", 100000), ("Temperature T (K)", 600)], "fn": _arrhenius},
    "Antoine Equation": {"inputs": [("Constant A", 6.90565), ("Constant B", 1211.033), ("Constant C", 220.79), ("Temperature T (°C)", 80)], "fn": _antoine},
    "LMTD": {"inputs": [("Hot-end ΔT₁ (K)", 80), ("Cold-end ΔT₂ (K)", 40)], "fn": _lmtd},
}
MAX_INPUTS = max(len(c["inputs"]) for c in CALCS.values())


ANNOTATED_LATEX = {
    "Ergun Equation": r"$$\frac{\Delta P}{L} = \underbrace{\frac{150\mu(1-\epsilon)^2 v_s}{\epsilon^3 d_p^2}}_{\text{Viscous contribution}} + \underbrace{\frac{1.75\rho(1-\epsilon)v_s^2}{\epsilon^3 d_p}}_{\text{Inertial contribution}}$$",
}

ERGUN_TAGS_HTML = (
    "<div class='tag-row'>"
    "<span class='tag-viscous'>Viscous term · dominates at low flow (laminar)</span>"
    "<span class='tag-inertial'>Inertial term · dominates at high flow (turbulent)</span>"
    "</div>"
)

# ── Design System CSS: Engineering Tool (Inter + STIX Two Math, no gradients) ──
APP_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=STIX+Two+Math&display=swap');

:root, .dark {
  --midnight-navy: #14263D;
  --deep-navy: #172B45;
  --slate-blue: #66758A;
  --off-white: #F8FAFC;
  --white: #FFFFFF;
  --border-cool-gray: #D9E1EA;
  --eng-blue: #2F80ED;
  --soft-blue: #EAF3FF;
  --soft-violet: #F1ECFF;
  --accent-violet: #7C5CDB;
  --success-green: #22A06B;

  /* Pin Gradio's own tokens to the light design so OS dark mode can't break contrast */
  color-scheme: light;
  --body-background-fill: var(--off-white);
  --background-fill-primary: var(--white);
  --background-fill-secondary: var(--off-white);
  --block-background-fill: transparent;
  --block-border-width: 0px;
  --block-border-color: transparent;
  --block-shadow: none;
  --block-label-background-fill: var(--white);
  --block-label-text-color: var(--slate-blue);
  --body-text-color: var(--deep-navy);
  --body-text-color-subdued: var(--slate-blue);
  --border-color-primary: var(--border-cool-gray);
  --input-background-fill: var(--white);
  --input-background-fill-focus: var(--white);
  --input-border-color: var(--border-cool-gray);
  --input-border-color-focus: var(--eng-blue);
  --input-shadow: none;
  --input-shadow-focus: 0 0 0 3px rgba(47, 128, 237, 0.15);
  --input-placeholder-color: #94A3B8;
  --button-primary-background-fill: var(--midnight-navy);
  --button-primary-background-fill-hover: #1C3654;
  --button-primary-text-color: #FFFFFF;
  --button-primary-border-color: var(--midnight-navy);
  --button-secondary-background-fill: var(--white);
  --button-secondary-text-color: var(--deep-navy);
  --button-secondary-border-color: var(--border-cool-gray);
  --shadow-drop: none;
  --shadow-drop-lg: none;
}

html { scroll-behavior: smooth; }

body, .gradio-container {
  background: var(--off-white) !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
  color: var(--deep-navy);
  line-height: 1.5;
}

.gradio-container {
  max-width: 100% !important;
  padding: 0 !important;
  margin: 0 !important;
}
.gradio-container main, .gradio-container .main { padding: 0 !important; max-width: 100% !important; }
footer { display: none !important; }

/* KaTeX */
.katex, .katex-display, .math-display { font-family: 'STIX Two Math', 'KaTeX_Main', serif; }
.katex-display { margin: 0.4em 0 !important; overflow-x: auto; overflow-y: hidden; }

/* ── Shell ───────────────────────────────────────────────────────────────── */
.app-shell { gap: 0 !important; flex-wrap: nowrap !important; align-items: stretch !important; }

.app-sidebar {
  background: var(--midnight-navy) !important;
  padding: 24px 14px !important;
  border-right: 1px solid #101F31 !important;
  position: sticky;
  top: 0;
  align-self: flex-start;
  height: 100vh;
  min-width: 230px !important;
  max-width: 270px;
  gap: 4px !important;
  justify-content: flex-start;
}
.app-sidebar .block, .app-sidebar .form { background: transparent !important; border: none !important; padding: 0 !important; }

.brand-header { padding: 0 6px 18px 6px; border-bottom: 1px solid rgba(255,255,255,0.12); margin-bottom: 14px; }
.brand-name { font-size: 22px; font-weight: 700; color: #FFFFFF; display: flex; align-items: center; gap: 10px; letter-spacing: -0.01em; }
.brand-sub { font-size: 12px; color: #94A3B8; margin-top: 4px; }

.app-sidebar button.nav-item {
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 10px !important;
  width: 100% !important;
  padding: 10px 12px !important;
  border-radius: 8px !important;
  border: none !important;
  border-left: 3px solid transparent !important;
  background: transparent !important;
  color: #CBD5E1 !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  text-align: left !important;
  box-shadow: none !important;
  transition: background 0.15s ease, color 0.15s ease !important;
}
.app-sidebar button.nav-item:hover { background: rgba(255,255,255,0.07) !important; color: #FFFFFF !important; }
.app-sidebar button.nav-item.active {
  background: rgba(47, 128, 237, 0.18) !important;
  color: #FFFFFF !important;
  font-weight: 600 !important;
  border-left-color: var(--eng-blue) !important;
}

.sidebar-footer {
  margin-top: auto;
  padding: 14px 6px 0 6px;
  border-top: 1px solid rgba(255,255,255,0.12);
  font-size: 12px;
  color: #94A3B8;
}

.content-wrapper { padding: 0 !important; gap: 0 !important; min-width: 0 !important; }

/* ── Top header ──────────────────────────────────────────────────────────── */
.top-header {
  align-items: center !important;
  justify-content: space-between !important;
  flex-wrap: nowrap !important;
  padding: 12px 32px !important;
  background: var(--white) !important;
  border-bottom: 1px solid var(--border-cool-gray) !important;
  margin: 0 !important;
  gap: 12px !important;
}
.top-header .block { padding: 0 !important; }
.header-title { font-size: 15px; font-weight: 600; color: var(--deep-navy); white-space: nowrap; }
.top-pill {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 12px; font-weight: 500; color: var(--slate-blue);
  background: var(--off-white); padding: 5px 12px; border-radius: 999px;
  border: 1px solid var(--border-cool-gray); white-space: nowrap;
}
.top-pill .dot { color: var(--success-green); }
button.back-btn { min-width: 0 !important; width: auto !important; flex: 0 0 auto !important; }

/* ── Screens ─────────────────────────────────────────────────────────────── */
.screen { padding: 28px 32px 48px 32px !important; max-width: 1180px; width: 100%; margin: 0 auto; gap: 16px !important; }

.screen-card, .breakdown-card, .semantic-breakdown-box, .interactive-preview-card, .steps-sidebar-box {
  background: var(--white) !important;
  border: 1px solid var(--border-cool-gray) !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}
.screen-card { padding: 28px !important; }
.breakdown-card, .semantic-breakdown-box, .interactive-preview-card { padding: 20px !important; }
.steps-sidebar-box { padding: 16px 12px !important; position: sticky; top: 16px; }

.screen-title { font-size: 28px; font-weight: 600; color: var(--deep-navy); letter-spacing: -0.01em; margin-bottom: 4px; }
.screen-desc { font-size: 14px; color: var(--slate-blue); margin-bottom: 8px; }
.section-title { font-size: 16px; font-weight: 600; color: var(--deep-navy); margin: 8px 0 0 0; }
.breakdown-header { font-size: 15px; font-weight: 600; color: var(--deep-navy); margin-bottom: 6px; }
.result-title { font-size: 28px; font-weight: 600; color: var(--deep-navy); margin: 2px 0 4px 0; letter-spacing: -0.01em; }
.body-text { font-size: 14.5px; color: var(--deep-navy); margin: 0; }

.formula-hero-box {
  background: var(--off-white) !important;
  border: 1px solid var(--border-cool-gray) !important;
  border-radius: 8px !important;
  padding: 16px 20px !important;
  text-align: center;
  overflow-x: auto;
}

/* Inputs */
.gradio-container textarea, .gradio-container input[type="text"] { font-size: 14px !important; border-radius: 8px !important; }

.eq-input textarea { min-height: 64px !important; max-height: 110px !important; resize: none; overflow-y: auto; }
.eq-input, .eq-input label { height: auto !important; min-height: 0 !important; }

/* Buttons */
button.crack-btn-primary {
  background: var(--midnight-navy) !important;
  color: #FFFFFF !important;
  border: 1px solid var(--midnight-navy) !important;
  border-radius: 8px !important;
  padding: 12px 24px !important;
  font-weight: 600 !important;
  font-size: 15px !important;
  box-shadow: none !important;
}
button.crack-btn-primary:hover { background: #1C3654 !important; }

button.btn-secondary-flat {
  background: var(--white) !important;
  color: var(--deep-navy) !important;
  border: 1px solid var(--border-cool-gray) !important;
  border-radius: 8px !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  box-shadow: none !important;
}
button.btn-secondary-flat:hover { background: var(--off-white) !important; border-color: #B8C7D8 !important; }

.quick-row { gap: 12px !important; flex-wrap: wrap !important; }
button.quick-card-box {
  background: var(--white) !important;
  color: var(--deep-navy) !important;
  border: 1px solid var(--border-cool-gray) !important;
  border-radius: 10px !important;
  padding: 14px 12px !important;
  min-width: 170px !important;
  box-shadow: none !important;
  font-size: 13.5px !important;
  font-weight: 600 !important;
  white-space: normal !important;
  line-height: 1.35 !important;
  transition: border-color 0.15s ease, background 0.15s ease !important;
}
button.quick-card-box:hover { border-color: var(--eng-blue) !important; background: #FAFCFF !important; }

/* Lesson outline (anchor links) */
.step-nav-row {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 9px 8px; border-radius: 8px; margin-bottom: 2px;
  text-decoration: none !important; color: inherit !important;
}
.step-nav-row:hover { background: var(--soft-blue); }
.step-circle {
  width: 22px; height: 22px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 600; color: #FFFFFF; background: var(--eng-blue); flex-shrink: 0;
}
.step-name { font-size: 13.5px; font-weight: 600; color: var(--deep-navy); }
.step-sub { font-size: 12px; color: var(--slate-blue); }
.outline-title { font-size: 15px; font-weight: 600; color: var(--deep-navy); margin: 0 6px 10px 6px; }

/* Tags */
.pill-topic {
  display: inline-block; background: var(--soft-blue); color: var(--eng-blue);
  padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 600;
}
.tag-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px; }
.tag-viscous, .tag-inertial { border-radius: 6px; padding: 4px 9px; font-size: 12px; font-weight: 600; }
.tag-viscous { background: var(--soft-blue); color: #1F66C7; border: 1px solid #D0E4FF; }
.tag-inertial { background: var(--soft-violet); color: #5B3FB8; border: 1px solid #E1D6FF; }

/* Symbols table */
.symbols-table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
.symbols-table th {
  background: var(--off-white); padding: 8px 12px; text-align: left;
  font-weight: 600; color: var(--deep-navy); border-bottom: 1px solid var(--border-cool-gray);
}
.symbols-table td { padding: 8px 12px; border-bottom: 1px solid var(--border-cool-gray); color: var(--deep-navy); }
.symbols-table tr:last-child td { border-bottom: none; }
.symbols-table .unit { color: var(--slate-blue); white-space: nowrap; }

/* Interactive focus */
.focus-symbol { font-family: 'STIX Two Math', serif; font-size: 30px; font-weight: 600; color: var(--deep-navy); }
.interactive-detail-box {
  background: var(--soft-violet); border: 1px solid #E1D6FF; border-radius: 8px;
  padding: 14px; margin-top: 10px; font-size: 13.5px; color: var(--deep-navy);
}

/* Worked example */
.steps-list { margin: 0; padding-left: 0; list-style: none; counter-reset: step; }
.steps-list li {
  counter-increment: step; position: relative; padding: 8px 0 8px 34px;
  font-size: 14px; border-bottom: 1px dashed var(--border-cool-gray);
}
.steps-list li:last-child { border-bottom: none; }
.steps-list li::before {
  content: counter(step); position: absolute; left: 0; top: 9px;
  width: 22px; height: 22px; border-radius: 50%; background: var(--soft-blue); color: var(--eng-blue);
  font-size: 12px; font-weight: 600; display: flex; align-items: center; justify-content: center;
}

.feedback-bubble {
  background: #F0FDF4 !important; border: 1px solid #BBF7D0 !important; border-radius: 8px !important;
  padding: 12px 14px !important; color: #166534 !important; font-size: 13.5px;
}

/* Calculator */
.calc-row { gap: 12px !important; flex-wrap: wrap !important; }
.calc-row .block { background: transparent !important; }
.calc-results { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 4px; }
.calc-tile { flex: 1 1 150px; background: var(--off-white); border: 1px solid var(--border-cool-gray); border-radius: 8px; padding: 12px 14px; }
.calc-tile.main { background: var(--soft-blue); border-color: #C9E0FF; flex-grow: 2; }
.calc-tile .k { font-size: 12px; color: var(--slate-blue); font-weight: 500; }
.calc-tile .v { font-size: 24px; font-weight: 600; color: var(--deep-navy); font-variant-numeric: tabular-nums; }
.calc-tile .u { font-size: 13px; font-weight: 500; color: var(--slate-blue); }
.calc-badge { display: inline-block; margin-top: 10px; padding: 4px 10px; border-radius: 999px; background: var(--soft-violet); color: #5B3FB8; font-size: 12px; font-weight: 600; }
.calc-note { font-size: 13.5px; color: var(--slate-blue); padding: 8px 0; }
.calc-note.warn { color: #9A5B00; background: #FFF7E6; border: 1px solid #FFE2A8; border-radius: 8px; padding: 10px 12px; }

/* History */
.history-item {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 12px 4px; border-bottom: 1px solid var(--border-cool-gray);
}
.history-item:last-child { border-bottom: none; }
.history-name { font-weight: 600; font-size: 14.5px; }
.empty-state { text-align: center; padding: 28px 12px; color: var(--slate-blue); font-size: 14px; }

/* ── Responsive ──────────────────────────────────────────────────────────── */
@media (max-width: 860px) {
  .app-shell { flex-wrap: wrap !important; }
  .app-sidebar {
    position: static; height: auto; max-width: 100%; min-width: 100% !important;
    flex-direction: row !important; flex-wrap: wrap; align-items: center; padding: 12px !important;
  }
  .app-sidebar .brand-header { border-bottom: none; margin: 0 12px 0 0; padding: 0; }
  .app-sidebar .brand-sub, .sidebar-footer { display: none; }
  .app-sidebar button.nav-item { width: auto !important; border-left: none !important; padding: 8px 10px !important; }
  .top-header { padding: 10px 16px !important; }
  .screen { padding: 16px 16px 40px 16px !important; }
  .steps-sidebar-box { position: static; }
  .result-title, .screen-title { font-size: 24px; }
}
"""

# ── Helpers ────────────────────────────────────────────────────────────────────
ALIASES = {
    "darcy": "Darcy–Weisbach", "friction": "Darcy–Weisbach", "pipe loss": "Darcy–Weisbach",
    "ideal gas": "Ideal Gas Law", "pv=nrt": "Ideal Gas Law", "pv = nrt": "Ideal Gas Law",
    "arrhenius": "Arrhenius Equation", "rate constant": "Arrhenius Equation", "kinetics": "Arrhenius Equation",
    "antoine": "Antoine Equation", "vapor pressure": "Antoine Equation", "vapour pressure": "Antoine Equation",
    "lmtd": "LMTD", "log mean": "LMTD", "log-mean": "LMTD", "exchanger": "LMTD",
    "heat": "Q = mCpΔT", "mcp": "Q = mCpΔT", "energy balance": "Q = mCpΔT",
    "raoult": "Raoult's Law", "reynolds": "Reynolds Number", "re =": "Reynolds Number",
    "fick": "Fick's Law", "diffusion": "Fick's Law", "ergun": "Ergun Equation",
    "pressure drop": "Ergun Equation", "packed bed": "Ergun Equation",
}


def get_equation_data(eq_name):
    """Return (key, data, matched). Falls back to Ergun with matched=False."""
    q = eq_name.strip().lower()
    for key, data in EQUATION_INFO.items():
        if q == key.lower():
            return key, data, True
    if len(q) >= 3:
        for key, data in EQUATION_INFO.items():
            if q in key.lower() or key.lower() in q:
                return key, data, True
        for alias, key in ALIASES.items():
            if alias in q:
                return key, EQUATION_INFO[key], True
    return "Ergun Equation", EQUATION_INFO["Ergun Equation"], False


def fmt_sym(s):
    s = html.escape(s)
    s = re.sub(r"_\{?(\w+)\}?", r"<sub>\1</sub>", s)
    return s.replace("^*", "<sup>*</sup>")


def build_symbols_table_html(symbols_list):
    rows = "".join(
        f"<tr><td><b>{fmt_sym(sym)}</b></td><td>{html.escape(mean)}</td><td class='unit'>{html.escape(unit)}</td></tr>"
        for sym, mean, unit in symbols_list
    )
    return (
        "<table class='symbols-table'><thead><tr><th>Symbol</th><th>Meaning</th><th>Unit</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def build_focus_html(key, symbol):
    for sym, mean, unit in EQUATION_INFO[key]["symbols"]:
        if sym == symbol:
            return (
                f"<div class='focus-symbol'>{fmt_sym(sym)}</div>"
                f"<div class='interactive-detail-box'><b>{html.escape(mean)}</b><br>"
                f"<b>Unit:</b> {html.escape(unit)}<br><br>"
                "Tip: ask yourself — if this goes up, does the result go up or down?</div>"
            )
    return ""


def build_steps_html(text):
    items = [re.sub(r"^\d+\.\s*", "", ln).strip() for ln in text.split("\n") if ln.strip()]
    return "<ol class='steps-list'>" + "".join(f"<li>{html.escape(i)}</li>" for i in items) + "</ol>"


def para(text):
    return f"<p class='body-text'>{html.escape(text)}</p>"


def header_html(text):
    return f"<span class='header-title'>{html.escape(text)}</span>"


OUTLINE = [
    ("Identify", "What is this equation?", "sec-formula"),
    ("Purpose", "What is it for?", "sec-purpose"),
    ("Variables", "Understand the symbols", "sec-symbols"),
    ("Worked Example", "Step-by-step calculation", "sec-worked"),
    ("Try it live", "Plug in your own numbers", "sec-calc"),
    ("What if...?", "Explore the effects", "sec-whatif"),
    ("Try This", "Practice problem", "sec-try"),
]
OUTLINE_HTML = (
    "<div class='outline-title'>Lesson outline</div>"
    + "".join(
        f"<a class='step-nav-row' href='#{sid}'><span class='step-circle'>{i}</span>"
        f"<div><div class='step-name'>{n}</div><div class='step-sub'>{s}</div></div></a>"
        for i, (n, s, sid) in enumerate(OUTLINE, 1)
    )
)


def history_markup(history):
    if not history:
        return "<div class='empty-state'>No equations yet. Crack one and it will show up here.</div>"
    rows = "".join(
        f"<div class='history-item'><span class='history-name'>{html.escape(k)}</span>"
        f"<span class='pill-topic'>{html.escape(EQUATION_INFO[k]['tag'])}</span></div>"
        for k in history
    )
    return rows


def identify_from_image(path):
    """Ask the local vision model which known equation a photo shows. Returns a key or ''."""
    try:
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        names = ", ".join(EQUATION_INFO)
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL_NAME,
                "messages": [{
                    "role": "user",
                    "content": f"Which equation is shown in this image? Reply with exactly one of: {names}. If none, reply UNKNOWN.",
                    "images": [b64],
                }],
                "stream": False,
            },
            timeout=60,
        )
        answer = r.json().get("message", {}).get("content", "")
        key, _, matched = get_equation_data(answer.strip().strip(".")) if "UNKNOWN" not in answer.upper() else ("", None, False)
        return key if matched else ""
    except Exception:
        gr.Warning("Couldn't read the image — is Ollama running? Type the equation name instead.")
        return ""


def fmt_num(v):
    if v == 0:
        return "0"
    if abs(v) >= 1e6 or abs(v) < 1e-3:
        return f"{v:.3e}"
    return f"{v:,.0f}" if abs(v) >= 1000 else f"{v:.4g}"


def calc_input_updates(key):
    inputs = CALCS[key]["inputs"]
    return [
        gr.update(label=inputs[i][0], value=inputs[i][1], visible=True) if i < len(inputs) else gr.update(label="", value=None, visible=False)
        for i in range(MAX_INPUTS)
    ]


def render_calc(key, values):
    spec = CALCS[key]
    values = list(values)[: len(spec["inputs"])]
    if any(v is None for v in values):
        return "<div class='calc-note'>Fill in every number to see the result.</div>"
    try:
        rows, badge = spec["fn"](*values)
    except ZeroDivisionError:
        return "<div class='calc-note warn'>One of the numbers is zero where it can't be (for example a diameter or viscosity).</div>"
    except (ValueError, OverflowError) as e:
        return f"<div class='calc-note warn'>{html.escape(str(e))}</div>"
    tiles = "".join(
        f"<div class='calc-tile{' main' if i == 0 else ''}'><div class='k'>{html.escape(lbl)}</div>"
        f"<div class='v'>{fmt_num(val)} <span class='u'>{html.escape(unit)}</span></div></div>"
        for i, (lbl, val, unit) in enumerate(rows)
    )
    badge_html = f"<div class='calc-badge'>{html.escape(badge)}</div>" if badge else ""
    return f"<div class='calc-results'>{tiles}</div>{badge_html}"


NAV = ["home", "quick", "upload", "history"]
VIEW_TITLES = {"home": "Dashboard", "quick": "Quick Equations", "upload": "Upload Notes", "history": "History"}


def view_updates(name, title=None):
    """Visibility + header + nav state for a view: home | quick | upload | history | result."""
    active = "home" if name == "result" else name
    return [
        gr.update(visible=name in ("home", "quick", "upload")),
        gr.update(visible=name == "result"),
        gr.update(visible=name == "history"),
        gr.update(visible=name in ("result", "history")),
        header_html(title or VIEW_TITLES.get(name, "Dashboard")),
        *[gr.update(elem_classes=["nav-item", "active"] if n == active else ["nav-item"]) for n in NAV],
        gr.update(visible=name == "upload"),
    ]


# ── Main Gradio App ────────────────────────────────────────────────────────────
with gr.Blocks(title="CrackIt — Engineering Equation Interpreter") as demo:
    history_state = gr.State([])
    current_eq = gr.State("Ergun Equation")

    with gr.Row(equal_height=False, elem_classes=["app-shell"]):
        # ── Sidebar ───────────────────────────────────────────────────────────
        with gr.Column(scale=0, min_width=230, elem_classes=["app-sidebar"]):
            gr.HTML("""
            <div class="brand-header">
              <div class="brand-name"><span>⚗️</span> CrackIt</div>
              <div class="brand-sub">Engineering Equation Interpreter</div>
            </div>
            """)
            nav_btn_home = gr.Button("🏠  Home", elem_classes=["nav-item", "active"])
            nav_btn_quick = gr.Button("⚡  Quick Equations", elem_classes=["nav-item"])
            nav_btn_upload = gr.Button("📤  Upload Notes", elem_classes=["nav-item"])
            nav_btn_history = gr.Button("🕒  History", elem_classes=["nav-item"])
            gr.HTML("<div class='sidebar-footer'>Runs 100% offline on your machine</div>")

        # ── Main workspace ────────────────────────────────────────────────────
        with gr.Column(scale=1, elem_classes=["content-wrapper"]):
            with gr.Row(elem_classes=["top-header"]):
                with gr.Row(scale=0):
                    header_back_btn = gr.Button("← Back", variant="secondary", size="sm", visible=False, elem_classes=["back-btn"])
                    header_title = gr.HTML(header_html("Dashboard"))
                gr.HTML("<div class='top-pill'><span class='dot'>●</span><span>Local model · Gemma 3 4B · Ollama</span></div>")

            # ── Screen 1: Home ────────────────────────────────────────────────
            with gr.Column(visible=True, elem_classes=["screen"]) as screen_1:
                with gr.Column(elem_classes=["screen-card"]):
                    gr.HTML("""
                    <div class="screen-title">Crack an Equation</div>
                    <div class="screen-desc">Type an equation name, pick a quick one below, or upload a photo of your notes.</div>
                    """)
                    formula_preview_box = gr.Markdown("", elem_classes=["formula-hero-box"], visible=False)
                    input_equation_text = gr.Textbox(
                        placeholder="e.g. Ergun equation, Q = mCpΔT, Reynolds number…",
                        lines=2, max_lines=3, show_label=False, container=False, elem_classes=["eq-input"],
                    )
                    upload_image_box = gr.Image(label="Photo of your notes or textbook", type="filepath", visible=False, height=240)
                    with gr.Row():
                        btn_tab_upload = gr.Button("📤  Upload photo", elem_classes=["btn-secondary-flat"], size="sm")
                        btn_tab_quick = gr.Button("⚡  Pick a quick equation", elem_classes=["btn-secondary-flat"], size="sm")
                    btn_main_crack = gr.Button("➔  Crack It", elem_classes=["crack-btn-primary"])

                gr.HTML("<div class='section-title' id='quick-start'>⚡ Quick Start Equations</div>")
                with gr.Row(elem_classes=["quick-row"]):
                    quick_buttons = {
                        key: gr.Button(f"{key}\n{data['tag']}", elem_classes=["quick-card-box"])
                        for key, data in EQUATION_INFO.items()
                    }

            # ── Screen 2: Result ──────────────────────────────────────────────
            with gr.Column(visible=False, elem_classes=["screen"]) as screen_2:
                with gr.Row(equal_height=False):
                    with gr.Column(scale=3, min_width=220):
                        gr.HTML(f"<div class='steps-sidebar-box'>{OUTLINE_HTML}</div>")

                    with gr.Column(scale=9, min_width=320):
                        out_tag_html = gr.HTML()
                        out_title_html = gr.HTML()

                        with gr.Column(elem_classes=["semantic-breakdown-box"], elem_id="sec-formula"):
                            out_formula_latex = gr.Markdown()
                            out_tags_html = gr.HTML()

                        with gr.Column(elem_classes=["breakdown-card"], elem_id="sec-purpose"):
                            gr.HTML("<div class='breakdown-header'>What is it for?</div>")
                            out_what_it_is = gr.HTML()

                        with gr.Row(equal_height=False):
                            with gr.Column(scale=6, min_width=300, elem_classes=["breakdown-card"], elem_id="sec-symbols"):
                                gr.HTML("<div class='breakdown-header'>Crack the Symbols</div>")
                                out_symbols_table = gr.HTML()
                            with gr.Column(scale=4, min_width=240, elem_classes=["interactive-preview-card"]):
                                gr.HTML("<div class='breakdown-header'>Interactive Focus</div>")
                                focus_dd = gr.Dropdown(choices=[], label="Pick a symbol", interactive=True, allow_custom_value=True)
                                out_focus_html = gr.HTML()

                        with gr.Column(elem_classes=["breakdown-card"], elem_id="sec-worked"):
                            gr.HTML("<div class='breakdown-header'>Worked Example</div>")
                            out_worked_example = gr.HTML()

                        with gr.Column(elem_classes=["breakdown-card"], elem_id="sec-calc"):
                            gr.HTML("<div class='breakdown-header'>Try it live</div>"
                                    "<p class='body-text' style='color:var(--slate-blue)'>Change any number and the answer updates instantly. It starts with the worked-example values.</p>")
                            with gr.Row(elem_classes=["calc-row"]):
                                calc_nums = [gr.Number(label="", visible=False, min_width=150) for _ in range(MAX_INPUTS)]
                            calc_out = gr.HTML()

                        with gr.Column(elem_classes=["breakdown-card"], elem_id="sec-whatif"):
                            gr.HTML("<div class='breakdown-header'>What Happens If...?</div>")
                            out_whatif_text = gr.HTML()

                        with gr.Column(elem_classes=["breakdown-card"], elem_id="sec-try"):
                            gr.HTML("<div class='breakdown-header'>Try This (Practice Problem)</div>")
                            out_trythis_text = gr.HTML()
                            with gr.Row():
                                student_answer_input = gr.Textbox(
                                    placeholder="Enter your calculation / answer (e.g. 4 times decrease)…",
                                    show_label=False, container=False, scale=4,
                                )
                                student_answer_btn = gr.Button("Check Answer", variant="primary", scale=1, min_width=140)
                            student_feedback_box = gr.Markdown("", elem_classes=["feedback-bubble"], visible=False)

            # ── Screen 3: History ─────────────────────────────────────────────
            with gr.Column(visible=False, elem_classes=["screen"]) as screen_3:
                with gr.Column(elem_classes=["screen-card"]):
                    gr.HTML("""
                    <div class="screen-title">History</div>
                    <div class="screen-desc">Equations you've cracked in this session.</div>
                    """)
                    history_html = gr.HTML(history_markup([]))
                    with gr.Row():
                        history_dd = gr.Dropdown(choices=[], label="Reopen an equation", interactive=True, allow_custom_value=True, scale=3)
                        history_open_btn = gr.Button("Open", variant="primary", scale=1, min_width=120)
                        history_clear_btn = gr.Button("Clear", elem_classes=["btn-secondary-flat"], scale=1, min_width=120)

    # ── Callbacks ──────────────────────────────────────────────────────────────
    VIEW_OUTPUTS = [
        screen_1, screen_2, screen_3, header_back_btn, header_title,
        nav_btn_home, nav_btn_quick, nav_btn_upload, nav_btn_history, upload_image_box,
    ]
    CRACK_OUTPUTS = VIEW_OUTPUTS + [
        current_eq, out_tag_html, out_title_html, out_formula_latex, out_tags_html,
        out_what_it_is, out_symbols_table, focus_dd, out_focus_html,
        out_worked_example, out_whatif_text, out_trythis_text,
        student_answer_input, student_feedback_box,
        history_state, history_html, history_dd,
        *calc_nums, calc_out,
    ]

    def on_crack(eq_text, image, history):
        text = (eq_text or "").strip()
        if not text and image:
            text = identify_from_image(image)
            if not text:
                gr.Warning("I couldn't recognise an equation in that image. Try typing its name.")
                return [gr.update()] * len(CRACK_OUTPUTS)
        if not text:
            gr.Warning("Type an equation name, upload a photo, or pick a quick equation first.")
            return [gr.update()] * len(CRACK_OUTPUTS)

        key, data, matched = get_equation_data(text)
        if not matched:
            gr.Info(f"No built-in match for “{text}” — showing the Ergun Equation instead.")

        history = [key] + [k for k in (history or []) if k != key][:19]
        symbols = [s[0] for s in data["symbols"]]
        annotated = key in ANNOTATED_LATEX

        return view_updates("result", key) + [
            key,
            f"<span class='pill-topic'>{html.escape(data['tag'])}</span>",
            f"<h1 class='result-title'>{html.escape(key)}</h1>",
            ANNOTATED_LATEX.get(key, data["latex"]),
            ERGUN_TAGS_HTML if annotated else "",
            para(data["for"]),
            build_symbols_table_html(data["symbols"]),
            gr.update(choices=symbols, value=symbols[0]),
            build_focus_html(key, symbols[0]),
            build_steps_html(data["worked"]),
            para(data["whatif"]),
            para(data["trythis"]),
            "",
            gr.update(value="", visible=False),
            history,
            history_markup(history),
            gr.update(choices=history, value=history[0]),
            *calc_input_updates(key),
            render_calc(key, [v for _, v in CALCS[key]["inputs"]]),
        ]

    def on_calc(key, *values):
        return render_calc(key, values)

    def on_preview(text):
        text = (text or "").strip()
        if len(text) < 3:
            return gr.update(value="", visible=False)
        key, data, matched = get_equation_data(text)
        return gr.update(value=data["latex"], visible=True) if matched else gr.update(value="", visible=False)

    def on_focus(key, symbol):
        return build_focus_html(key, symbol) if symbol else ""

    def go(name):
        return lambda: view_updates(name)

    def check_ans(key, student_ans):
        if not (student_ans or "").strip():
            return gr.update(value="⚠️ Please enter an answer or calculation first.", visible=True)
        prompt = (
            f"Equation: {key}\n"
            f"Problem: {EQUATION_INFO[key]['trythis']}\n"
            f"Student answer: {student_ans}\n"
            "Check if correct. Be brief, encouraging, max 2 sentences."
        )
        try:
            r = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": "You check engineering math for a diploma student. Be kind and brief (max 2 sentences)."},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                },
                timeout=45,
            )
            fb = r.json().get("message", {}).get("content", "Good attempt!")
            return gr.update(value=f"🎓 **Tutor feedback:** {fb}", visible=True)
        except Exception:
            return gr.update(
                value="⚠️ Couldn't reach the local model, so I can't check this right now. Make sure `ollama serve` is running and try again.",
                visible=True,
            )

    def clear_history():
        return [], history_markup([]), gr.update(choices=[], value=None)

    scroll_quick = "() => setTimeout(() => document.getElementById('quick-start')?.scrollIntoView({behavior:'smooth'}), 150)"

    # Crack actions
    btn_main_crack.click(on_crack, [input_equation_text, upload_image_box, history_state], CRACK_OUTPUTS)
    input_equation_text.submit(on_crack, [input_equation_text, upload_image_box, history_state], CRACK_OUTPUTS)
    for name, btn in quick_buttons.items():
        btn.click(lambda h, n=name: on_crack(n, None, h), [history_state], CRACK_OUTPUTS)

    # Navigation
    for btn in (header_back_btn, nav_btn_home):
        btn.click(go("home"), outputs=VIEW_OUTPUTS)
    nav_btn_quick.click(go("quick"), outputs=VIEW_OUTPUTS).then(None, js=scroll_quick)
    nav_btn_upload.click(go("upload"), outputs=VIEW_OUTPUTS)
    nav_btn_history.click(go("history"), outputs=VIEW_OUTPUTS)
    btn_tab_upload.click(go("upload"), outputs=VIEW_OUTPUTS)
    btn_tab_quick.click(go("quick"), outputs=VIEW_OUTPUTS).then(None, js=scroll_quick)

    # History
    history_open_btn.click(lambda k, h: on_crack(k, None, h) if k else [gr.update()] * len(CRACK_OUTPUTS),
                           [history_dd, history_state], CRACK_OUTPUTS)
    history_clear_btn.click(clear_history, outputs=[history_state, history_html, history_dd])

    # Result interactions
    gr.on(triggers=[n.change for n in calc_nums], fn=on_calc, inputs=[current_eq, *calc_nums], outputs=calc_out, show_progress="hidden")
    input_equation_text.change(on_preview, input_equation_text, formula_preview_box, show_progress="hidden")
    focus_dd.change(on_focus, [current_eq, focus_dd], out_focus_html)
    student_answer_btn.click(check_ans, [current_eq, student_answer_input], student_feedback_box)
    student_answer_input.submit(check_ans, [current_eq, student_answer_input], student_feedback_box)

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(), css=APP_CSS)
