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
            
            def italicise(indexes: list):
                """
                This function returns a row-wise style for DataFrame rows.
                Rows with indexes in the `indexes` list will be italicised.
                
                :param indexes: List of DataFrame indexes to italicise.
                :return: A function to be applied with df.style.apply.
                """
                def style_row(row):
                    if row.name in indexes:  # Check if the row's index is in the list
                        return ['font-style: italic'] * len(row)  # Italicize the entire row
                    else:
                        return [''] * len(row)  # No styling for other rows
                return style_row
            
            def make_bold(indexes: list):
                """
                This function returns a row-wise style for DataFrame rows.
                Rows with indexes in the `indexes` list will be made bold.
                
                :param indexes: List of DataFrame indexes of rows to make bold.
                :return: A function to be applied with df.style.apply.
                """
                def style_row(row):
                    if row.name in indexes:  # Check if the row's index is in the list
                        return ['font-weight: bold'] * len(row)  # Make the entire row bold
                    else:
                        return [''] * len(row)  # No styling for other rows
                return style_row
            
            def color_text(indexes: list, color: str):
                """
                This function returns a row-wise style for DataFrame rows.
                Rows with indexes in the `indexes` list will have their text color changed.

                :param indexes: List of DataFrame indexes to colorize.
                :param color: The desired text color (e.g., "red", "#ff0000").
                :return: A function to be applied with df.style.apply.
                """
                def style_row(row):
                    if row.name in indexes:  # Check if the row's index is in the list
                        return [f'color: {color}'] * len(row)  # Apply the text color to all cells
                    else:
                        return [''] * len(row)  # No styling for other rows
                return style_row
            
            def fill_row_color(indexes: list, color: str):
                """
                This function returns a row-wise style for DataFrame rows.
                Rows with indexes in the `indexes` list will have their background color filled.

                :param indexes: List of DataFrame indexes to fill.
                :param color: The desired background color (e.g., "yellow", "#ffcccb").
                :return: A function to be applied with df.style.apply.
                """
                def style_row(row):
                    if row.name in indexes:  # Check if the row's index is in the list
                        return [f'background-color: {color}'] * len(row)  # Apply background color to all cells
                    else:
                        return [''] * len(row)  # No styling for other rows
                return style_row

            # Specify the rows to italicize (by index)
            indexes_to_italicize = [1, 2, 3, 5, 6, 7, 9, 11]
            indexes_to_color = [1, 2, 3, 5, 6, 7, 9, 11]
            indexes_to_make_bold = [0, 4, 8, 10, 12]
            indexes_to_fill_row_color = [0, 4, 8, 10, 12]

            # Apply the styling
            styled_df = df_results.style.apply(italicise(indexes_to_italicize), axis=1)
            styled_df = styled_df.apply(color_text(indexes_to_color, 'grey'), axis=1)
            styled_df = styled_df.apply(make_bold(indexes_to_make_bold), axis=1)
            styled_df = styled_df.apply(fill_row_color(indexes_to_fill_row_color, 'lightgrey'), axis=1)
            styled_df = styled_df.set_table_attributes('class="table table-hover"')
            styled_df = styled_df.format(lambda x: f"£{x:,.2f}" if isinstance(x, (int, float)) else x)
            styled_df = styled_df.set_properties(subset=['Annual', 'Monthly', 'Weekly'], **{'text-align': 'left'})
            styled_df = styled_df.hide(axis="index")

            # Convert to HTML
            table_html = styled_df.to_html(index=False)

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