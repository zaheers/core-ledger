import decimal
from decimal import Decimal
from dataclasses import dataclass
from typing import Optional

# Globally enforce Banker's Rounding for all financial calculations
decimal.getcontext().rounding = decimal.ROUND_HALF_EVEN

# ==========================================
# 1. THE DATA MODEL
# ==========================================
@dataclass(frozen=True)
class Event:
    system_day: int
    value_date: int
    type: str
    account_id: str
    amount: Decimal
    ref_id: Optional[str] = None
    description: str = ""  # Added to document the business reason for the event

# ==========================================
# 2. THE LEDGER CORE
# ==========================================
class Ledger:
    def __init__(self):
        self.event_stream = []
        self.assessed_overdraft_fees = set()
        self.daily_errors = []
        self.accounts = {
            'ACC-001': 2,  # AED (2 decimal places)
            'ACC-002': 3   # BHD (3 decimal places)
        }

    def _quantize(self, amount: Decimal, account_id: str) -> Decimal:
        """Forces Banker's Rounding to the strict precision of the target currency."""
        precision = self.accounts[account_id]
        quantizer = Decimal('10') ** -precision 
        return amount.quantize(quantizer)

    def get_ledger_balance(self, account_id: str, current_system_day: int, target_value_date: int) -> Decimal:
        """Derives the cleared balance by replaying history up to the target_value_date."""
        balance = Decimal('0')
        for event in self.event_stream:
            # Only apply events we know about TODAY, but that are economically effective ON/BEFORE the target date
            if (event.account_id == account_id and 
                event.system_day <= current_system_day and 
                event.value_date <= target_value_date):
                
                if event.type in ('CREDIT', 'INTEREST', 'REVERSAL'):
                    balance += event.amount
                elif event.type in ('DEBIT', 'SETTLE', 'FEE'):
                    balance -= event.amount
                    
        return self._quantize(balance, account_id)

    def get_active_holds(self, account_id: str, current_system_day: int) -> Decimal:
        """Sums up money currently frozen by network authorizations."""
        holds = {}
        for event in self.event_stream:
            if event.account_id == account_id and event.system_day <= current_system_day:
                if event.type == 'AUTH':
                    holds[event.ref_id] = event.amount
                elif event.type == 'SETTLE' and event.ref_id in holds:
                    # Release the hold once the final settlement arrives
                    holds[event.ref_id] = Decimal('0')
                    
        total_holds = Decimal(sum(holds.values()))
        return self._quantize(total_holds, account_id)

    def get_available_balance(self, account_id: str, current_system_day: int) -> Decimal:
        """Ledger Balance minus Active Holds. This is the customer's actual spending power."""
        ledger_bal = self.get_ledger_balance(account_id, current_system_day, current_system_day)
        active_holds = self.get_active_holds(account_id, current_system_day)
        return ledger_bal - active_holds

    def post(self, event):
        """Validates network holds and appends events to the immutable log."""
        if event.type == 'AUTH':
            avail_bal = self.get_available_balance(event.account_id, event.system_day)
            # Strict validation: Do not allow an authorization if funds are insufficient
            if avail_bal - event.amount < Decimal('0'):
                self.daily_errors.append(
                    f"Day {event.system_day}: Auth {event.ref_id} REJECTED ({event.description}). Avail Bal: {avail_bal}"
                )
                return 

        # Append-only: History is never overwritten
        self.event_stream.append(event)

    def process_eod(self, current_system_day: int):
        """Runs end-of-day batch jobs: Retroactive Overdraft Fees & Interest Capitalization."""
        # 1. Overdraft Fees (Time-Traveling Logic)
        for account_id in self.accounts:
            if account_id == 'ACC-002': 
                continue # BHD scope bypassed for overdraft fees

            # Look back at every day from Day 1 to the current day
            for d in range(1, current_system_day + 1):
                if (account_id, d) not in self.assessed_overdraft_fees:
                    # Calculate the historical balance using CURRENT knowledge
                    historical_bal = self.get_ledger_balance(account_id, current_system_day, d)
                    
                    if historical_bal < Decimal('0'):
                        fee_event = Event(
                            system_day=current_system_day,
                            value_date=current_system_day,
                            type='FEE',
                            account_id=account_id,
                            amount=Decimal('25.00'),
                            ref_id=f"OD-FEE-D{d}",
                            description=f"Retroactive OD Fee for Day {d}"
                        )
                        self.post(fee_event)
                        # Guarantee idempotency: never charge twice for the same historical day
                        self.assessed_overdraft_fees.add((account_id, d))

        # 2. Interest Capitalization (Executes strictly on Day 6)
        if current_system_day == 6:
            for account_id, precision in self.accounts.items():
                total_interest = Decimal('0')
                
                for d in range(1, 7):
                    bal = self.get_ledger_balance(account_id, 6, d)
                    if bal > Decimal('0'):
                        daily_accrual = bal * Decimal('0.0004')
                        # Round daily accrual to prevent fractional penny generation
                        rounded_daily = self._quantize(daily_accrual, account_id)
                        total_interest += rounded_daily
                
                if total_interest > Decimal('0'):
                    interest_event = Event(
                        system_day=6,
                        value_date=6,
                        type='INTEREST',
                        account_id=account_id,
                        amount=total_interest,
                        ref_id="INT-CAP",
                        description="End of Window Interest Capitalization"
                    )
                    self.post(interest_event)

