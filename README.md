# In-Memory Core Ledger Engine

## Overview
This repository contains a robust, in-memory core banking ledger built in Python. The system strictly follows Event Sourcing principles to manage account balances, enforce currency-specific precision using Banker's Rounding, and handle complex temporal scenarios like backdated transactions and orphaned settlements.

## Architectural Principles
1. **Append-Only Event Sourcing:** There are no mutable `current_balance` variables. The state of any account at any point in time is derived purely by folding the immutable event stream.
2. **Temporal Decoupling:** The system distinguishes between `system_day` (when an event is processed) and `value_date` (the historical economic effective date). This allows the engine to accurately reconstruct past states without destroying the chronological audit trail.
3. **Strict Precision:** Floating-point math is strictly forbidden. All monetary values are handled using Python's `Decimal` library. Banker's Rounding (`ROUND_HALF_EVEN`) is globally enforced to specific account tolerances (e.g., AED to 2 decimal places, BHD to 3).

## Key Features
* **Available Balance Engine:** Dynamically calculates liquidity by subtracting active network holds (`AUTH`) from the cleared ledger balance.
* **Orphaned Settlement Handling:** Automatically processes force-posted settlements (where no prior authorization exists) without crashing or corrupting the hold state.
* **Time-Traveling Overdraft Assessment:** An End-of-Day (EOD) batch job that re-evaluates historical daily closing balances. If a late-arriving backdated debit retroactively overdraws an account, the system generates fees today for the historical infractions, ensuring idempotency so days are never double-charged.
* **Auditable Statement Generator:** Derives clean, human-readable account statements that strip out pending holds and chronologically order posted transactions by processing date.

## Sample Account Statement (ACC-001)
The engine generates a chronological audit trail of posted transactions, strictly separating system processing days (`Post Day`) from economic effective dates (`Val Day`) while excluding pending authorization holds:

```text
========================= OFFICIAL ACCOUNT STATEMENT =========================
Account Number: ACC-001
Statement Period: Day 1 to Day 6
--------------------------------------------------------------------------------------------
Post Day   | Val Day   | Ref ID     | Description                      | Amount     | Balance   
--------------------------------------------------------------------------------------------
Day 1      | Day 1     | E1         | Initial Deposit                  | +1200.00   | 1200.00   
Day 1      | Day 1     | E2         | Rent Payment                     | -950.00    | 250.00    
Day 3      | Day 3     | E4         | Salary Deposit                   | +400.00    | 650.00    
Day 4      | Day 4     | Auth-A     | Hotel Checkout Settlement        | -185.00    | 465.00    
Day 4      | Day 4     | Auth-Z     | Orphaned Force-Post Settlement   | -180.00    | 285.00    
Day 5      | Day 2     | E7         | Backdated Check Clearing         | -620.00    | -335.00   
Day 5      | Day 5     | OD-FEE-D2  | Retroactive OD Fee for Day 2     | -25.00     | -360.00   
Day 5      | Day 5     | OD-FEE-D4  | Retroactive OD Fee for Day 4     | -25.00     | -385.00   
Day 5      | Day 5     | OD-FEE-D5  | Retroactive OD Fee for Day 5     | -25.00     | -410.00   
Day 6      | Day 2     | E9         | Reversal of Backdated Check      | +620.00    | 210.00    
Day 6      | Day 6     | INT-CAP    | End of Window Interest Capitaliz | +0.73      | 210.73    
--------------------------------------------------------------------------------------------
ENDING CLEARED BALANCE: 210.73 ACC
==============================================================================

## Execution
Run the `ledger.py` script to execute the 6-day stream simulation and print the daily reporting metrics.