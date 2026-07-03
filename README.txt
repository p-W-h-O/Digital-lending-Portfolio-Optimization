Digital Lending: Portfolio Optimization — reproducibility bundle
================================================================
dataset/
  customers.csv          24,000 borrowers: geography, income proxy, employment,
                         bureau band, cash-flow consistency, balance volatility,
                         spending-shock flag
  loans.csv              39,913 loans: product, ticket, tenure, APR, risk grade,
                         channel, CAC, approval TAT, months on book, default flag,
                         economics (income, loss, opex, net margin)
  loans_enriched.csv     loans joined with customer attributes + segment labels
  repayment_monthly.csv  316,962 loan-month records: OnTime / Partial / DPD30 / DPD90+

code/
  generate_data.py       synthetic data generator (seeded, fully reproducible;
                         embeds the causal relationships required by the brief)
  analyze.py             full analysis: segmentation, channel economics, product
                         sweet spots, vintage curves, EWS backtest, policy simulation
  summary.json           every number used in the report and deck, as computed

Run order: python generate_data.py && python analyze.py  (numpy + pandas required)
