-- ====================================================================
-- TLCS Black Box Signal Engine: Autonomous Zero-Blueprint Shield
-- File: algo_engine/sql/block_non_canonical_triggers.sql
-- ====================================================================
-- Prevents insertion of Day Type Blueprints or Trade Sequences as
-- standalone trade alerts, enforcing strictly the 12 Canonical Strategy Triggers.

CREATE OR REPLACE FUNCTION trg_enforce_canonical_shadow_triggers()
RETURNS TRIGGER AS $$
DECLARE
    clean_type TEXT;
BEGIN
    clean_type := UPPER(TRIM(NEW.type));

    -- Strip leading BUY / SELL prefixes if present
    IF clean_type LIKE 'BUY %' THEN
        clean_type := SUBSTRING(clean_type FROM 5);
    ELSIF clean_type LIKE 'SELL %' THEN
        clean_type := SUBSTRING(clean_type FROM 6);
    END IF;

    -- Strict Rejection of Day Type Blueprints and Trade Sequences
    IF clean_type LIKE '%BLUEPRINT%' OR clean_type LIKE '%SEQUENCE%' THEN
        RAISE EXCEPTION 'Non-canonical execution rejected: % is a market regime context, not a valid trade trigger.', NEW.type;
    END IF;

    -- Enforce 12 Canonical Triggers
    IF clean_type NOT IN (
        'LONG MISSILE', 'SHORT MISSILE',
        'LONG LIGHTNING', 'SHORT LIGHTNING',
        'LONG SCALP', 'SHORT SCALP',
        'LONG DIVERGENCE', 'SHORT DIVERGENCE',
        'LONG HIDDEN DIVERGENCE', 'SHORT HIDDEN DIVERGENCE',
        'LONG EXTREME REVERSAL', 'SHORT EXTREME REVERSAL'
    ) THEN
        RAISE EXCEPTION 'Non-canonical execution rejected: % does not match any of the 12 Canonical Strategy Archetypes.', NEW.type;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_block_non_canonical_shadow_signals ON public.shadow_signals;

CREATE TRIGGER trg_block_non_canonical_shadow_signals
    BEFORE INSERT OR UPDATE ON public.shadow_signals
    FOR EACH ROW
    EXECUTE FUNCTION trg_enforce_canonical_shadow_triggers();
