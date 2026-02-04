#!/usr/bin/env python3
"""
Economic Data Analyzer Script
Part of the macro-finance-analyst skill

This script provides utilities for analyzing economic data and generating
formatted reports for macro-economic analysis.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple


def calculate_yoy_change(current: float, prior_year: float) -> float:
    """Calculate year-over-year percentage change."""
    if prior_year == 0:
        return 0.0
    return ((current - prior_year) / prior_year) * 100


def calculate_mom_change(current: float, prior_month: float) -> float:
    """Calculate month-over-month percentage change."""
    if prior_month == 0:
        return 0.0
    return ((current - prior_month) / prior_month) * 100


def calculate_annualized_change(current: float, prior: float, periods_per_year: int = 12) -> float:
    """Calculate annualized change from periodic data."""
    if prior == 0:
        return 0.0
    periodic_change = current / prior
    return (periodic_change ** periods_per_year - 1) * 100


def taylor_rule(
    inflation: float,
    output_gap: float,
    neutral_real_rate: float = 2.0,
    inflation_target: float = 2.0,
    inflation_weight: float = 0.5,
    output_weight: float = 0.5
) -> float:
    """
    Calculate the Taylor Rule implied Fed Funds Rate.
    
    Args:
        inflation: Current inflation rate (%)
        output_gap: Output gap as percentage of potential GDP
        neutral_real_rate: Assumed neutral real rate (default 2%)
        inflation_target: Fed's inflation target (default 2%)
        inflation_weight: Weight on inflation deviation (default 0.5)
        output_weight: Weight on output gap (default 0.5)
    
    Returns:
        Implied Fed Funds Rate (%)
    """
    implied_rate = (
        neutral_real_rate +
        inflation +
        inflation_weight * (inflation - inflation_target) +
        output_weight * output_gap
    )
    return round(implied_rate, 2)


def sahm_rule_indicator(unemployment_history: List[float]) -> Tuple[float, bool]:
    """
    Calculate the Sahm Rule recession indicator.
    
    Args:
        unemployment_history: List of monthly unemployment rates (most recent last)
                            Need at least 15 months of data
    
    Returns:
        Tuple of (indicator value, recession signal triggered)
    """
    if len(unemployment_history) < 15:
        raise ValueError("Need at least 15 months of unemployment data")
    
    # Current 3-month average
    current_3m_avg = sum(unemployment_history[-3:]) / 3
    
    # Find minimum of 3-month averages over prior 12 months
    min_3m_avg = float('inf')
    for i in range(3, 15):
        avg = sum(unemployment_history[-(i+3):-i]) / 3
        min_3m_avg = min(min_3m_avg, avg)
    
    indicator = current_3m_avg - min_3m_avg
    recession_signal = indicator >= 0.5
    
    return round(indicator, 2), recession_signal


def calculate_real_rate(nominal_rate: float, inflation_expectation: float) -> float:
    """Calculate real interest rate (Fisher equation approximation)."""
    return round(nominal_rate - inflation_expectation, 2)


def calculate_breakeven_inflation(nominal_yield: float, tips_yield: float) -> float:
    """Calculate breakeven inflation from nominal and TIPS yields."""
    return round(nominal_yield - tips_yield, 2)


def format_data_comparison(
    indicator_name: str,
    actual: float,
    consensus: float,
    prior: float,
    unit: str = "%"
) -> str:
    """
    Format economic data release comparison.
    
    Returns formatted string comparing actual vs consensus vs prior.
    """
    surprise = actual - consensus
    surprise_str = f"+{surprise:.2f}" if surprise > 0 else f"{surprise:.2f}"
    
    vs_prior = actual - prior
    vs_prior_str = f"+{vs_prior:.2f}" if vs_prior > 0 else f"{vs_prior:.2f}"
    
    result = f"""
## {indicator_name}

| Metric | Value |
|--------|-------|
| **Actual** | {actual:.2f}{unit} |
| Consensus | {consensus:.2f}{unit} |
| Prior | {prior:.2f}{unit} |
| **Surprise** | {surprise_str}{unit} |
| vs Prior | {vs_prior_str}{unit} |
"""
    
    # Add interpretation
    if abs(surprise) < 0.1:
        interpretation = "📊 **In-line with expectations**"
    elif surprise > 0.2:
        interpretation = "📈 **Strong beat - positive surprise**"
    elif surprise > 0:
        interpretation = "📈 **Modest beat**"
    elif surprise < -0.2:
        interpretation = "📉 **Significant miss - negative surprise**"
    else:
        interpretation = "📉 **Modest miss**"
    
    result += f"\n{interpretation}\n"
    
    return result


def generate_scenario_analysis(
    base_case: Dict,
    bull_case: Dict,
    bear_case: Dict
) -> str:
    """
    Generate formatted scenario analysis table.
    
    Each case dict should have: probability, trigger, sp500_impact, rates_impact, usd_impact
    """
    template = f"""
