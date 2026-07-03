import json
import numpy as np
import pandas as pd

cust = pd.read_csv("/home/claude/out/customers.csv")
loans = pd.read_csv("/home/claude/out/loans.csv")
panel = pd.read_csv("/home/claude/out/repayment_monthly.csv")
df = loans.merge(cust, on="customer_id")
df["om"] = pd.PeriodIndex(df.origination_month, freq="M")
df["vintage_half"] = df.om.dt.year.astype(str) + np.where(df.om.dt.month <= 6, " H1", " H2")
disb_total = df.ticket_size_inr.sum()

S = {}

# ---------- portfolio snapshot ----------
S["portfolio"] = {
    "n_customers": int(cust.shape[0]),
    "n_loans": int(df.shape[0]),
    "disbursed_cr": round(disb_total / 1e7, 1),
    "default_rate_count": round(df.default_flag.mean() * 100, 1),
    "default_rate_value": round((df.default_flag * df.ticket_size_inr).sum() / disb_total * 100, 1),
    "net_margin_pct": round(df.net_margin_inr.sum() / disb_total * 100, 2),
    "net_margin_cr": round(df.net_margin_inr.sum() / 1e7, 1),
    "product_mix": {k: round(v / disb_total * 100, 1) for k, v in df.groupby("product").ticket_size_inr.sum().items()},
    "total_loss_cr": round(df.credit_loss_inr.sum() / 1e7, 1),
}

# originations by half-year + value default rate by vintage (seasoned >= 6 mob)
v = df.groupby("vintage_half").agg(disb=("ticket_size_inr", "sum"), n=("loan_id", "count")).reset_index()
v["disb_cr"] = (v.disb / 1e7).round(1)
seas = df[df.months_on_book >= 6].copy()
seas["def6"] = ((seas.default_flag == 1) & (seas.default_mob <= 6)).astype(int)
vd = seas.groupby("vintage_half").apply(lambda g: (g.def6 * g.ticket_size_inr).sum() / g.ticket_size_inr.sum() * 100, include_groups=False)
S["vintages"] = {"labels": v.vintage_half.tolist(), "disb_cr": v.disb_cr.tolist(),
                 "default_value_pct": [round(vd.get(h, np.nan), 1) for h in v.vintage_half]}

# ---------- Q1: segmentation ----------
def seg(r):
    vol_hi = r.balance_volatility > 0.55
    if r.bureau_band in ("Prime", "Near-prime") and r.employment_type == "Salaried" and not vol_hi:
        return "S1 Anchor Salaried Prime"
    if r.bureau_band in ("Prime", "Near-prime") and r.employment_type == "Self-employed" and r.cashflow_consistency >= 0.55:
        return "S2 Established Self-Employed"
    if r.bureau_band == "Thin-file" and not vol_hi:
        return "S3 Stable New-to-Credit"
    if r.bureau_band == "Subprime" and vol_hi:
        return "S6 Stressed Subprime"
    if vol_hi and r.employment_type in ("Gig", "Informal"):
        return "S5 Volatile Gig & Informal"
    return "S4 Mid-Book Mixed"

df["segment"] = df.apply(seg, axis=1)
seg_order = ["S1 Anchor Salaried Prime", "S2 Established Self-Employed", "S3 Stable New-to-Credit",
             "S4 Mid-Book Mixed", "S5 Volatile Gig & Informal", "S6 Stressed Subprime"]
g = df.groupby("segment")
seg_tbl = pd.DataFrame({
    "share_value_pct": (g.ticket_size_inr.sum() / disb_total * 100).round(1),
    "default_value_pct": (g.apply(lambda x: (x.default_flag * x.ticket_size_inr).sum() / x.ticket_size_inr.sum() * 100, include_groups=False)).round(1),
    "net_margin_pct": (g.apply(lambda x: x.net_margin_inr.sum() / x.ticket_size_inr.sum() * 100, include_groups=False)).round(2),
    "avg_apr": (g.apr.mean() * 100).round(1),
    "avg_ticket_k": (g.ticket_size_inr.mean() / 1000).round(0),
}).loc[seg_order].reset_index()
S["segments"] = seg_tbl.to_dict(orient="records")

# ---------- Q2: channels ----------
g = df.groupby("channel")
ch_tbl = pd.DataFrame({
    "share_value_pct": (g.ticket_size_inr.sum() / disb_total * 100).round(1),
    "cac": g.cac_inr.mean().round(0),
    "tat_h": g.approval_tat_hours.median().round(1),
    "default_value_pct": (g.apply(lambda x: (x.default_flag * x.ticket_size_inr).sum() / x.ticket_size_inr.sum() * 100, include_groups=False)).round(1),
    "net_margin_pct": (g.apply(lambda x: x.net_margin_inr.sum() / x.ticket_size_inr.sum() * 100, include_groups=False)).round(2),
    "net_margin_per_loan": g.net_margin_inr.mean().round(0),
}).reset_index()
S["channels"] = ch_tbl.to_dict(orient="records")

