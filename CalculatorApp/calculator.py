import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dataclasses import dataclass, field

# ======== GLOBAL CONSTANTS / CONFIGURATION ========

TAX_BANDS = [
    # (upper_limit, tax_rate)
    (50_270, 0.20),       # 20% up to 50,270
    (125_140, 0.40),      # 40% from 50,270 to 125,140
    (float('inf'), 0.45)  # 45% above 125,140
]

PERSONAL_ALLOWANCE_DEFAULT = 12_570
PERSONAL_ALLOWANCE_TAPER_THRESHOLD = 100_000
NI_THRESHOLDS = {
    'LOWER_MONTHLY': 1_048,
    'UPPER_MONTHLY': 4_189,
    'MAIN_RATE': 0.08,
    'UPPER_RATE': 0.02
}
STUDENT_LOAN_PLANS = {
    'Plan 2': {
        'rate': 0.09,
        'threshold': 27_295
    },
    'No Plan': {
        'rate': 0.00,
        'threshold': float('inf')  # Or 0, effectively no repayment
    }
}

WEEKS_PER_MONTH = 4.345

# ======== USER DATA CLASS ========

@dataclass
class User:
    """
    Holds all relevant personal financial information for calculation.
    
    Attributes:
        gross_salary: Annual salary (before tax/NI).
        monthly_bills: Dict of fixed monthly bills, e.g. rent, council tax.
        weekly_expenses: Dict of recurring weekly expenses, e.g. groceries.
        pension_contribution_percentage: % of gross salary contributed to pension.
        salary_sacrifice: Monthly amount contributed via salary sacrifice schemes.
        student_loan_plan: String identifier for the student loan plan, e.g. 'Plan 2' or 'No Plan'.
    """
    gross_salary: float
    monthly_bills: dict[str, float] = field(default_factory=dict)
    weekly_expenses: dict[str, float] = field(default_factory=dict)
    pension_contribution_percentage: float = 0.0
    salary_sacrifice: float = 0.0
    student_loan_plan: str = "No Plan"

# ======== PERIOD AMOUNTS ========

class PeriodAmounts:
    """
    Stores an amount in a canonical (e.g. annual) format, but can be constructed
    using annual, monthly, or weekly amounts.
    """

    def __init__(
        self,
        *,
        annual: float = None,
        monthly: float = None,
        weekly: float = None,
        weeks_per_year: float = 52.1429
    ):
        """
        Exactly one of `annual`, `monthly`, or `weekly` should be provided.
        If multiple or none are provided, raises a ValueError.

        :param annual: The amount in annual terms.
        :param monthly: The amount in monthly terms.
        :param weekly: The amount in weekly terms.
        :param weeks_per_year: Number of weeks used to convert from weekly to annual.
        """
        # Count how many arguments are non-None.
        provided_args = sum(val is not None for val in [annual, monthly, weekly])
        if provided_args != 1:
            raise ValueError(
                "Exactly one of `annual`, `monthly`, or `weekly` must be provided."
            )

        self._weeks_per_year = weeks_per_year

        # Convert whichever input we got into the canonical annual amount.
        if annual is not None:
            self._annual = annual
        elif monthly is not None:
            self._annual = monthly * 12
        else:  # weekly is not None
            self._annual = weekly * self._weeks_per_year

    @property
    def annual(self) -> float:
        return self._annual

    @property
    def monthly(self) -> float:
        return self._annual / 12

    @property
    def weekly(self) -> float:
        return self._annual / self._weeks_per_year

    def as_dict(self, currency_prefix: str = '£') -> dict[str, str]:
        """
        Return a dictionary with the annual, monthly, and weekly amounts
        already formatted with a currency prefix.
        """
        return {
            "annual": f"{currency_prefix}{self.annual:,.2f}",
            "monthly": f"{currency_prefix}{self.monthly:,.2f}",
            "weekly": f"{currency_prefix}{self.weekly:,.2f}",
        }

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(annual={self.annual:.2f}, "
            f"monthly={self.monthly:.2f}, weekly={self.weekly:.2f})"
        )

# ======== TAKE-HOME CALCULATOR ========

