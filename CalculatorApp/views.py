import io
import base64

import pandas as pd
from django.shortcuts import render
from plotly.offline import plot
from plotly.graph_objects import Figure

from .forms import CalculatorForm
from .calculator import User, TakeHomeCalculator, build_results_dataframe, create_sankey_figure

def calculator_view(request):
    """
    Shows a form to collect user data, then displays
    a table + Sankey diagram of the results.
    """

    if request.method == 'POST':
        form = CalculatorForm(request.POST)
        if form.is_valid():
            # 1. Extract data from form

            # Annual Fields
            gross_salary = form.cleaned_data['gross_salary']
            pension_contribution_percentage = form.cleaned_data['pension_contribution_percentage'] or 0
            salary_sacrifice = form.cleaned_data['salary_sacrifice'] or 0
            student_loan_plan = form.cleaned_data['student_loan_plan'] or 'No Plan'

            # Monthly Bills
            rent = form.cleaned_data['rent'] or 0
            council_tax = form.cleaned_data['council_tax'] or 0
            electricity = form.cleaned_data['electricity'] or 0
            gas = form.cleaned_data['gas'] or 0
            water = form.cleaned_data['water'] or 0
            internet = form.cleaned_data['internet'] or 0
            phone = form.cleaned_data['phone'] or 0
            subscriptions = form.cleaned_data['subscriptions'] or 0
            other_monthly = form.cleaned_data['other_monthly'] or 0

            # Weekly Expenses
            groceries = form.cleaned_data['groceries'] or 0
            eating_out = form.cleaned_data['eating_out'] or 0
            travel = form.cleaned_data['travel'] or 0
            other_weekly = form.cleaned_data['other_weekly'] or 0

            # 2. Build dictionaries for monthly_bills & weekly_expenses 
            monthly_bills = {
                'rent': rent,
                'council_tax': council_tax,
                'electricity': electricity,
                'gas': gas,
                'water': water,
                'internet': internet,
                'phone': phone,
                'subscriptions': subscriptions,
                'other': other_monthly
            }

            weekly_expenses = {
                'groceries': groceries,
                'eating_out': eating_out,
                'travel': travel,
                'other': other_weekly
            }

            # 3. Create User object
            user = User(
                gross_salary=gross_salary,
                monthly_bills=monthly_bills,
                weekly_expenses=weekly_expenses,
                pension_contribution_percentage=pension_contribution_percentage,
                salary_sacrifice=salary_sacrifice,
                student_loan_plan=student_loan_plan
            )

            # 4. Run the TakeHomeCalculator
            calculator = TakeHomeCalculator(user)
            calculator.calculate_all()
            pa_results = calculator.get_results()  # returns dict[str, PeriodAmounts]

            # 5. Build DataFrame
            df_results = build_results_dataframe(pa_results)

            # Convert DataFrame to HTML (for embedding in template)
            table_html = df_results.to_html(
                classes="table table-hover",
                float_format="£{:,.2f}".format,
                index=False,
                justify='left'
            )

            # 6. Build Sankey figure
            sankey_fig = create_sankey_figure(pa_results)
            # Convert Sankey figure to HTML <div> (no extra JS needed if we 
            # handle it with 'include_plotlyjs=True' or a separate script)
            sankey_div = plot(
                sankey_fig, 
                output_type='div', 
                include_plotlyjs=False   # We can include Plotly separately in the template
            )

            # 7. Render results template
            return render(
                request,
                'CalculatorApp/calculator_results.html',
                {
                    'form': form,
                    'table_html': table_html,
                    'sankey_div': sankey_div,
                }
            )
    else:
        form = CalculatorForm()

    # If it's a GET or the form is invalid, display the form again
    return render(request, 'CalculatorApp/calculator_form.html', {'form': form})