# aggregator vintage deterioration (seasoned)
agg_v = seas[seas.channel == "DSA / Aggregator"].groupby("vintage_half").apply(
    lambda g: (g.def6 * g.ticket_size_inr).sum() / g.ticket_size_inr.sum() * 100, include_groups=False)
org_v = seas[seas.channel == "Organic / Repeat"].groupby("vintage_half").apply(
    lambda g: (g.def6 * g.ticket_size_inr).sum() / g.ticket_size_inr.sum() * 100, include_groups=False)
labels = [h for h in S["vintages"]["labels"] if h in agg_v.index and h in org_v.index]
S["channel_vintage"] = {"labels": labels,
                        "aggregator": [round(agg_v[h], 1) for h in labels],
                        "organic": [round(org_v[h], 1) for h in labels]}
# aggregator share of originations over time
agg_share = df.groupby("vintage_half").apply(
    lambda g: g.loc[g.channel == "DSA / Aggregator", "ticket_size_inr"].sum() / g.ticket_size_inr.sum() * 100, include_groups=False)
S["agg_share"] = {"labels": S["vintages"]["labels"], "pct": [round(agg_share.get(h, np.nan), 1) for h in S["vintages"]["labels"]]}

# ---------- Q3: product x ticket sweet spot ----------
def tband(r):
    if r["product"] == "BNPL":
        edges, lab = [8000, 20000], ["< 8k", "8-20k", "> 20k"]
    elif r["product"] == "Personal Loan":
        edges, lab = [60000, 150000], ["< 60k", "60-150k", "> 150k"]
    else:
        edges, lab = [250000, 600000], ["< 2.5L", "2.5-6L", "> 6L"]
    t = r.ticket_size_inr
    return lab[0] if t < edges[0] else (lab[1] if t < edges[1] else lab[2])

df["ticket_band"] = df.apply(tband, axis=1)
pt = df.groupby(["product", "ticket_band"]).apply(
    lambda g: pd.Series({"def": (g.default_flag * g.ticket_size_inr).sum() / g.ticket_size_inr.sum() * 100,
                         "margin": g.net_margin_inr.sum() / g.ticket_size_inr.sum() * 100,
                         "share": g.ticket_size_inr.sum() / disb_total * 100}), include_groups=False).round(2).reset_index()
S["product_ticket"] = pt.to_dict(orient="records")

ten = df[df["product"] == "Personal Loan"].groupby("tenure_months").apply(
    lambda g: pd.Series({"def": (g.default_flag * g.ticket_size_inr).sum() / g.ticket_size_inr.sum() * 100,
                         "margin": g.net_margin_inr.sum() / g.ticket_size_inr.sum() * 100}), include_groups=False).round(2).reset_index()
S["pl_tenure"] = ten.to_dict(orient="records")

# ---------- Q ews: early warning backtest ----------
p = panel.merge(loans[["loan_id", "default_flag", "default_mob", "months_on_book"]], on="loan_id")
p = p.sort_values(["loan_id", "mob"])
p["is_partial"] = (p.status == "Partial").astype(int)
p["is_dpd30"] = (p.status == "DPD30").astype(int)
gp = p.groupby("loan_id")
p["part_roll3"] = gp.is_partial.rolling(3, min_periods=1).sum().values
p["dpd_roll3"] = gp.is_dpd30.rolling(3, min_periods=1).sum().values
p["flag"] = ((p.part_roll3 >= 2) | (p.is_dpd30 == 1)).astype(int)

flags = p[p.flag == 1].groupby("loan_id").mob.min().rename("first_flag_mob")
ld = loans.set_index("loan_id").join(flags)
defs = ld[ld.default_flag == 1]
flagged_defs = defs[defs.first_flag_mob.notna() & (defs.first_flag_mob <= defs.default_mob - 1)]
lead2 = defs[defs.first_flag_mob.notna() & (defs.first_flag_mob <= defs.default_mob - 2)]
nondefs = ld[ld.default_flag == 0]
fp = nondefs.first_flag_mob.notna().mean()
flagged_all = ld[ld.first_flag_mob.notna()]
precision = flagged_all.default_flag.mean()
S["ews"] = {
    "capture_any": round(len(flagged_defs) / len(defs) * 100, 1),
    "capture_60d": round(len(lead2) / len(defs) * 100, 1),
    "median_lead_months": float(np.median((defs.default_mob - defs.first_flag_mob).dropna().clip(lower=0))),
    "false_positive_pct": round(fp * 100, 1),
    "precision_pct": round(precision * 100, 1),
    "base_rate_pct": round(ld.default_flag.mean() * 100, 1),
    "lift": round(precision / ld.default_flag.mean(), 1),
}

# ---------- policy simulation ----------
red = df[(df.channel == "DSA / Aggregator") & (df.risk_grade.isin(["D", "E"])) &
         ((df.bureau_band == "Subprime") | (df.balance_volatility > 0.55))]
