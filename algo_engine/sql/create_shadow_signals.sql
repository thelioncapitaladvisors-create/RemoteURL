-- ====================================================================
-- TLCS Black Box Signal Engine: Shadow Database Schema
-- Table: public.shadow_signals
-- ====================================================================
-- Run this SQL in the Supabase SQL Editor to create the shadow table.
-- Mirrors public.signals schema exactly for parity auditing.

CREATE TABLE IF NOT EXISTS public.shadow_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    signal_ts TIMESTAMPTZ DEFAULT now(),
    symbol TEXT NOT NULL,
    type TEXT NOT NULL,
    entry NUMERIC,
    stop NUMERIC,
    target NUMERIC,
    tp2 NUMERIC,
    tp3 NUMERIC,
    tp4 NUMERIC,
    trail_sl NUMERIC,
    trailing_stop NUMERIC,
    status TEXT NOT NULL DEFAULT 'OPEN',
    outcome TEXT DEFAULT 'OPEN',
    exit_price NUMERIC,
    exit_at TIMESTAMPTZ,
    hold_duration NUMERIC,
    profit NUMERIC,
    rr NUMERIC,
    message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    pricing_type TEXT DEFAULT 'SHADOW',
    source TEXT DEFAULT 'BLACKBOX',
    trigger TEXT DEFAULT 'TradeOpen',
    exchange TEXT,
    dhan_entry_order_id TEXT,
    dhan_exit_order_id TEXT,
    dhan_traded_symbol TEXT
);

-- Indices for rapid querying & parity audit comparison
CREATE INDEX IF NOT EXISTS idx_shadow_signals_symbol ON public.shadow_signals (symbol);
CREATE INDEX IF NOT EXISTS idx_shadow_signals_created_at ON public.shadow_signals (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_shadow_signals_status ON public.shadow_signals (status);
CREATE INDEX IF NOT EXISTS idx_shadow_signals_outcome ON public.shadow_signals (outcome);
CREATE INDEX IF NOT EXISTS idx_shadow_signals_source ON public.shadow_signals (source);

-- Enable Row Level Security (RLS)
ALTER TABLE public.shadow_signals ENABLE ROW LEVEL SECURITY;

-- Allow public / anon read access for mobile app and web dashboard parity audit
CREATE POLICY "Allow public read on shadow_signals"
    ON public.shadow_signals
    FOR SELECT
    TO public
    USING (true);

-- Allow authenticated and service_role full write access
CREATE POLICY "Allow service_role insert on shadow_signals"
    ON public.shadow_signals
    FOR INSERT
    TO service_role
    WITH CHECK (true);

CREATE POLICY "Allow service_role update on shadow_signals"
    ON public.shadow_signals
    FOR UPDATE
    TO service_role
    USING (true);

CREATE POLICY "Allow service_role delete on shadow_signals"
    ON public.shadow_signals
    FOR DELETE
    TO service_role
    USING (true);
