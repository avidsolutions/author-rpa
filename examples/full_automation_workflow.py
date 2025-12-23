#!/usr/bin/env python3
"""Example: Full Automation Workflow with Autho.R RPA.

This example demonstrates a complete administrative workflow that:
1. Reads local data (CSV of client records)
2. Fetches web data (currency exchange rates)
3. Processes and transforms the data
4. Generates a Word document report
5. Creates a PDF summary
6. Logs all activities

This showcases how Autho.R can automate end-to-end business processes.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rpa import RPA
from rpa.workflows import AutomationWorkflow, AutomationStep, StepType


def create_invoice_workflow():
    """Create a workflow that processes invoices and generates reports."""

    workflow = AutomationWorkflow(
        name="Invoice Processing Workflow",
        description="Process client invoices, fetch exchange rates, generate reports"
    )

    # Step 1: Read client invoice data from CSV
    workflow.read_csv(
        name="load_invoices",
        path="data/invoices.csv",
        save_as="invoices"
    )

    # Step 2: Fetch current exchange rates from API
    workflow.api_call(
        name="fetch_exchange_rates",
        url="https://api.exchangerate-api.com/v4/latest/USD",
        save_as="exchange_rates"
    )

    # Step 3: Transform data - calculate totals with exchange rates
    def calculate_totals(context):
        invoices = context.get("invoices", [])
        rates = context.get("exchange_rates", {}).get("rates", {})

        for invoice in invoices:
            amount_usd = float(invoice.get("amount", 0))
            invoice["amount_eur"] = round(amount_usd * rates.get("EUR", 0.85), 2)
            invoice["amount_gbp"] = round(amount_usd * rates.get("GBP", 0.73), 2)

        return invoices

    workflow.custom(
        name="calculate_totals",
        action=calculate_totals,
        save_as="processed_invoices"
    )

    # Step 4: Generate Word report
    workflow.create_word(
        name="generate_report",
        output_path="output/invoice_report.docx",
        title="Invoice Processing Report",
        content="{{report_content}}"
    )

    # Step 5: Log completion
    workflow.log(
        name="log_completion",
        message="Invoice processing workflow completed successfully"
    )

    return workflow


def create_form_filling_workflow():
    """Create a workflow that fills out government/business forms."""

    workflow = AutomationWorkflow(
        name="Form Filling Workflow",
        description="Automatically fill government forms with company data"
    )

    # Step 1: Read company data from JSON config
    workflow.read_file(
        name="load_company_data",
        path="config/company_info.json",
        save_as="company_data"
    )

    # Step 2: Parse the JSON
    def parse_json(context):
        import json
        raw_data = context.get("company_data", "{}")
        return json.loads(raw_data)

    workflow.custom(
        name="parse_company_data",
        action=parse_json,
        save_as="company"
    )

    # Step 3: Fill the form
    workflow.add_step(AutomationStep(
        name="fill_esd_form",
        step_type=StepType.FILL_FORM,
        params={
            "template_path": "templates/EMPIRE STATE DEVELOPMENT_PIW.docx",
            "output_path": "output/ESD_FORM_FILLED.docx",
            "field_mappings": [
                {"table": 0, "row": 0, "col": 2, "value": "{{company.project_name}}"},
                {"table": 0, "row": 2, "col": 2, "value": "{{company.legal_name}}"},
                {"table": 0, "row": 5, "col": 2, "value": "{{company.contact_name}}"},
                {"table": 0, "row": 7, "col": 7, "value": "{{company.email}}"},
            ],
        },
    ))

    # Step 4: Log
    workflow.log(
        name="log_completion",
        message="Form filled and saved to output/ESD_FORM_FILLED.docx"
    )

    return workflow


def create_web_scrape_report_workflow():
    """Create a workflow that scrapes web data and generates a report."""

    workflow = AutomationWorkflow(
        name="Web Scrape and Report",
        description="Scrape website data and generate PDF report"
    )

    # Step 1: Fetch webpage
    workflow.http_get(
        name="fetch_page",
        url="https://httpbin.org/json",
        save_as="web_data"
    )

    # Step 2: Transform to report content
    def format_report(context):
        data = context.get("web_data", {})
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report = f"""
WEB DATA REPORT
Generated: {now}
================

Data Source: httpbin.org
Type: JSON API Response

Content:
{data}

