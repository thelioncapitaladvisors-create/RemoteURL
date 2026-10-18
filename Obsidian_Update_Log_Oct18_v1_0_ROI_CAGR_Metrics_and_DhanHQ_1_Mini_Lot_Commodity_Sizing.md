# Platform Update Log: Version 1.0 ROI/CAGR Metrics & DhanHQ 1 Mini Lot Commodity Sizing
**Date**: October 18, 2026  
**Module**: Mobile Terminal Paper Portfolio Simulator (`SCREENER` tab / `page.tsx`)  
**Scope**: 
1. Added Return on Investment (ROI) and Annualized CAGR metrics across the 8-metric KPI grid and equity curve readouts.
2. Standardized default commodity position sizing to 1 Mini Lot as available on DhanHQ.

### Changes Summary:
1. **DhanHQ 1 Mini Lot Commodity Sizing**:
   - `DEFAULT_LOT_CONFIG['mcx']` and `DHAN_DEFAULT_LOT_CONFIG['mcx']`: Configured `size: 10`, `symbolLabel: 'MCX COMMODITIES (1 Mini Lot)'`.
   - `paperSimulatedTrades` & `dhanPaperSimulatedTrades`: Mapped all commodity symbols to DhanHQ retail mini lot contracts:
     - `GOLD` / `GOLDM`: `10 Qty` (100g, 1 pt = ₹10)
     - `GOLDPETAL`: `1 Qty` (1g, 1 pt = ₹1)
     - `SILVER` / `SILVERM`: `5 Qty` (5kg, 1 pt = ₹5)
     - `SILVERMIC`: `1 Qty` (1kg, 1 pt = ₹1)
     - `CRUDEOIL` / `CRUDEOILM`: `10 Qty` (10 bbl, 1 pt = ₹10)
     - `NATURALGAS` / `NATURALGASM`: `250 Qty` (250 mmBtu, 1 pt = ₹250)
     - `ALUMINI` / `ALUMINIUM`: `1000 Qty` (1 MT, 1 pt = ₹1000)
     - `ZINCM` / `ZINC`: `1000 Qty` (1 MT, 1 pt = ₹1000)
     - `LEADMINI` / `LEAD`: `1000 Qty` (1 MT, 1 pt = ₹1000)
     - `COPPER`: `2500 Qty` (2.5 MT, 1 pt = ₹2500)
   - Updated Contract Quantity card UI to reflect `1 Mini Lot (GoldM: 10 | CrudeM: 10)` and `MCX 1 Mini Lot: GoldM=10 | CrudeM=10 | SilverM=5 | NGM=250`.

2. **ROI & Annualized CAGR Integration**:
   - Expanded KPI summary grid from 6 to 8 cards across `TLCS_PAPER` and `DHAN_PAPER`.
   - Annualized CAGR computed via `((Balance / Capital) ** (52 / Weeks) - 1) * 100`.
   - Dynamic trending arrows and color coding for gains (`text-emerald-500`) vs losses (`text-rose-500`).
   - Added CAGR badge to equity curve header and inspection readout bar.

3. **Rules & Documentation**:
   - Codified in `AGENTS.md` and `.agents/AGENTS.md`.
   - Created Obsidian note `Obsidian/45_Platform_v1_0_ROI_CAGR_Metrics_and_DhanHQ_1_Mini_Lot_Commodity_Sizing.md`.
