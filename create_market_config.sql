
CREATE TABLE IF NOT EXISTS public.market_config (
    market_id text PRIMARY KEY,
    symbols jsonb NOT NULL DEFAULT '[]'::jsonb,
    updated_at timestamp with time zone DEFAULT timezone('utc'::text, now())
);
ALTER TABLE public.market_config ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable read access for all users" ON public.market_config FOR SELECT USING (true);
