from django import forms

STUDENT_LOAN_CHOICES = [
    ('Plan 2', 'Plan 2'),
    ('No Plan', 'No Plan'),
]

class CalculatorForm(forms.Form):
    gross_salary = forms.FloatField(
        label="Gross Salary",
        min_value=0,
        widget=forms.NumberInput(attrs={
            "style": "width: 120px;",  # Inline CSS to control the width
            "placeholder": "Enter salary",  # Optional: Add a placeholder
        })
    )
    pension_contribution_percentage = forms.FloatField(
        label="Pension Contribution", 
        min_value=0, 
        required=False,
        widget=forms.NumberInput(attrs={
            "style": "width: 120px;",  # Inline CSS to control the width
        })
    )
    salary_sacrifice = forms.FloatField(
        label="Monthly Salary Sacrifice",
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            "style": "width: 120px;",  # Inline CSS to control the width
        })
    )
    student_loan_plan = forms.ChoiceField(
        label="Student Loan Plan",
        choices=STUDENT_LOAN_CHOICES,
        required=False
    )

    # Monthly Bills
    rent = forms.FloatField(
        label="Rent or Mortgage", 
        min_value=0, 
        required=False,
        widget=forms.NumberInput(attrs={
            "style": "width: 120px;",  # Inline CSS to control the width
        })
    )
    
    council_tax = forms.FloatField(
        label="Council Tax", 
        min_value=0, 
        required=False,
        widget=forms.NumberInput(attrs={
            "style": "width: 120px;",  # Inline CSS to control the width
        })
    )

    electricity = forms.FloatField(
        label="Electricity", 
        min_value=0, 
        required=False,
        widget=forms.NumberInput(attrs={
            "style": "width: 120px;",  # Inline CSS to control the width
        })
    )

    gas = forms.FloatField(
        label="Gas", 
        min_value=0, 
        required=False,
        widget=forms.NumberInput(attrs={
            "style": "width: 120px;",  # Inline CSS to control the width
        })
    )

    water = forms.FloatField(
        label="Water", 
        min_value=0, 
        required=False,
        widget=forms.NumberInput(attrs={
            "style": "width: 120px;",  # Inline CSS to control the width
        })
    )

    internet = forms.FloatField(
        label="Internet", 
        min_value=0, 
        required=False,
        widget=forms.NumberInput(attrs={
            "style": "width: 120px;",  # Inline CSS to control the width
        })
    )

    phone = forms.FloatField(
        label="Phone", 
        min_value=0, 
        required=False,
        widget=forms.NumberInput(attrs={
            "style": "width: 120px;",  # Inline CSS to control the width
        })
    )

    subscriptions = forms.FloatField(
        label="Subscriptions", 
        min_value=0, 
        required=False,
        widget=forms.NumberInput(attrs={
            "style": "width: 120px;",  # Inline CSS to control the width
        })
    )

    other_monthly = forms.FloatField(
        label="Other", 
        min_value=0, 
        required=False,
        widget=forms.NumberInput(attrs={
            "style": "width: 120px;",  # Inline CSS to control the width
        })
    )

    # Weekly Expenses
    groceries = forms.FloatField(
        label="Groceries", 
        min_value=0, 
        required=False,
        widget=forms.NumberInput(attrs={
            "style": "width: 120px;",  # Inline CSS to control the width
        })
    )

    eating_out = forms.FloatField(
        label="Eating Out", 
        min_value=0, 
        required=False,
        widget=forms.NumberInput(attrs={
            "style": "width: 120px;",  # Inline CSS to control the width
        })
    )

    travel = forms.FloatField(
        label="Travel", 
        min_value=0, 
        required=False,
        widget=forms.NumberInput(attrs={
            "style": "width: 120px;",  # Inline CSS to control the width
        })
    )

    other_weekly = forms.FloatField(
        label="Other", 
        min_value=0, 
        required=False,
        widget=forms.NumberInput(attrs={
            "style": "width: 120px;",  # Inline CSS to control the width
        })
    )