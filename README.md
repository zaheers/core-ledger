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

## Execution
Run the `ledger.py` script to execute the 6-day stream simulation and print the daily reporting metrics.