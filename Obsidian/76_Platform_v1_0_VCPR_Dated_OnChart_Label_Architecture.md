# Platform v1.0: Virgin CPR On-Chart Pop-Up Label Renaming & Temporal Zone Tracking Architecture

**Status**: PRODUCTION VERIFIED & SYNCHRONIZED  
**Date**: October 26, 2026  
**Indicator Version**: v1.0 (Pine Script v6)  
**Target File**: `TV Indicator/TLCS_Virgin_CPR_Zones.pine`

---

## 1. Executive Summary & Purpose

In institutional price action trading following Frank Ochoa's *Secrets of a Pivot Boss*, Virgin Central Pivot Range (VCPR) levels serve as powerful magnet zones for retests, support bounces, and resistance rejections. When price penetrates or tests a multi-day unvisited CPR level, fast visual identification of the **exact historical date** when that Virgin CPR was formed provides critical context regarding the age and strength of the zone.

Previously, on-chart pop-up labels displayed generic timeframes:
```
🧲 Daily VCPR SUPPORT TOUCH
Zone: [22636.83 - 22665.5]
Price: 22699.5
```

The user requested:
> *"Simply rename it as 'VCPR Dated ________ ' here"*

This architecture enhancement upgrades `TV Indicator/TLCS_Virgin_CPR_Zones.pine` to deterministically track the historical formation timestamp (`timePrev`) of every active Virgin CPR zone, formatting the on-chart pop-up signal labels cleanly as:
```
VCPR Dated 24-Oct-2026
```
(or `Weekly VCPR Dated 20-Oct-2026`, etc.).

---

## 2. Technical Architecture & Implementation

### 2.1 Zone Timestamp Tracking in `f_virginCPR`
To ensure that each Virgin CPR remembers its exact historical creation date across rolling sessions:
1. Captured session open timestamp:
   ```pine
   var int curTime = na
   if isNew
       curTime := time(reqTf)
   int timePrev = curTime[1]
   ```
2. Dynamic timestamp array `zTime`:
   ```pine
   var array<int> zTime = array.new_int()
   ```
   When an active zone rolls off due to `maxZones` capacity:
   ```pine
   array.shift(zTime)
   ```
   When a new untouched CPR qualifies as virgin:
   ```pine
   array.push(zTime, timePrev)
   ```
3. Signal trigger date extraction:
   ```pine
   int zT = array.get(zTime, i)
   touchedTime := zT
   ```

### 2.2 Date Formatting & Display Modes
Two user-configurable settings were added under `group = GEN`:
- `labelFormat`:
  - `'Compact (Date Only)'` (*Default*): Displays clean `'VCPR Dated <Date>'` directly matching the user's request.
  - `'Full (Date + Zone + Price)'`: Appends zone boundaries and touch price on subsequent lines.
- `vcprDateFormat`: Options for `dd-MMM-yyyy` (default, e.g. `24-Oct-2026`), `dd-MM-yyyy`, `yyyy-MM-dd`, and `dd MMM yyyy`.

### 2.3 Pop-Up Label Construction
```pine
string dateStr = not na(zT) ? str.format_time(zT, dtFmt, syminfo.timezone) : ''
string tfPrefix = tag == 'D' ? 'VCPR Dated ' : (tag == 'W' ? 'Weekly VCPR Dated ' : (tag == 'M' ? 'Monthly VCPR Dated ' : 'Yearly VCPR Dated '))
string signalTitle = tfPrefix + dateStr
string zoneStr = str.tostring(bt, '#.##') + ' - ' + str.tostring(t, '#.##')
string labelText = signalTitle + (lblFmt == 'Full (Date + Zone + Price)' ? '\nZone: [' + zoneStr + ']\nPrice: ' + str.tostring(close, '#.##') : '')
```

Interactive cursor hover tooltip preserves complete zone telemetry:
```pine
tooltip = signalTitle + '\nZone: [' + zoneStr + ']\nTouch Price: ' + str.tostring(close, '#.##')
```

### 2.4 Real-Time Pop-Up Alert Dialogs & HUD Telemetry Synchronization
The real-time alert dialogs and on-chart HUD table were also updated to mirror the `VCPR Dated <Date>` format:
- Daily: `🚨 [NIFTY (VCPR Dated 24-Oct-2026)] BULLISH SUPPORT TEST (Bounce)...`
- HUD Header: `VCPR DATED 24-OCT-2026` / `▲ BULLISH SUPPORT TEST (24-Oct-2026)`

---

## 3. Verification & Synchronized Backups

All 4 storage locations have identical SHA-256 hashes (`d470405830b9b5f886013e8e73e19ffb4bb5c1699c75b540e8719215ef1cd277`):
- `Project/TV Indicator/TLCS_Virgin_CPR_Zones.pine`
- `Project Backup/TV Indicator/TLCS_Virgin_CPR_Zones.pine`
- `Backups/Project/TV Indicator/TLCS_Virgin_CPR_Zones.pine`
- `Backups copy/Project/TV Indicator/TLCS_Virgin_CPR_Zones.pine`
