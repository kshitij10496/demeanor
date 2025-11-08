import os
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats as st
import yfinance as yf

# Map index ticker to corresponding symbols used by Yahoo Finance.
TICKERS = {
    # Dow Jones Industrial Average
    "DJIA": "^DJI",
    # S&P 500
    "SP500": "^GSPC",
    # NASDAQ Composite
    "NASDAQ": "^IXIC",
    # NIFTY 50
    "NIFTY50": "^NSEI",
}


def fetch_historical_price_data(ticker, period="max"):
    """Fetches the daily closing value for the provided ticker.
    Default period is "max", which goes as far back in history as supported by Yahoo Finance.

    Add caching mechanism to avoid redundant API calls.
    We store the fetched data in a CSV file for future use.
    """
    if os.path.exists(f"data/{ticker}-{period}.csv"):
        df = pd.read_csv(f"data/{ticker}-{period}.csv", index_col=0, parse_dates=True)
    else:
        data = yf.Ticker(ticker)
        df = data.history(period=period)

        # Save the fetched data to a CSV file for future use.
        os.makedirs("data", exist_ok=True)
        df.to_csv(f"data/{ticker}-{period}.csv")

    return df[["Close"]].copy()


def compute_daily_price_change(df):
    """Subtract each day's log from that of the day following to get the magnitude of the daily price changes."""

    # math.log() function cannot be applied to Pandas Series directly.
    # Thus, we use numpy's log function to compute the natural logarithm of the closing prices.
    df["Delta"] = np.log(df["Close"]) - np.log(df["Close"].shift(1))
    return df


def z_score(s):
    """Computes the z-score of a Gaussian random variable."""
    return (s - s.mean()) / s.std()


def plot_z_scores(df, ticker_name):
    """Plots z-scores over time with reference lines for standard deviations."""
    plt.figure(figsize=(14, 7))

    # Plot z-scores
    plt.plot(df.index, df["Z-Score"], linewidth=0.5, alpha=0.7, label="Z-Score")

    # Add reference lines for standard deviations
    plt.axhline(
        y=0, color="black", linestyle="-", linewidth=0.8, alpha=0.5, label="Mean"
    )
    plt.axhline(
        y=1, color="green", linestyle="--", linewidth=0.8, alpha=0.5, label="±1σ (68%)"
    )
    plt.axhline(y=-1, color="green", linestyle="--", linewidth=0.8, alpha=0.5)
    plt.axhline(
        y=2, color="orange", linestyle="--", linewidth=0.8, alpha=0.5, label="±2σ (95%)"
    )
    plt.axhline(y=-2, color="orange", linestyle="--", linewidth=0.8, alpha=0.5)
    plt.axhline(
        y=3, color="red", linestyle="--", linewidth=0.8, alpha=0.5, label="±3σ (99.7%)"
    )
    plt.axhline(y=-3, color="red", linestyle="--", linewidth=0.8, alpha=0.5)

    plt.title(
        f"Z-Scores of Daily Log Returns - {ticker_name}", fontsize=14, fontweight="bold"
    )
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Z-Score (Standard Deviations)", fontsize=12)
    plt.legend(loc="best")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Save the plot
    fname = f"output/{ticker_name}/{time.strftime('%Y-%m-%d')}_z_scores.png"
    os.makedirs(os.path.dirname(fname), exist_ok=True)
    plt.savefig(fname, dpi=250)
    plt.close()
    print(f"Plot saved: {fname}")


def compute_distribution_stats(z_scores, ticker_name):
    """Compares observed z-score distribution against theoretical standard normal distribution."""
    total_days = len(z_scores)

    print(f"\n{'-' * 60}")
    print(f"Distribution Analysis: {ticker_name}")
    print(f"{'-' * 60}")
    print(f"Total days: {total_days}\n")

    # Define thresholds we are interested in.
    # Each threshold represents the number of standard deviations away from the mean.
    thresholds = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    print(
        f"{'Threshold':<12} {'Observed':<20} {'Expected (Normal)':<20} {'Difference':<15}"
    )
    print(f"{'-' * 70}")

    for threshold in thresholds:
        # Observed counts
        observed_count = (z_scores.abs() > threshold).sum()
        observed_pct = (observed_count / total_days) * 100

        # Expected probability from standard normal distribution
        # P(|Z| > threshold) = 2 * (1 - CDF(threshold))
        expected_prob = 2 * (1 - st.norm.cdf(threshold))
        expected_count = expected_prob * total_days
        expected_pct = expected_prob * 100

        # Difference
        diff_count = observed_count - expected_count
        diff_pct = observed_pct - expected_pct

        print(
            f"|Z| > {threshold}σ    {observed_count:>5} ({observed_pct:>5.2f}%)     "
            f"{expected_count:>5.1f} ({expected_pct:>5.2f}%)      "
            f"{diff_count:>+6.1f} ({diff_pct:>+5.2f}%)"
        )

    print(f"{'-' * 70}\n")


def main():
    for ticker, symbol in TICKERS.items():
        print(f"\n{'=' * 60}")
        print(f"Processing: {ticker}")
        print(f"{'=' * 60}")

        # Fetch historical price data.
        df = fetch_historical_price_data(symbol, period="max")

        # Compute daily price change using the closing price.
        df = compute_daily_price_change(df)

        # Remove NaN values before computing z-scores.
        df = df.dropna()

        # Compute z-scores.
        df["Z-Score"] = z_score(df["Delta"])

        # Save results to CSV
        output_file = f"output/{ticker}/{time.strftime('%Y-%m-%d')}_analysis.csv"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        df.to_csv(output_file)

        # Generate and save plot
        plot_z_scores(df, ticker)

        # Show some basic stats
        print(f"\nBasic Statistics for {ticker}:")
        print(f"  Data points: {len(df)}")
        print(
            f"  Date range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}"
        )

        # Compute and display distribution statistics
        compute_distribution_stats(df["Z-Score"], ticker)


if __name__ == "__main__":
    main()
