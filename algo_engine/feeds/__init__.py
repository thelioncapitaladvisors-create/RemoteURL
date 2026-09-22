"""
algo_engine.feeds — Real-Time Market Data Ingestion Layer
=========================================================

Exports:
    BaseFeed, FeedStatus, Tick
    CandleAggregator
    DhanFeed
    BinanceFeed
    GlobalFeed
    FeedManager, normalize_symbol, get_market_category
"""

from .base_feed import BaseFeed, FeedStatus, Tick
from .aggregator import CandleAggregator
from .dhan_feed import DhanFeed
from .binance_feed import BinanceFeed
from .global_feed import GlobalFeed
from .feed_manager import FeedManager, normalize_symbol, get_market_category, is_market_open
from .bootstrapper import HistoricalBootstrapper

__all__ = [
    "BaseFeed",
    "FeedStatus",
    "Tick",
    "CandleAggregator",
    "DhanFeed",
    "BinanceFeed",
    "GlobalFeed",
    "FeedManager",
    "normalize_symbol",
    "get_market_category",
    "is_market_open",
    "HistoricalBootstrapper",
]