# ==========================================
# 3. THE EXECUTION SCRIPT
# ==========================================
def run_simulation():
    ledger = Ledger()
    
    # Mapping the exact scenario from the project requirements
    stream = {
        1: [
            Event(1, 1, 'CREDIT', 'ACC-001', Decimal('1200.00'), 'E1', "Initial Deposit"),
            Event(1, 1, 'DEBIT', 'ACC-001', Decimal('950.00'), 'E2', "Rent Payment")
        ],
        2: [
            Event(2, 2, 'AUTH', 'ACC-001', Decimal('200.00'), 'Auth-A', "Hotel Hold")
        ],
        3: [
            Event(3, 3, 'CREDIT', 'ACC-001', Decimal('400.00'), 'E4', "Salary Deposit")
        ],
        4: [
            # Settle A releases Auth-A and deducts 185
            Event(4, 4, 'SETTLE', 'ACC-001', Decimal('185.00'), 'Auth-A', "Hotel Checkout Settlement"),
            # Settle Z has no matching Auth (Orphaned Settlement rule)
            Event(4, 4, 'SETTLE', 'ACC-001', Decimal('180.00'), 'Auth-Z', "Orphaned Force-Post Settlement")
        ],
        5: [
            # TRAP: This debit arrives Day 5 but is economically effective Day 2
            Event(5, 2, 'DEBIT', 'ACC-001', Decimal('620.00'), 'E7', "Backdated Check Clearing"),
            # This Auth will fail because E7 drains the available balance
            Event(5, 5, 'AUTH', 'ACC-001', Decimal('90.00'), 'Auth-B', "Dinner Hold"),
            
            # TRAP: Splitting BHD 10.000 into 3 parts without losing fractions of a fil (Banker's Rounding test)
            Event(5, 5, 'CREDIT', 'ACC-002', Decimal('3.334'), 'E10-1', "BHD Split 1"),
            Event(5, 5, 'CREDIT', 'ACC-002', Decimal('3.333'), 'E10-2', "BHD Split 2"),
            Event(5, 5, 'CREDIT', 'ACC-002', Decimal('3.333'), 'E10-3', "BHD Split 3")
        ],
        6: [
            # Append-only reversal of the backdated check (restores balance, but leaves fees intact)
            Event(6, 2, 'REVERSAL', 'ACC-001', Decimal('620.00'), 'E9', "Reversal of Backdated Check")
        ]
    }
    
    # Process the 6-day window
    for day in range(1, 7):
        print(f"\n{'='*15} END OF SYSTEM DAY {day} {'='*15}")
        
        # 1. Append daily events
        if day in stream:
            for event in stream[day]:
                ledger.post(event)
                
        # 2. Trigger EOD jobs
        ledger.process_eod(day)
        
        # 3. Print Daily Statements
        for account_id in ledger.accounts:
            ledger_bal = ledger.get_ledger_balance(account_id, current_system_day=day, target_value_date=day)
            avail_bal = ledger.get_available_balance(account_id, current_system_day=day)
            active_holds = ledger.get_active_holds(account_id, current_system_day=day)
            fees_today = sum(1 for e in ledger.event_stream if e.type == 'FEE' and e.system_day == day and e.account_id == account_id)
            
            print(f"[{account_id}] Ledger Bal: {ledger_bal} | Avail Bal: {avail_bal} | Active Holds: {active_holds} | Fees Today: {fees_today}")
            
        # Print any rejections or errors caught during posting
        if ledger.daily_errors:
            print("Errors/Rejections:")
            for err in ledger.daily_errors:
                print(f"  - {err}")
            ledger.daily_errors.clear()

# Execute the simulation
run_simulation()