# Rejected Criteria & Assumptions

During the requirements analysis phase, several acceptance criteria provided in the prompt were identified as mathematically invalid, non-compliant with standard clearing network rules, or incompatible with an append-only ledger architecture. These criteria were explicitly rejected.

### 1. REJECTED: "E7 causes exactly one overdraft fee to be assessed, on Day 2."
* **Reason for Rejection:** Backdated events cascade through time. E7 was effective Day 2, meaning it retroactively overdrew the account for Day 2, Day 4, and Day 5. Therefore, it triggers **three** overdraft fees (AED 75.00 total). Furthermore, the fees cannot be booked "on Day 2"; they must be booked on the assessment day (Day 5) to prevent altering closed historical reporting periods.

### 2. REJECTED: "Any settlement referencing an authorization ID not present in the ledger must be rejected and the funds must not leave the account."
* **Reason for Rejection:** This violates standard card network clearing rules (e.g., Visa/Mastercard). A settlement without a prior authorization (like `Auth-Z` on Day 4) is known as an "Orphaned Settlement" or a "Force-Post." A core ledger must accept this as a direct debit against the ledger balance. Rejecting it would result in the bank absorbing the customer's legitimate debt. 

### 3. REJECTED: "After E9, all balances and fees return to their pre-E7 values."
* **Reason for Rejection:** This violates the fundamental law of an immutable, Event-Sourced ledger. History cannot be erased. Event 9 is an append-only reversal. While it mathematically restores the ledger balance moving forward, the overdraft fees assessed on Day 5 were valid based on the system state at that time. Reversals do not magically delete historical penalty fees; those fees remain on the ledger unless a separate fee-reversal event is explicitly authorized.

### 4. REJECTED: "The three BHD instalments in E10 must each be BHD 3.334."
* **Reason for Rejection:** Basic arithmetic. `3.334 + 3.334 + 3.334 = 10.002`. If we accept this criterion, the ledger is literally fabricating `0.002` BHD out of thin air. To strictly equal 10.000, the splits must be handled dynamically, yielding `3.334`, `3.333`, and `3.333`.

### 5. REJECTED: "If the rounded daily interest accruals do not sum to the capitalized total, the remainder is discarded."
* **Reason for Rejection:** Financial ledgers cannot "discard" remainders or fractions of a penny. To ensure the Conservation of Funds, the daily accrual must be quantized (rounded using Banker's Rounding) *first*, and then those exact quantized values are summed. This guarantees that the sum of the daily calculations matches the capitalized total to the exact decimal without any discarded remainder.