class TakeHomeCalculator:
    """
    Calculates various deductions and net pay for a given User.
    """

    def __init__(self, user: User):
        """
        Initialize with a User object containing all relevant financial info.
        """
        self.user = user
        self._pension_contribution = None
        self._salary_sacrifice = None
        self._personal_allowance = None
        self._taxable_income = None
        self._tax = None
        self._ni_contributions = None
        self._student_loan_repayment = None
        self._net_income = None
        self._bills = None
        self._total_bills = None
        self._spendable_income = None
        self._expenses = None
        self._total_expenses = None
        self._spendable_income_after_expenses = None

    def calculate_all(self) -> None:
        """
        Main entry point to calculate all relevant fields.
        """
        self._calculate_pension_contribution()
        self._calculate_salary_sacrifice()
        self._calculate_personal_allowance()
        self._calculate_taxable_income()
        self._calculate_tax()
        self._calculate_ni_contributions()
        self._calculate_student_loan_repayment()
        self._calculate_net_income()
        self._calculate_spendable_income()
        self._calculate_spendable_income_after_expenses()
    
    def get_results(self) -> dict[str, PeriodAmounts]:
        """
        Return each result as a PeriodAmounts object.
        """
        if self._net_income is None:
            self.calculate_all()

        gross_salary_pa = PeriodAmounts(annual=self.user.gross_salary)
        personal_allowance_pa = PeriodAmounts(annual=self._personal_allowance)
        
        results = {
            "Gross Salary": gross_salary_pa,
            "Pension Contribution": self._pension_contribution,
            "Salary Sacrifice": self._salary_sacrifice,
            "Personal Allowance": personal_allowance_pa,
            "Taxable Income": self._taxable_income,
            "Tax": self._tax,
            "NI Contributions": self._ni_contributions,
            "Student Loan Repayment": self._student_loan_repayment,
            "Net Income": self._net_income,
            "Bills": self._total_bills,
            "Spendable Income": self._spendable_income,
            "Expenses": self._total_expenses,
            "Spendable Income After Expenses": self._spendable_income_after_expenses,
        }
        return results

    # =============== HELPER CALCULATION METHODS ===============

    def _calculate_pension_contribution(self) -> PeriodAmounts:
        """
        Calculate the annual pension contribution based on gross salary and the user's
        pension contribution percentage.
        """
        if self._pension_contribution is None:
            annual_value = self.user.gross_salary * self.user.pension_contribution_percentage / 100
            self._pension_contribution = PeriodAmounts(annual=annual_value)
        return self._pension_contribution

    def _calculate_salary_sacrifice(self) -> PeriodAmounts:
        """
        Convert monthly salary sacrifice into an annual figure.
        """
        if self._salary_sacrifice is None:
            monthly_value = self.user.salary_sacrifice
            self._salary_sacrifice = PeriodAmounts(monthly=monthly_value)
        return self._salary_sacrifice

    def _calculate_personal_allowance(self) -> float:
        """
        Calculate personal allowance, which starts reducing once gross salary
        is above a certain threshold (£100k in the UK).
        """
        if self._personal_allowance is None:
            if self.user.gross_salary >= PERSONAL_ALLOWANCE_TAPER_THRESHOLD:
                # Tapering: lose £1 of allowance for every £2 above 100k
                tapered_amount = (self.user.gross_salary - PERSONAL_ALLOWANCE_TAPER_THRESHOLD) / 2
                self._personal_allowance = max(0, PERSONAL_ALLOWANCE_DEFAULT - tapered_amount)
            else:
                self._personal_allowance = PERSONAL_ALLOWANCE_DEFAULT
        return self._personal_allowance

    def _calculate_taxable_income(self) -> PeriodAmounts:
        """
        Total taxable income after subtracting pension, salary sacrifice, and personal allowance.
        """
        if self._taxable_income is None:
            pre_tax_deductions = (self._calculate_pension_contribution().annual +
                                  self._calculate_salary_sacrifice().annual)
            self._taxable_income = (
                self.user.gross_salary
                - pre_tax_deductions
                - self._calculate_personal_allowance()
            )
            # Ensure we don't treat negative taxable income as if it reduces the tax
            taxable_income = max(0, self._taxable_income)
            self._taxable_income = PeriodAmounts(annual=taxable_income)
        return self._taxable_income

    def _calculate_tax(self) -> PeriodAmounts:
        """
        Calculate tax using tiered rates (20%, 40%, 45%) on segments of taxable income.
        """
        if self._tax is None:
            annual_taxable_income = self._calculate_taxable_income().annual
            personal_allowance = self._calculate_personal_allowance()
            remaining = annual_taxable_income
            annual_tax = 0.0
            lower_limit = 0.0
            for upper_limit, rate in TAX_BANDS:
                # The first band effectively starts at 0 (after personal allowance).
                band_size = (upper_limit - personal_allowance) - lower_limit
                if remaining <= 0:
                    break
                if remaining <= band_size:
                    annual_tax+= remaining * rate
                    break
                else:
                    annual_tax += band_size * rate
                    remaining -= band_size
                    lower_limit = upper_limit - personal_allowance
            
            self._tax = PeriodAmounts(annual=annual_tax)
        return self._tax

    def _calculate_ni_contributions(self) -> PeriodAmounts:
        """
        Calculate National Insurance (NI) contributions based on monthly thresholds.
        """
        if self._ni_contributions is None:
            gross_salary = self.user.gross_salary
            monthly_salary = gross_salary / 12
            lower = NI_THRESHOLDS['LOWER_MONTHLY']
            upper = NI_THRESHOLDS['UPPER_MONTHLY']
            main_rate = NI_THRESHOLDS['MAIN_RATE']
            upper_rate = NI_THRESHOLDS['UPPER_RATE']

            if monthly_salary <= lower:
                annual_ni_contributions = 0.0
            elif lower < monthly_salary <= upper:
                annual_ni_contributions = main_rate * (gross_salary - 12 * lower)
            else:
                # NI on the band between lower and upper
                total_main = main_rate * 12 * (upper - lower)
                # NI above upper threshold
                total_upper = upper_rate * (gross_salary - 12 * upper)
                annual_ni_contributions = total_main + total_upper
            
            self._ni_contributions = PeriodAmounts(annual=annual_ni_contributions)
        return self._ni_contributions

    def _calculate_student_loan_repayment(self) -> PeriodAmounts:
        """
        Calculate annual student loan repayment based on the plan specified and thresholds.
        """
        if self._student_loan_repayment is None:
            plan = self.user.student_loan_plan
            if plan not in STUDENT_LOAN_PLANS:
                raise ValueError(
                    f"Unsupported student loan plan: {plan}. "
                    f"Supported plans are: {list(STUDENT_LOAN_PLANS.keys())}"
                )
            
            rate = STUDENT_LOAN_PLANS[plan]['rate']
            threshold = STUDENT_LOAN_PLANS[plan]['threshold']
            gross_salary = self.user.gross_salary
            annual_student_loan_repayment = max(0, rate * (gross_salary - threshold))

            self._student_loan_repayment = PeriodAmounts(annual=annual_student_loan_repayment)
        return self._student_loan_repayment

    def _calculate_net_income(self) -> PeriodAmounts:
        """
        Calculate the final net annual income by subtracting all taxes and deductions
        from gross salary.
        """
        if self._net_income is None:
            gross_salary = self.user.gross_salary
            pre_tax_deductions = (self._calculate_pension_contribution().annual +
                                  self._calculate_salary_sacrifice().annual)
            annual_tax = self._calculate_tax().annual
            annual_ni = self._calculate_ni_contributions().annual
            student_loan = self._calculate_student_loan_repayment().annual

            net_annual_income = (
                gross_salary - 
                pre_tax_deductions - 
                annual_tax - 
                annual_ni - 
                student_loan
            )

            self._net_income = PeriodAmounts(annual=net_annual_income)
        return self._net_income
    
    def _calculate_spendable_income(self) -> PeriodAmounts:
        """
        Calculates net income after taxes and semi-fixed bills are payed for.
        """
        if self._spendable_income is None:
            bills_pa = [
                PeriodAmounts(monthly=amt)
                for amt in self.user.monthly_bills.values()
            ]
            self._bills = bills_pa

            total_bills_pa = PeriodAmounts(annual=sum(b.annual for b in bills_pa))
            self._total_bills = total_bills_pa

            net_income_pa = self._calculate_net_income()
            annual_spendable_income = net_income_pa.annual - total_bills_pa.annual
            self._spendable_income = PeriodAmounts(annual=annual_spendable_income)
        return self._spendable_income
    
    def _calculate_spendable_income_after_expenses(self) -> PeriodAmounts:
        """
        Calculates net income after taxes, semi-fixed bills and weekly expenses
        (e.g. groceries) are payed for.
        """
        if self._spendable_income_after_expenses is None:
            expenses_pa = [
                PeriodAmounts(weekly=amt)
                for amt in self.user.weekly_expenses.values()
            ]
            self._expenses = expenses_pa
            total_expenses_pa = PeriodAmounts(annual=sum(e.annual for e in expenses_pa))
            self._total_expenses = total_expenses_pa
            spendable_income_pa = self._calculate_spendable_income()
            weekly_spendable_income_after_expenses = spendable_income_pa.weekly - total_expenses_pa.weekly
            self._spendable_income_after_expenses= PeriodAmounts(weekly=weekly_spendable_income_after_expenses)
        return self._spendable_income_after_expenses
    
