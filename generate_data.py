"""
Synthetic data generator: digital lending portfolio (India, emerging-market NBFC style).
Embeds the causal relationships required by the problem statement:
  - weaker profiles -> higher risk
  - higher risk -> tighter terms / higher pricing (imperfectly, via a noisy scorecard)
  - deteriorating payment behaviour precedes default
  - higher cash-flow volatility -> higher delinquency likelihood
  - faster/cheaper acquisition (aggregator) -> adverse selection
  - newer cohorts (2025 aggregator-heavy) behave worse
Snapshot date: 2026-03 (loans originated 2023-01 .. 2025-12).
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

N_CUST = 24000
SNAPSHOT = pd.Period("2026-03", freq="M")

# ---------------- customers ----------------
geo = rng.choice(["Metro", "Tier-2", "Tier-3"], N_CUST, p=[0.36, 0.40, 0.24])
emp = rng.choice(["Salaried", "Self-employed", "Gig", "Informal"], N_CUST, p=[0.40, 0.28, 0.22, 0.10])

# monthly income (INR), lognormal by employment x geography
inc_mu = {"Salaried": 10.55, "Self-employed": 10.45, "Gig": 10.05, "Informal": 9.85}
geo_adj = {"Metro": 0.22, "Tier-2": 0.0, "Tier-3": -0.18}
income = np.array([rng.lognormal(inc_mu[e] + geo_adj[g], 0.45) for e, g in zip(emp, geo)])
income = np.clip(income, 9000, 600000).round(-2)

# bureau band: depends on employment + geography
def bureau_probs(e, g):
    base = {"Salaried": [0.42, 0.30, 0.10, 0.18],
            "Self-employed": [0.30, 0.32, 0.16, 0.22],
            "Gig": [0.14, 0.26, 0.22, 0.38],
            "Informal": [0.08, 0.20, 0.27, 0.45]}[e]  # prime, near, sub, thin
    p = np.array(base, dtype=float)
    if g == "Tier-3":
        p = p + np.array([-0.05, -0.02, 0.02, 0.05])
    if g == "Metro":
        p = p + np.array([0.04, 0.01, -0.01, -0.04])
    p = np.clip(p, 0.01, None); return p / p.sum()

bureau = np.array([rng.choice(["Prime", "Near-prime", "Subprime", "Thin-file"], p=bureau_probs(e, g))
                   for e, g in zip(emp, geo)])

# behavioural signals (account-aggregator style)
cons_mu = {"Salaried": 0.78, "Self-employed": 0.62, "Gig": 0.52, "Informal": 0.45}
cashflow_consistency = np.clip(np.array([rng.normal(cons_mu[e], 0.13) for e in emp]), 0.05, 0.98)
balance_volatility = np.clip(1.05 - cashflow_consistency + rng.normal(0, 0.10, N_CUST), 0.05, 1.4)
spending_shock = (rng.random(N_CUST) < np.clip(0.08 + 0.35 * (balance_volatility - 0.3), 0.03, 0.55)).astype(int)

customers = pd.DataFrame({
    "customer_id": [f"C{100000+i}" for i in range(N_CUST)],
    "geography": geo, "employment_type": emp,
    "monthly_income_inr": income.astype(int),
    "bureau_band": bureau,
    "cashflow_consistency": cashflow_consistency.round(3),
    "balance_volatility": balance_volatility.round(3),
    "spending_shock_flag": spending_shock,
})

# ---------------- loans ----------------
# 1.0-1.6 loans per customer; volume grows over time; aggregator share grows in 2025
n_loans_per = rng.choice([1, 1, 1, 2, 2, 3], N_CUST)
rows = []
months = pd.period_range("2023-01", "2025-12", freq="M")
# origination volume weights: growth curve
mw = np.linspace(1.0, 2.6, len(months)); mw = mw / mw.sum()

prod_mix = {"Salaried": [0.55, 0.40, 0.05], "Self-employed": [0.35, 0.20, 0.45],
            "Gig": [0.40, 0.55, 0.05], "Informal": [0.30, 0.62, 0.08]}  # PL, BNPL, SME

loan_id = 0
for i in range(N_CUST):
    for _ in range(n_loans_per[i]):
        m = rng.choice(len(months), p=mw)
        om = months[m]
        prod = rng.choice(["Personal Loan", "BNPL", "SME Working Capital"], p=prod_mix[emp[i]])
        # channel mix: shifts toward aggregator over time; BNPL skews partnership
        t = m / (len(months) - 1)  # 0..1
        if prod == "BNPL":
            ch_p = np.array([0.18, 0.10 + 0.18 * t, 0.22, 0.50 - 0.18 * t])
        else:
            ch_p = np.array([0.34 - 0.06 * t, 0.22 + 0.22 * t, 0.32 - 0.10 * t, 0.12 - 0.06 * t])
        ch_p = np.clip(ch_p, 0.02, None); ch_p /= ch_p.sum()
        channel = rng.choice(["Digital Marketing", "DSA / Aggregator", "Organic / Repeat", "Partnership / Embedded"], p=ch_p)

        if prod == "Personal Loan":
            ticket = float(np.clip(rng.lognormal(11.2, 0.5), 25000, 500000))
            tenure = int(rng.choice([6, 9, 12, 18, 24, 36], p=[0.10, 0.12, 0.30, 0.24, 0.16, 0.08]))
        elif prod == "BNPL":
            ticket = float(np.clip(rng.lognormal(9.0, 0.55), 2000, 60000))
            tenure = int(rng.choice([1, 3, 6, 9], p=[0.22, 0.40, 0.30, 0.08]))
        else:
            ticket = float(np.clip(rng.lognormal(12.6, 0.5), 100000, 2500000))
            tenure = int(rng.choice([6, 12, 18, 24], p=[0.20, 0.40, 0.25, 0.15]))
        ticket = round(ticket, -2)

        rows.append((f"L{500000+loan_id}", customers.customer_id[i], i, str(om), prod, channel, ticket, tenure))
        loan_id += 1

loans = pd.DataFrame(rows, columns=["loan_id", "customer_id", "ci", "origination_month",
                                    "product", "channel", "ticket_size_inr", "tenure_months"])
L = len(loans)
ci = loans.ci.values
om_idx = loans.origination_month.map({str(m): k for k, m in enumerate(months)}).values

# --- origination risk grade: noisy scorecard (lender's imperfect view) ---
bnum = pd.Series(bureau).map({"Prime": -1.0, "Near-prime": -0.2, "Subprime": 0.9, "Thin-file": 0.55}).values
enum = pd.Series(emp).map({"Salaried": -0.5, "Self-employed": 0.1, "Gig": 0.45, "Informal": 0.7}).values
score = (0.9 * bnum[ci] + 0.6 * enum[ci] + 0.9 * (balance_volatility[ci] - 0.45)
         + 0.5 * (np.log(loans.ticket_size_inr.values / (income[ci] * 3 + 1)))
         + rng.normal(0, 0.55, L))  # noise = scorecard imperfection
qs = np.quantile(score, [0.25, 0.50, 0.75, 0.92])
grade = np.select([score < qs[0], score < qs[1], score < qs[2], score < qs[3]],
                  ["A", "B", "C", "D"], default="E")
loans["risk_grade"] = grade

# pricing: base by product + grade premium (risk-based but compressed -> mispricing to find)
base_apr = loans["product"].map({"Personal Loan": 0.19, "BNPL": 0.24, "SME Working Capital": 0.205}).values
grade_prem = pd.Series(grade).map({"A": -0.025, "B": 0.0, "C": 0.02, "D": 0.035, "E": 0.045}).values
loans["apr"] = (base_apr + grade_prem + rng.normal(0, 0.008, L)).round(4)

# acquisition economics
cac_mu = {"Digital Marketing": 2300, "DSA / Aggregator": 3200, "Organic / Repeat": 450, "Partnership / Embedded": 1100}
loans["cac_inr"] = [int(max(150, rng.normal(cac_mu[c], cac_mu[c] * 0.18))) for c in loans.channel]
tat_mu = {"Digital Marketing": 7, "DSA / Aggregator": 3, "Organic / Repeat": 10, "Partnership / Embedded": 2}
loans["approval_tat_hours"] = [round(max(0.5, rng.gamma(2.2, tat_mu[c] / 2.2)), 1) for c in loans.channel]

# --- true default probability (12m horizon, scaled to tenure exposure) ---
true_b = pd.Series(bureau).map({"Prime": -1.15, "Near-prime": -0.35, "Subprime": 0.95, "Thin-file": 0.45}).values
true_e = pd.Series(emp).map({"Salaried": -0.45, "Self-employed": 0.05, "Gig": 0.40, "Informal": 0.65}).values
true_g = pd.Series(geo).map({"Metro": -0.05, "Tier-2": 0.0, "Tier-3": 0.18}).values
ch_sel = loans.channel.map({"Digital Marketing": 0.10, "DSA / Aggregator": 0.42,
                            "Organic / Repeat": -0.38, "Partnership / Embedded": 0.02}).values
prod_eff = loans["product"].map({"Personal Loan": 0.0, "BNPL": 0.18, "SME Working Capital": -0.10}).values
tk_inc = np.log(loans.ticket_size_inr.values / (income[ci] * 3 + 1))
vint = np.where(om_idx >= 24, 0.22, np.where(om_idx >= 12, 0.08, 0.0))  # 2025 cohorts worse
vint = vint * np.where(loans.channel.values == "DSA / Aggregator", 1.8, 0.7)  # concentrated in aggregator
ten_eff = 0.012 * (loans.tenure_months.values - 12)

logit = (-2.62 + 0.95 * true_b[ci] + 0.75 * true_e[ci] + true_g[ci]
         + 1.15 * (balance_volatility[ci] - 0.45) + 0.30 * spending_shock[ci]
         + 0.45 * np.clip(tk_inc, -2.5, 2.5) + ch_sel + prod_eff + vint + ten_eff
         + rng.normal(0, 0.25, L))
pd12 = 1 / (1 + np.exp(-logit))
exposure = np.clip(loans.tenure_months.values / 12, 0.25, 1.6)
p_def = np.clip(pd12 * exposure, 0.002, 0.92)
defaults = rng.random(L) < p_def

# default month (months on book at first 90+); peak months 3-9
mob_total = np.minimum(loans.tenure_months.values, (SNAPSHOT - pd.PeriodIndex(loans.origination_month, freq="M")).map(lambda x: x.n).values)
mob_total = np.maximum(mob_total, 1)
raw_dm = np.maximum(2, rng.gamma(3.2, 2.0, L).astype(int))
default_month = np.minimum(raw_dm, np.maximum(2, loans.tenure_months.values))
observed_default = defaults & (default_month <= mob_total)
loans["months_on_book"] = mob_total
loans["default_flag"] = observed_default.astype(int)
loans["default_mob"] = np.where(observed_default, default_month, 0)

# ---------------- monthly repayment panel ----------------
pan_loan, pan_mob, pan_status = [], [], []
vol = balance_volatility[ci]
base_partial = np.clip(0.03 + 0.18 * (vol - 0.35), 0.01, 0.30)
base_late = np.clip(0.01 + 0.10 * (vol - 0.35), 0.004, 0.18)
for k in range(L):
    T = int(mob_total[k]); dm = int(default_month[k]) if observed_default[k] else 10**6
    for m in range(1, min(T, dm) + 1):
        ramp = max(0, 4 - (dm - m)) if dm < 10**6 else 0  # 0..4 in the 4 months before default
        p_part = min(0.85, base_partial[k] + 0.17 * ramp)
        p_late = min(0.80, base_late[k] + 0.13 * ramp)
        u = rng.random()
        if m == dm:
            s = "DPD90+"
        elif u < p_late:
            s = "DPD30"
        elif u < p_late + p_part:
            s = "Partial"
        else:
            s = "OnTime"
        pan_loan.append(k); pan_mob.append(m); pan_status.append(s)

panel = pd.DataFrame({"k": pan_loan, "mob": pan_mob, "status": pan_status})
panel["loan_id"] = loans.loan_id.values[panel.k.values]

# ---------------- economics ----------------
months_earning = np.where(observed_default, np.maximum(default_month - 1, 1), mob_total)
# declining-balance: avg outstanding ~ 55% of ticket over life
income_inr = loans.apr.values * loans.ticket_size_inr.values * 0.55 * (months_earning / 12)
fees = 0.015 * loans.ticket_size_inr.values
lgd = loans["product"].map({"Personal Loan": 0.70, "BNPL": 0.82, "SME Working Capital": 0.58}).values
ead_factor = np.clip(1 - (default_month - 1) / np.maximum(loans.tenure_months.values, 1), 0.25, 1.0)
loss = np.where(observed_default, lgd * ead_factor * loans.ticket_size_inr.values, 0.0)
opex = 0.012 * loans.ticket_size_inr.values + 90 * mob_total
loans["interest_fee_income_inr"] = (income_inr + fees).round(0)
loans["credit_loss_inr"] = loss.round(0)
loans["opex_inr"] = opex.round(0)
loans["net_margin_inr"] = (income_inr + fees - loss - opex - loans.cac_inr.values).round(0)
loans["net_margin_pct_disb"] = (loans.net_margin_inr / loans.ticket_size_inr).round(4)

loans = loans.drop(columns=["ci"])
customers.to_csv("/home/claude/out/customers.csv", index=False)
loans.to_csv("/home/claude/out/loans.csv", index=False)
panel[["loan_id", "mob", "status"]].to_csv("/home/claude/out/repayment_monthly.csv", index=False)
print("customers", customers.shape, "loans", loans.shape, "panel", panel.shape)
print("portfolio 90+ ever rate (count):", round(loans.default_flag.mean() * 100, 2), "%")
disb = loans.ticket_size_inr.sum()
print("disbursed (INR cr):", round(disb / 1e7, 1))
print("value-weighted default:", round((loans.default_flag * loans.ticket_size_inr).sum() / disb * 100, 2), "%")
print("net margin %% of disbursed:", round(loans.net_margin_inr.sum() / disb * 100, 2), "%")
