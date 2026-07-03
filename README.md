# Digital Lending: Portfolio Optimization

![Python](https://img.shields.io/badge/Python-pandas%20%7C%20numpy-3776AB?logo=python&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-Analysis-F37626?logo=jupyter&logoColor=white)
![LaTeX](https://img.shields.io/badge/LaTeX-Report-008080?logo=latex&logoColor=white)

An end-to-end credit-risk and portfolio-strategy project for a digital lending institution (NBFC). Working from a synthetic-but-realistic loan book, the analysis diagnoses **where risk is concentrated, why fast growth is degrading loan quality, and how pricing fails to track risk** — then translates the findings into a credit policy package projected to nearly triple risk-adjusted margin.

The emphasis throughout is on **decisions, not data dumps**: every metric is built to answer a question a Chief Risk Officer would actually ask.

---

## The Business Question

> **How can a digital lender use end-to-end customer and transaction data to strengthen risk assessment, catch delinquency early, fix pricing, and grow the book without degrading it?**

Across **39,913 loans** (₹377.5 Cr disbursed · 24,000 borrowers · 36 monthly cohorts), risk-adjusted contribution margin sat at just **1.42%**, and **13.7%** of disbursed value had ever reached 90+ days past due. The core finding: these losses are **concentrated, identifiable at application, and partly self-inflicted** through channel and pricing choices — which means they are fixable.

---

## Project Structure 

---

## Tools Used

| Tool | Purpose |
|---|---|
| **Python (pandas, numpy)** | Synthetic data generation, feature engineering, analysis |
| **Jupyter Notebook** | Segmentation, channel economics, early-warning backtest |
| **LaTeX** | Professional CRO report formatting |
| **PowerPoint** | Stakeholder deck |

---

## Methodology

### 1. Synthetic Data Generation (Python)
The brief required designing our own dataset. We built a **seeded, fully reproducible** 39,913-loan portfolio spanning **7 data areas** — customer profile, loan & product terms, monthly repayment behaviour, behavioural signals, acquisition, time dimension, and outcomes. The generator embeds realistic causal relationships (weaker profiles default more, volatility precedes delinquency, cheap fast growth is adversely selected, newer cohorts behave worse) **under statistical noise**, so every finding is recovered through analysis rather than assumed.

### 2. Risk Segmentation
Built **6 rule-based segments** from three attributes known at application — bureau band × employment type × cash-flow volatility. Rules were chosen over clustering so each segment is auditable and directly implementable as a policy.

| Segment | Share | Default (value) | Margin | Avg APR |
|---|---|---|---|---|
| S1 Anchor Salaried Prime | 18.6% | 3.6% | +3.99% | 19.9% |
| S2 Established Self-Employed | 23.9% | 8.8% | **+5.46%** | 21.4% |
| S3 Stable New-to-Credit | 17.0% | 16.3% | −0.05% | 23.1% |
| S4 Mid-Book Mixed | 28.9% | 16.5% | +0.80% | 22.8% |
| S5 Volatile Gig & Informal | 7.2% | 24.5% | −5.65% | 23.9% |
| S6 Stressed Subprime | 4.4% | 36.6% | **−10.07%** | 24.9% |

### 3. Channel Economics
Modeled acquisition cost, approval speed, and credit outcomes across **4 channels** to test whether growth was buying quality.

| Channel | Share | CAC/loan | Default (value) | Margin |
|---|---|---|---|---|
| DSA / Aggregator | 33.8% | ₹3,196 | 19.0% | **−2.7%** |
| Digital Marketing | 30.4% | ₹2,303 | 12.9% | +2.1% |
| Organic / Repeat | 26.0% | ₹451 | 9.0% | **+5.6%** |
| Partnership / Embedded | 9.9% | ₹1,095 | 10.4% | +2.4% |

### 4. Early Warning System (EWS)
Backtested a deliberately simple **2-trigger rule** — partial payments in 2 of the last 3 months, or any 30-DPD event — on **3,16,962** monthly repayment records. Simplicity was intentional: the rule is explainable to a regulator, a collections agent, and the customer.

- Flagged **77.2%** of eventual defaulters before default (median **2-month** lead)
- **4.0× lift** over base rate → 1 default per 3 outreach calls, vs 1 per 13 undirected

### 5. Policy Impact Simulation
Each policy move was simulated on the actual book. Mechanical effects (removing losses, added interest) come straight from the data; behavioural responses (repricing attrition, cure rate) are stated assumptions, separated explicitly from results.

### 6. Credit Policy Package
Findings translated into a three-move, two-quarter plan, each with explicit triggers, rollout timelines, and stated trade-offs — delivered as a CRO report and a stakeholder deck.

---

## Key Findings

1. **Risk is concentrated and visible at application.** Two volatile segments hold **11.6%** of the book but drive **24.5%** of all losses; default spans **3.6% → 36.6%** across segments, all knowable on day one.

2. **The growth engine is adversely selected.** The DSA/aggregator channel grew from **23% → 42%** of originations while running at **−2.7% margin** and **19.0%** default — paying the most (₹3,196 CAC) to acquire the worst borrowers. Notably, speed isn't the culprit: the faster Partnership channel performs fine, so the problem is volume-incentivised intermediaries.

3. **Pricing doesn't track risk.** APR spans only **5 points** (19.9% → 24.9%) while default spans **33 points** (3.6% → 36.6%) — safe borrowers subsidise risky ones, and competitors can poach the best.

4. **Clear product traps.** 36-month personal loans default at **18.4%** vs **8.9%** at 12 months; sub-₹8k BNPL has excellent credit (**1.4%** default) but loses **~32 paise per rupee** — a cost-structure problem, not a credit one.

5. **Defaults are predictable.** Repayment behaviour deteriorates **~2 months** before default, making preventive collections viable.

---

## Strategic Recommendation

A **three-move, two-quarter** policy package:

| Move | Timeline | Action |
|---|---|---|
| **1. Exit the Red Zone** | Immediate | Decline aggregator-sourced grade D/E applicants who are subprime or volatile — 8.5% of volume, 22% of losses |
| **2. Reprice the Amber Middle** | Next cycle | +200 bps on C/D grades outside the red zone; term caps on PL, BNPL, SME |
| **3. Stand Up Early Warning** | 60–90 days | Deploy the 2-trigger rule into tiered collections |

**Projected impact:** default rate **13.7% → 9.4%**, risk-adjusted margin **1.42% → 3.87%** (**≈₹9 Cr/yr** on the current book) for an **8.5%** volume trade-off.

> These are modeled projections on a synthetic dataset; assumptions (LGD, repricing elasticity, cure rate) are stated explicitly in the report.

---


## Acknowledgements

Project brief by the **Consulting & Analytics Club, IIT Guwahati**.

---

## Authors

**PALLAV PRATIBH** · **MANNAT SHRIVASTAV** · **KAPIL PARODA**