S["loss_concentration"] = {
    "s5s6_share_book": round(df.loc[df.segment.isin(["S5 Volatile Gig & Informal", "S6 Stressed Subprime"]), "ticket_size_inr"].sum() / disb_total * 100, 1),
    "s5s6_share_loss": round(df.loc[df.segment.isin(["S5 Volatile Gig & Informal", "S6 Stressed Subprime"]), "credit_loss_inr"].sum() / df.credit_loss_inr.sum() * 100, 1),
}
S["red_zone"] = {
    "share_value_pct": round(red.ticket_size_inr.sum() / disb_total * 100, 1),
    "share_count_pct": round(len(red) / len(df) * 100, 1),
    "default_value_pct": round((red.default_flag * red.ticket_size_inr).sum() / red.ticket_size_inr.sum() * 100, 1),
    "net_margin_pct": round(red.net_margin_inr.sum() / red.ticket_size_inr.sum() * 100, 2),
    "loss_cr": round(red.credit_loss_inr.sum() / 1e7, 1),
    "loss_share_pct": round(red.credit_loss_inr.sum() / df.credit_loss_inr.sum() * 100, 1),
    "net_margin_cr": round(red.net_margin_inr.sum() / 1e7, 1),
}
# Policy A: stop red zone -> pro-forma portfolio
keep = df.drop(red.index)
S["policy_A"] = {
    "volume_loss_pct": round(red.ticket_size_inr.sum() / disb_total * 100, 1),
    "new_default_value_pct": round((keep.default_flag * keep.ticket_size_inr).sum() / keep.ticket_size_inr.sum() * 100, 1),
    "new_net_margin_pct": round(keep.net_margin_inr.sum() / keep.ticket_size_inr.sum() * 100, 2),
}
# Policy B: +200bps APR on amber zone (grade C/D outside red zone), assume 15% volume attrition
amber = keep[keep.risk_grade.isin(["C", "D"])]
extra_income = 0.02 * amber.ticket_size_inr * 0.55 * (np.minimum(amber.tenure_months, amber.months_on_book) / 12)
amber_margin_new = amber.net_margin_inr.sum() + extra_income.sum()
attrition = 0.15
amber_kept_margin = (1 - attrition) * amber_margin_new
nonamber = keep.drop(amber.index)
new_disb_B = nonamber.ticket_size_inr.sum() + (1 - attrition) * amber.ticket_size_inr.sum()
new_margin_B = nonamber.net_margin_inr.sum() + amber_kept_margin
S["policy_B"] = {
    "amber_share_pct": round(amber.ticket_size_inr.sum() / disb_total * 100, 1),
    "margin_pct_after_AB": round(new_margin_B / new_disb_B * 100, 2),
}
# Policy C: EWS-driven collections; cure 25% of captured would-be defaulters' losses (forward book)
cure = 0.25
captured_loss = keep.loc[keep.default_flag == 1].merge(flags, left_on="loan_id", right_index=True, how="inner")
captured_loss = captured_loss[captured_loss.first_flag_mob <= captured_loss.default_mob - 1]
saved = cure * captured_loss.credit_loss_inr.sum()
S["policy_C"] = {"loss_saved_cr": round(saved / 1e7, 1),
                 "margin_pct_after_ABC": round((new_margin_B + saved * (1 - attrition * 0)) / new_disb_B * 100, 2)}
# combined NPL view: A removes red-zone defaults; C cures 25% of captured remaining defaults
rem_def_value = (keep.default_flag * keep.ticket_size_inr).sum()
cap_def_value = captured_loss.ticket_size_inr.sum()
npl_after = (rem_def_value - cure * cap_def_value) / keep.ticket_size_inr.sum() * 100
S["combined"] = {"npl_before": S["portfolio"]["default_rate_value"], "npl_after": round(npl_after, 1),
                 "margin_before": S["portfolio"]["net_margin_pct"], "margin_after": S["policy_C"]["margin_pct_after_ABC"]}

# top/bottom microsegments for report color
micro = df.groupby(["segment", "channel"]).apply(
    lambda g: pd.Series({"margin": g.net_margin_inr.sum() / g.ticket_size_inr.sum() * 100,
                         "share": g.ticket_size_inr.sum() / disb_total * 100,
                         "def": (g.default_flag * g.ticket_size_inr).sum() / g.ticket_size_inr.sum() * 100}),
    include_groups=False).round(2)
S["best_micro"] = micro.sort_values("margin", ascending=False).head(4).reset_index().to_dict(orient="records")
S["worst_micro"] = micro[micro.share > 0.5].sort_values("margin").head(4).reset_index().to_dict(orient="records")

df.to_csv("/home/claude/out/loans_enriched.csv", index=False)
with open("/home/claude/out/summary.json", "w") as f:
    json.dump(S, f, indent=1, default=str)
print(json.dumps(S, indent=1, default=str))
