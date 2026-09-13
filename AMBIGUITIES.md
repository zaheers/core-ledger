# Handled Ambiguities

While building the core ledger, several edge cases were identified that the business requirements did not explicitly address. Here is how the engine resolves them:

1. **Overdraft Fee Currency Support:** 
   * *Ambiguity:* The prompt dictates an AED 25.00 overdraft fee but does not specify how to charge this against the BHD account (ACC-002) if it goes negative.
   * *Resolution:* Building an FX (Foreign Exchange) translation layer to convert a 25.00 AED fee into BHD was deemed out-of-scope for an in-memory prototype. I explicitly bypassed `ACC-002` in the overdraft fee loop to prevent crashing the system with mismatched currency arithmetic.

2. **Hold Expirations:**
   * *Ambiguity:* How long does an `AUTH` live if a `SETTLE` never arrives?
   * *Resolution:* For this 6-day window, holds are assumed to be indefinite. In a production environment, a cron job or scheduled task would be required to automatically drop `AUTH` events that have aged past the network threshold (e.g., 7 days for standard retail).

3. **Settlement Amounts vs. Auth Amounts:**
   * *Ambiguity:* `Auth-A` was for 200.00, but the `SETTLE` was for 185.00. 
   * *Resolution:* The ledger explicitly zeroes out the *entire* hold amount associated with the `ref_id` the moment the settlement arrives, regardless of whether the settlement amount is higher or lower than the original auth.