--- End of Report ---
"""
        return report

    workflow.custom(
        name="format_report",
        action=format_report,
        save_as="report_content"
    )

    # Step 3: Create PDF
    workflow.create_pdf(
        name="generate_pdf",
        output_path="output/web_report.pdf",
        content="{{report_content}}",
        title="Web Scraping Report"
    )

    # Step 4: Also save as text file
    workflow.write_file(
        name="save_text_report",
        path="output/web_report.txt",
        content="{{report_content}}"
    )

    return workflow


def create_data_pipeline_workflow():
    """Create a data pipeline workflow with multiple transformations."""

    workflow = AutomationWorkflow(
        name="Data Pipeline",
        description="ETL pipeline: Extract, Transform, Load"
    )

    # Step 1: Extract - Read source data
    workflow.read_csv(
        name="extract_data",
        path="data/raw_sales.csv",
        save_as="raw_data"
    )

    # Step 2: Transform - Clean and process
    def clean_data(context):
        data = context.get("raw_data", [])
        cleaned = []
        for row in data:
            if row.get("amount") and float(row.get("amount", 0)) > 0:
                row["amount"] = float(row["amount"])
                row["processed_at"] = datetime.now().isoformat()
                cleaned.append(row)
        return cleaned

    workflow.custom(
        name="transform_clean",
        action=clean_data,
        save_as="cleaned_data"
    )

    # Step 3: Transform - Aggregate
    def aggregate_data(context):
        data = context.get("cleaned_data", [])
        total = sum(row.get("amount", 0) for row in data)
        count = len(data)
        return {
            "total_sales": total,
            "transaction_count": count,
            "average_sale": total / count if count > 0 else 0,
        }

    workflow.custom(
        name="transform_aggregate",
        action=aggregate_data,
        save_as="summary"
    )

    # Step 4: Load - Write processed data
    workflow.write_csv(
        name="load_processed",
        path="output/processed_sales.csv",
        data="cleaned_data"
    )

    # Step 5: Generate summary report
    def create_summary_report(context):
        summary = context.get("summary", {})
        return f"""
SALES SUMMARY REPORT
====================
Total Sales: ${summary.get('total_sales', 0):,.2f}
Transactions: {summary.get('transaction_count', 0)}
Average Sale: ${summary.get('average_sale', 0):,.2f}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    workflow.custom(
        name="create_summary",
        action=create_summary_report,
        save_as="summary_report"
    )

    workflow.write_file(
        name="save_summary",
        path="output/sales_summary.txt",
        content="{{summary_report}}"
    )

    return workflow


def demo_fluent_api():
    """Demonstrate the fluent API for building workflows."""

    print("\n" + "=" * 70)
    print("FLUENT API DEMONSTRATION")
    print("=" * 70)

    # Build workflow with fluent API (method chaining)
    workflow = (
        AutomationWorkflow("Quick Report", "Generate quick report from API")
        .http_get("fetch_data", "https://httpbin.org/get", save_as="api_response")
        .log("log_fetch", "Data fetched successfully")
        .custom("process", lambda context: {"processed": True, "data": context.get("api_response")}, save_as="result")
        .log("log_done", "Processing complete")
    )

    # Preview the workflow
    print("\nWorkflow Steps:")
    for step in workflow.dry_run():
        print(f"  - {step['name']} ({step['type']})")

    # Execute
    print("\nExecuting workflow...")
    result = workflow.run()

    print(f"\nStatus: {result['status']}")
    print(f"Duration: {result['duration']:.2f}s")


def main():
    """Run the automation workflow demonstrations."""

    print("=" * 70)
    print("Autho.R RPA - Full Automation Workflow Examples")
    print("=" * 70)

    # Create output directory
    Path("output").mkdir(exist_ok=True)

    # Demo 1: Fluent API
    demo_fluent_api()

    # Demo 2: Invoice workflow (preview only - requires data files)
    print("\n" + "=" * 70)
    print("INVOICE WORKFLOW PREVIEW")
    print("=" * 70)

    invoice_workflow = create_invoice_workflow()
    print("\nWorkflow: " + invoice_workflow.name)
    print("Steps:")
    for step in invoice_workflow.dry_run():
        print(f"  {step['name']:25} -> {step['type']}")
        if step.get('saves_as'):
            print(f"    {'':25}    saves as: {step['saves_as']}")

    # Demo 3: Export workflow as JSON
    print("\n" + "=" * 70)
    print("WORKFLOW JSON EXPORT")
    print("=" * 70)

    web_workflow = create_web_scrape_report_workflow()
    json_export = web_workflow.to_json()
    print(json_export[:500] + "...")

    print("\n" + "=" * 70)
    print("All demonstrations complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
