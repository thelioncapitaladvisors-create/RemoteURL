---
name: vectorbt
description: Provides documentation and context for VectorBT, a high-performance Python backtesting library. Activate this skill when asked to backtest trading algorithms, run parameter sweeps, or optimize trading strategies in Python.
---

# VectorBT Backtesting Skill

This skill contains the official `vectorbt` GitHub repository. VectorBT is an open-source Python library designed to analyze trading strategies at scale using pandas, NumPy, and Numba.

## Contents
The official vectorbt repository has been cloned into the `resources/` directory.
You can read through `resources/README.md` or look at `resources/examples/` for usage patterns on how to structure a vectorized backtest.

## Usage
When the user asks to backtest a strategy:
1. `vectorbt` operates on pandas DataFrames and Series. It represents trading data as multidimensional arrays.
2. Standard installation: `pip install vectorbt`
3. Basic usage pattern:
   ```python
   import vectorbt as vbt

   # Fetch data
   price = vbt.YFData.download("AAPL").get("Close")

   # Calculate moving averages
   fast_ma = vbt.MA.run(price, 10)
   slow_ma = vbt.MA.run(price, 50)

   # Generate crossover signals
   entries = fast_ma.ma_crossed_above(slow_ma)
   exits = fast_ma.ma_crossed_below(slow_ma)

   # Run backtest
   portfolio = vbt.Portfolio.from_signals(price, entries, exits, init_cash=10000)

   # View metrics
   print(portfolio.stats())
   ```
4. For parameter optimization, `vectorbt` can run multiple windows (e.g. `fast_window=[10, 20]`) simultaneously due to its vectorized nature.