## Scenario Analysis

| Scenario | Probability | Key Trigger | S&P 500 | Rates | USD |
|----------|-------------|-------------|---------|-------|-----|
| 🐂 **Bull** | {bull_case['probability']}% | {bull_case['trigger']} | {bull_case['sp500_impact']} | {bull_case['rates_impact']} | {bull_case['usd_impact']} |
| 📊 **Base** | {base_case['probability']}% | {base_case['trigger']} | {base_case['sp500_impact']} | {base_case['rates_impact']} | {base_case['usd_impact']} |
| 🐻 **Bear** | {bear_case['probability']}% | {bear_case['trigger']} | {bear_case['sp500_impact']} | {bear_case['rates_impact']} | {bear_case['usd_impact']} |
"""
    return template


def fed_funds_futures_implied_rate(futures_price: float) -> float:
    """Convert Fed Funds Futures price to implied rate."""
    return round(100 - futures_price, 3)


def calculate_forward_rate(
    spot_rate_short: float,
    spot_rate_long: float,
    short_maturity: float,
    long_maturity: float
) -> float:
    """
    Calculate implied forward rate from spot rates.
    
    Args:
        spot_rate_short: Spot rate for shorter maturity (%)
        spot_rate_long: Spot rate for longer maturity (%)
        short_maturity: Shorter maturity in years
        long_maturity: Longer maturity in years
    
    Returns:
        Implied forward rate (%)
    """
    # Using continuous compounding approximation
    forward_rate = (
        (spot_rate_long * long_maturity - spot_rate_short * short_maturity) /
        (long_maturity - short_maturity)
    )
    return round(forward_rate, 2)


def generate_research_note_template(
    title: str,
    date: str,
    thesis: str,
    conviction: str = "Medium"
) -> str:
    """Generate a research note template."""
    template = f"""
# {title} | {date}

## Executive Summary
- [Key point 1]
- [Key point 2]
- [Key point 3]

## Investment Thesis
{thesis}

## Key Arguments

### 1. [Argument Title]
[Supporting data and analysis]

### 2. [Argument Title]
[Supporting data and analysis]

### 3. [Argument Title]
[Supporting data and analysis]

## Risks to View
| Risk | Probability | Impact |
|------|-------------|--------|
| [Risk 1] | [Low/Med/High] | [Low/Med/High] |
| [Risk 2] | [Low/Med/High] | [Low/Med/High] |

## Trade Expression
| Position | Entry | Target | Stop | Risk/Reward |
|----------|-------|--------|------|-------------|
| [Trade] | [X] | [Y] | [Z] | [R:R] |

## Conviction Level: {conviction}

---
*This analysis is for informational purposes only and does not constitute investment advice.*
"""
    return template


if __name__ == "__main__":
    # Example usage
    print("=== Taylor Rule Example ===")
    implied_rate = taylor_rule(
        inflation=2.8,
        output_gap=0.5,
        neutral_real_rate=2.0,
        inflation_target=2.0
    )
    print(f"Implied Fed Funds Rate: {implied_rate}%")
    
    print("\n=== Data Comparison Example ===")
    comparison = format_data_comparison(
        indicator_name="Core CPI MoM",
        actual=0.4,
        consensus=0.3,
        prior=0.3,
        unit="%"
    )
    print(comparison)
    
    print("\n=== Scenario Analysis Example ===")
    scenarios = generate_scenario_analysis(
        base_case={
            'probability': 50,
            'trigger': 'Soft landing achieved',
            'sp500_impact': '+8-12%',
            'rates_impact': '-50bps',
            'usd_impact': 'Stable'
        },
        bull_case={
            'probability': 25,
            'trigger': 'Productivity boom + rate cuts',
            'sp500_impact': '+15-20%',
            'rates_impact': '-100bps',
            'usd_impact': '-5%'
        },
        bear_case={
            'probability': 25,
            'trigger': 'Sticky inflation + recession',
            'sp500_impact': '-15-20%',
            'rates_impact': '+50bps then cuts',
            'usd_impact': '+5%'
        }
    )
    print(scenarios)