# ======== HELPER FUNCTIONS =========
def build_results_dataframe(results: dict[str, PeriodAmounts]) -> pd.DataFrame:
    """
    Given a dict of {ItemName: PeriodAmounts}, build a DataFrame
    with columns [Item, Annual, Monthly, Weekly].
    """
    data = []
    for name, pa in results.items():
        data.append({
            "Item": name,
            "Annual": pa.annual,
            "Monthly": pa.monthly,
            "Weekly": pa.weekly
        })
    df = pd.DataFrame(data).round(2)
    return df

def create_sankey_figure(pa_results: dict[str, PeriodAmounts]) -> go.Figure:
    """
    Build a Sankey diagram from the annual amounts in `pa_results`.
    Keys in `pa_results` should include:
      - Gross Salary
      - Pension Contribution
      - Salary Sacrifice
      - Tax
      - NI Contributions
      - Student Loan Repayment
      - Net Income
      - Bills
      - Spendable Income
      - Expenses
      - Spendable Income After Expenses
    """
    # 1) Extract annual amounts from PeriodAmounts
    gross_salary = pa_results["Gross Salary"].annual
    pension = pa_results["Pension Contribution"].annual
    sacrifice = pa_results["Salary Sacrifice"].annual
    tax = pa_results["Tax"].annual
    ni = pa_results["NI Contributions"].annual
    student_loan = pa_results["Student Loan Repayment"].annual
    net_income = pa_results["Net Income"].annual
    bills = pa_results["Bills"].annual
    spendable_income = pa_results["Spendable Income"].annual
    expenses = pa_results["Expenses"].annual
    spendable_after_expenses = pa_results["Spendable Income After Expenses"].annual

    # 2) Define the Sankey nodes (each index corresponds to a label)
    labels = [
        "Gross Salary",             # 0
        "Pension",                  # 1
        "Salary Sacrifice",         # 2
        "Tax",                      # 3
        "NI",                       # 4
        "Student Loan",             # 5
        "Net Income",               # 6
        "Bills",                    # 7
        "Spendable Income",         # 8
        "Expenses",                 # 9
        "Income After Expenses"     # 10
    ]

    # 3) Define the links (source -> target, with 'value')
    #    - All outflows from Gross Salary (node 0)
    #    - Net Income (node 6) splits into Bills (node 7) and Spendable (node 8)
    #    - Spendable (node 8) splits into Weekly Expenses (node 9) and leftover (node 10)

    sources = [
        0, 0, 0, 0, 0, 0,          # from Gross Salary -> Pension, Sacrifice, Tax, NI, Student Loan
        6, 6,                      # from Net Income -> Bills, Spendable
        8, 8                       # from Spendable -> Expenses, Income After Expenses
    ]

    targets = [
        1, 2, 3, 4, 5, 6,          # indices for Pension, Sacrifice, Tax, NI, Student Loan
        7, 8,                      # Bills, Spendable Income
        9, 10                      # Expenses, Income After Expenses
    ]

    values = [
        pension, sacrifice, tax, ni, student_loan, net_income,
        bills, spendable_income,
        expenses, spendable_after_expenses
    ]

    # 4) Build the Sankey figure
    fig = go.Figure(data=[go.Sankey(
        arrangement="snap",
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color="lightblue"
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color="rgba(100, 100, 100, 0.2)"  # semi-transparent links
        )
    )])

    fig.update_layout(
        title_text="Annual Cash Flow Sankey Diagram",
        font_size=12,
        width=1000,
        height=600
    )
    return fig