# Number and Math Justifications

## Day 5: The Time-Travel Overdraft Scenario
On Day 5, a late-arriving debit of AED 620.00 (E7) was processed with a `value_date` of Day 2. 
When the End of Day (EOD) engine ran on Day 5, it re-evaluated historical balances:
* **Day 2 Historical Balance:** Originally 250.00. With E7 applied, it became `-370.00`. (Triggers Fee 1)
* **Day 3 Historical Balance:** Originally 650.00. With E7 applied, it became `30.00`. (No Fee)
* **Day 4 Historical Balance:** Originally 285.00. With E7 applied, it became `-335.00`. (Triggers Fee 2)
* **Day 5 Balance:** The closing balance for Day 5 evaluated to `-335.00` before fees. (Triggers Fee 3)

The engine correctly generated three AED 25.00 fees on Day 5, resulting in a total fee deduction of AED 75.00. 
**Day 5 Final Ledger Balance:** 285.00 (Day 4) - 620.00 (E7) - 75.00 (Fees) = **-410.00 AED**.

## Day 5: The Auth Rejection
`Auth-B` (AED 90.00) arrived on Day 5 *after* E7. The Available Balance check accurately replayed the stream up to that moment, factored in E7, and determined the Available Balance was `-335.00`. Because `-335.00 - 90.00 < 0`, the transaction was correctly rejected.

## Day 5: The BHD Precision Split (Event 10)
To credit exactly BHD 10.000 across 3 installments without fractional penny loss, the values were explicitly divided as:
* Split 1: 3.334
* Split 2: 3.333
* Split 3: 3.333
Summing these yields exactly 10.000. Banker's rounding (`ROUND_HALF_EVEN`) to 3 decimal places ensures no precision is lost or hallucinated during subsequent EOD interest calculations.

## Day 6: The Reversal
Event 9 reversed the backdated E7 check. Because the system is append-only, the reversal was posted as a new event rather than deleting E7. 
This restored the ledger balance mathematically (`-410.00 + 620.00 = 210.00`), but left the previously assessed overdraft fees untouched, adhering to immutable ledger principles.