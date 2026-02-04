# Quantitative Models & Frameworks


## Equity Valuation Models

### Earnings Yield vs Bond Yield (Fed Model)
```
Equity Risk Premium (ERP) = E/P - 10Y Treasury Yield
```

Where `E/P` = Earnings Yield (inverse of P/E ratio)

**Interpretation**:
- Higher ERP → Equities more attractive vs bonds
- Historical average ERP: ~3-4%
- Below 2% → Equities potentially overvalued

### Shiller CAPE (Cyclically Adjusted P/E)
```
CAPE = Current Price / (10-year average of inflation-adjusted earnings)
```

**Historical Reference**:
- Long-term average: ~17x
- Above 25x: Expensive
- Above 30x: Historically preceded corrections
- Below 15x: Historically attractive entry points

### Gordon Growth Model (Dividend Discount)
```
P = D1 / (r - g)
```

Where:
- `P` = Fair value price
- `D1` = Expected dividend next year
- `r` = Required rate of return
- `g` = Dividend growth rate (perpetual)

---

## Fixed Income Models

### Duration & Convexity

**Modified Duration**:
```
Price Change ≈ -Duration × ΔYield × 100
```

Example: Duration of 5, rates rise 1% → Price falls ~5%

**Convexity Adjustment** (for larger yield changes):
```
Price Change ≈ (-Duration × ΔYield + 0.5 × Convexity × ΔYield²) × 100
```

### Breakeven Inflation
```
Breakeven Inflation = Nominal Treasury Yield - TIPS Real Yield
```

**Interpretation**:
- Represents market's expected inflation over the bond's maturity
- Compare to Fed's 2% target and surveys (Michigan, SPF)

### Credit Spread Decomposition
```
Credit Spread = Expected Loss + Liquidity Premium + Risk Premium
```

- **Expected Loss** = Probability of Default × Loss Given Default
- **Liquidity Premium** = Compensation for illiquidity
- **Risk Premium** = Excess return for bearing systematic risk

---

## FX Models

### Uncovered Interest Rate Parity (UIP)
```
E[S(t+1)] / S(t) = (1 + i_domestic) / (1 + i_foreign)
```

Where `S` = Spot exchange rate

**Forward Premium/Discount**:
```
Forward Points = Spot × (i_domestic - i_foreign) × (Days/360)
```

### Real Effective Exchange Rate (REER)
```
REER = Nominal Exchange Rate × (Domestic CPI / Foreign CPI)
```

**Interpretation**:
- Above long-term average → Currency overvalued
- Below long-term average → Currency undervalued

### Purchasing Power Parity (PPP)
```
Implied Fair Value = PPP Exchange Rate = P_domestic / P_foreign
```

**Note**: PPP is a long-term equilibrium concept; short-term deviations are normal.

---

## Economic Indicators & Thresholds

### Yield Curve Recession Signals

| Spread | Threshold | Historical Lead Time |
|--------|-----------|---------------------|
| 10Y-2Y | Inversion (< 0) | 6-24 months |
| 10Y-3M | Inversion (< 0) | 6-18 months |
| Near-Term Forward Spread | < 0 | More timely signal |

**NY Fed Recession Probability Model**:
Uses 10Y-3M spread to estimate probability of recession in next 12 months.

### ISM PMI Economic Regimes

| PMI Level | Economic Condition |
|-----------|-------------------|
| > 55 | Strong expansion |
| 50-55 | Moderate expansion |
| 47-50 | Contraction risk |
| 45-47 | Mild contraction |
| < 45 | Significant contraction |

### Okun's Law
```
ΔUnemployment ≈ -0.5 × (GDP Growth - Trend Growth)
```

For US: ~2% GDP growth needed to keep unemployment stable.

---

## Risk Metrics

### Value at Risk (VaR) - Parametric
```
VaR(α) = μ - σ × Z(α)
```

Where:
- `μ` = Expected return
- `σ` = Standard deviation
- `Z(α)` = Z-score for confidence level (1.65 for 95%, 2.33 for 99%)

### Sharpe Ratio
```
Sharpe = (R_portfolio - R_f) / σ_portfolio
```

**Interpretation**:
- > 1.0: Good
- > 2.0: Very good
- > 3.0: Excellent

### Maximum Drawdown
```
Max DD = (Trough Value - Peak Value) / Peak Value
```

---

## Correlation Framework

### Risk-On / Risk-Off Regime Detection

**Typical Risk-On Correlations**:
- Stocks ↑, Bonds ↓
- USD ↓, EM Currencies ↑
- Credit Spreads ↓
- VIX ↓

**Typical Risk-Off Correlations**:
- Stocks ↓, Bonds ↑
- USD ↑, JPY ↑, CHF ↑
- Credit Spreads ↑
- VIX ↑
- Gold ↑

### 60/40 Portfolio Correlation Assumptions
- Historical Stock/Bond Correlation: -0.2 to -0.3 (varies by regime)
- When correlation turns positive → Diversification breaks down
- Post-2020: More frequent positive correlations in inflationary regimes

---

## Quick Reference Formulas

### Returns & Compounding
```
Compound Annual Growth Rate (CAGR) = (End/Start)^(1/Years) - 1
Continuously Compounded Return = ln(P1/P0)
```

### Bond Math
```
Yield to Maturity (approximate) = (Coupon + (Face - Price)/Years) / ((Face + Price)/2)
```

### Option Greeks Reference
- **Delta**: Rate of change of option price vs underlying
- **Gamma**: Rate of change of delta
- **Theta**: Time decay per day
- **Vega**: Sensitivity to volatility changes
