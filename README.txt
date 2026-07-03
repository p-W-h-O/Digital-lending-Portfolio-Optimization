# Decoding Customer Value: A SQL-Driven Retention Strategy

![Python](https://img.shields.io/badge/Python-pandas%20%7C%20numpy-3776AB?logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-Segmentation-4479A1?logo=mysql&logoColor=white)
![Power BI](https://img.shields.io/badge/Power%20BI-Dashboard-F2C811?logo=powerbi&logoColor=black)
![Jupyter](https://img.shields.io/badge/Jupyter-EDA-F37626?logo=jupyter&logoColor=white)
![LaTeX](https://img.shields.io/badge/LaTeX-Report-008080?logo=latex&logoColor=white)

A complete customer intelligence project for a direct-to-consumer fashion brand. The analysis builds customer loyalty segmentation from scratch using **only transactional and behavioral data** — no timestamps, no pre-built loyalty scores — and produces a data-backed retention playbook.

---

## The Business Question

> **Is the brand successfully building a loyal customer base, or is it reliant on continuous promotional activity?**

Across **3,900 customers**, the data revealed that only **19.4% qualify as genuinely loyal** (full-price repeat buyers), **43% of all purchases depend on discounts**, and **long-tenure customers show no decline in discount usage over time**. Critically, discounts are tied to the subscription programme rather than to loyalty — the brand is operating a **subsidised** customer base, not a loyal one.

---

## Project Structure
---

## Tools Used

| Tool | Purpose |
|---|---|
| **Python (pandas, numpy)** | Synthetic data generation, feature engineering, analysis |
| **Jupyter Notebook** | Segmentation, channel economics, EWS backtest |
| **MySQL / SQL** | Portfolio segmentation queries |
| **Power BI** | Leadership-facing risk dashboard |
| **LaTeX** | Professional CRO report formatting |

---

## Methodology

### 1. Synthetic Data Generation (Python)
- Built a seeded, reproducible **39,913-loan** portfolio across **7 data areas** — customer profile, loan & product, repayment behaviour, behavioural signals, acquisition, time dimension, and outcomes
- Embedded the brief's causal relationships (weaker profiles riskier, volatility precedes delinquency, adverse selection in cheap growth, worse newer cohorts) **under statistical noise**, so findings are recovered by analysis, not assumed

### 2. Risk Segmentation (SQL / Python)
Built **6 rule-based segments** from three application-time attributes — bureau band × employment type × cash-flow volatility:

| Segment | Share of Book | Default (value) | Margin | Avg APR |
|---|---|---|---|---|
| S1 Anchor Salaried Prime | 18.6% | 3.6% | +3.99% | 19.9% |
| S2 Established Self-Employed | 23.9% | 8.8% | **+5.46%** | 21.4% |
| S3 Stable New-to-Credit | 17.0% | 16.3% | −0.05% | 23.1% |
| S4 Mid-Book Mixed | 28.9% | 16.5% | +0.80% | 22.8% |
| S5 Volatile Gig & Informal | 7.2% | 24.5% | −5.65% | 23.9% |
| S6 Stressed Subprime | 4.4% | 36.6% | **−10.07%** | 24.9% |

### 3. Channel Economics
Modeled acquisition cost, approval speed, and credit outcomes across **4 channels**:

| Channel | Share | CAC/loan | Default (value) | Margin |
|---|---|---|---|---|
| DSA / Aggregator | 33.8% | ₹3,196 | 19.0% | **−2.7%** |
| Digital Marketing | 30.4% | ₹2,303 | 12.9% | +2.1% |
| Organic / Repeat | 26.0% | ₹451 | 9.0% | **+5.6%** |
| Partnership / Embedded | 9.9% | ₹1,095 | 10.4% | +2.4% |

### 4. Early Warning System (EWS)
Backtested a **2-trigger rule** (partial payments in 2 of last 3 months, or any 30-DPD event) on **3,16,962** monthly repayment records:
- Flagged **77.2%** of eventual defaulters before default (median **2-month** lead)
- **4.0× lift** over base rate — 1 default per 3 outreach calls vs 1 per 13

### 5. Dashboard (Power BI)
A leadership risk view built on **6 leading indicators** — vintage default by cohort × channel, EWS flag/conversion, channel risk-adjusted margin, red-zone origination share, roll rates, and top-decile exposure concentration.

### 6. Credit Policy Package
A three-move, two-quarter plan with explicit triggers, rollout timelines, and trade-offs — delivered as a CRO report and stakeholder deck.

---

## Key Findings

1. **Risk is concentrated and visible at application.** Two volatile segments hold just **11.6%** of the book but drive **24.5%** of all credit losses; default spans **3.6% → 36.6%** across segments, all knowable on day one.

2. **The growth engine is adversely selected.** The DSA/aggregator channel grew from **23% → 42%** of originations while running at **−2.7% margin** and **19.0%** default — paying the most (₹3,196 CAC) to acquire the worst borrowers.

3. **Pricing doesn't track risk.** APR spans only **19.9% → 24.9%** (5 points) while default spans **3.6% → 36.6%** (33 points) — safe borrowers subsidise risky ones.

4. **Clear product traps.** 36-month personal loans default at **18.4%** vs **8.9%** at 12 months; sub-₹8k BNPL has excellent credit (1.4% default) but loses **~32 paise per rupee** — a cost problem, not a credit one.

5. **Defaults are predictable.** Behaviour deteriorates **~2 months** before default, making preventive collections viable.

---

## Strategic Recommendation

A **three-move, two-quarter** policy package:

| Move | Timeline | Action |
|---|---|---|
| **1. Exit the Red Zone** | Immediate | Decline aggregator-sourced grade D/E applicants who are subprime or volatile (8.5% of volume, 22% of losses) |
| **2. Reprice the Amber Middle** | Next cycle | +200 bps on C/D grades outside red zone; term caps on PL, BNPL, SME |
| **3. Stand Up Early Warning** | 60–90 days | Deploy 2-trigger rule into tiered collections |

**Projected impact:** default rate **13.7% → 9.4%**, risk-adjusted margin **1.42% → 3.87%** (**≈₹9 Cr/yr**) for an **8.5%** volume trade-off.

Full reasoning, assumptions, and trade-offs are in [`deliverables/credit_policy_report.pdf`](deliverables/credit_policy_report.pdf).

---

## How to Reproduce

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/digital-lending-portfolio-optimization.git

# 2. Install Python dependencies
pip install pandas numpy matplotlib seaborn jupyter

# 3. Generate the dataset and run the analysis
python python/generate_data.py
python analysis/analyze.py

# 4. Load engineered CSVs into MySQL and run sql/segmentation_queries.sql

# 5. Open powerbi/dashboard.pbix in Power BI Desktop
```

---

## Acknowledgements

Project brief by the **Consulting & Analytics Club, IIT Guwahati**.

---

## Authors

**<Your Name>** · **<Teammate 2>** · **<Teammate 3>**


