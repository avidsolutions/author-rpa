"""
Illinois Procurement Gateway (IPG) Application Fix Script
Addresses returned application issues and provides automation for corrections
"""

import os
import json
from datetime import datetime
from pathlib import Path
import requests
from typing import Dict, List, Tuple


class IPGApplicationFixer:
    """Handles IPG application corrections and document verification"""
    
    REQUIRED_DOCS_2024 = {
        'federal_tax_return': 'Federal income tax return (2024) - gross sales page',
        'illinois_tax_return': 'Illinois income tax return - address page',
        'il_941_form': 'Form IL-941 (for manufacturers only)'
    }
    
    OWNERSHIP_THRESHOLD_PERCENT = 5.0
    OWNERSHIP_THRESHOLD_DOLLAR = 142740.00
    
    def __init__(self, company_name: str, output_dir: str = './output'):
        self.company_name = company_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.report = []
        
    def add_to_report(self, message: str, severity: str = "INFO"):
        """Add a message to the report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{severity}] {message}"
        self.report.append(entry)
        print(entry)
    
    def check_question_c1_documents(self, docs_path: str) -> Dict[str, bool]:
        """
        Check if required documents for Question C.1 are present
        
        Args:
            docs_path: Path to directory containing tax documents
            
        Returns:
            Dictionary with document status
        """
        self.add_to_report("=" * 80)
        self.add_to_report("CHECKING QUESTION C.1 - REQUIRED DOCUMENTATION")
        self.add_to_report("=" * 80)
        
        docs_dir = Path(docs_path)
        status = {}
        
        if not docs_dir.exists():
            self.add_to_report(f"Documents directory not found: {docs_path}", "ERROR")
            return status
        
        # Check for 2024 Federal tax return
        federal_files = list(docs_dir.glob("*federal*2024*")) + \
                       list(docs_dir.glob("*1040*2024*")) + \
                       list(docs_dir.glob("*1120*2024*"))
        status['federal_tax_return'] = len(federal_files) > 0
        
        if status['federal_tax_return']:
            self.add_to_report(f"✓ Federal tax return found: {federal_files[0].name}")
        else:
            self.add_to_report("✗ Federal tax return (2024) NOT FOUND", "ERROR")
            self.add_to_report("  Required: Page showing total annual gross sales from 2024 Federal return")
        
        # Check for Illinois tax return
        illinois_files = list(docs_dir.glob("*illinois*")) + \
                        list(docs_dir.glob("*IL*tax*"))
        status['illinois_tax_return'] = len(illinois_files) > 0
        
        if status['illinois_tax_return']:
            self.add_to_report(f"✓ Illinois tax return found: {illinois_files[0].name}")
        else:
            self.add_to_report("✗ Illinois tax return NOT FOUND", "ERROR")
            self.add_to_report("  Required: Page showing Illinois address")
        
        # Check for IL-941 (for manufacturers)
        il941_files = list(docs_dir.glob("*941*")) + \
                     list(docs_dir.glob("*IL-941*"))
        status['il_941_form'] = len(il941_files) > 0
        
        if status['il_941_form']:
            self.add_to_report(f"✓ Form IL-941 found: {il941_files[0].name}")
        else:
            self.add_to_report("⚠ Form IL-941 NOT FOUND (Required for manufacturers only)", "WARNING")
            self.add_to_report("  If manufacturer: Submit IL-941 showing W-2, W-2G, 1099-R count")
        
        return status
    
    def check_illinois_sos_status(self, business_name: str = None) -> Dict:
        """
        Check business standing with Illinois Secretary of State
        
        Args:
            business_name: Business name to check (defaults to company_name)
            
        Returns:
            Dictionary with business status information
        """
        self.add_to_report("=" * 80)
        self.add_to_report("CHECKING QUESTION E.1 - ILLINOIS SOS BUSINESS STATUS")
        self.add_to_report("=" * 80)
        
        business_name = business_name or self.company_name
        
        result = {
            'business_name': business_name,
            'in_good_standing': None,
            'check_url': 'http://www.cyberdriveillinois.com/departments/business_services/corp.html',
            'resolve_url': 'http://www.cyberdriveillinois.com/departments/business_services/howdoi.html'
        }
        
        self.add_to_report(f"Business Name: {business_name}")
        self.add_to_report("⚠ MANUAL CHECK REQUIRED", "WARNING")
        self.add_to_report(f"  1. Visit: {result['check_url']}")
        self.add_to_report("  2. Search for your business")
        self.add_to_report("  3. Verify 'Good Standing' status")
        
        self.add_to_report("\n✗ ISSUE REPORTED: Business not in good standing", "ERROR")
        self.add_to_report("  ACTION REQUIRED:")
        self.add_to_report(f"  - Contact IL SOS Department of Business Services")
        self.add_to_report(f"  - Resolve standing issues before re-submitting IPG")
        self.add_to_report(f"  - Info: {result['resolve_url']}")
        
        return result
    
    def calculate_ownership_disclosure(self, owners: List[Dict]) -> Tuple[bool, List[Dict]]:
        """
        Determine if ownership disclosure is required (Question I.1)
        
        Args:
            owners: List of owner dictionaries with 'name', 'ownership_percent', 
                   'ownership_value', 'distributive_income_percent', 'distributive_income_value'
        
        Returns:
            Tuple of (disclosure_required, list of owners requiring disclosure)
        """
        self.add_to_report("=" * 80)
        self.add_to_report("CHECKING QUESTION I.1 - OWNERSHIP DISCLOSURE REQUIREMENTS")
        self.add_to_report("=" * 80)
        
        disclosure_required = False
        owners_to_disclose = []
        
        self.add_to_report(f"Ownership Threshold: {self.OWNERSHIP_THRESHOLD_PERCENT}% or ${self.OWNERSHIP_THRESHOLD_DOLLAR:,.2f}")
        self.add_to_report(f"Distributive Income Threshold: {self.OWNERSHIP_THRESHOLD_PERCENT}% or ${self.OWNERSHIP_THRESHOLD_DOLLAR:,.2f}")
        self.add_to_report("")
        
        for owner in owners:
            name = owner.get('name', 'Unknown')
            ownership_pct = owner.get('ownership_percent', 0)
            ownership_val = owner.get('ownership_value', 0)
            income_pct = owner.get('distributive_income_percent', 0)
            income_val = owner.get('distributive_income_value', 0)
            
            requires_disclosure = False
            reasons = []
            
            # Check Question A: Owns more than 5%
            if ownership_pct > self.OWNERSHIP_THRESHOLD_PERCENT:
                requires_disclosure = True
                reasons.append(f"Owns {ownership_pct}% (> {self.OWNERSHIP_THRESHOLD_PERCENT}%)")
            
            # Check Question B: Owns less than 5% but value > $142,740
            if ownership_pct <= self.OWNERSHIP_THRESHOLD_PERCENT and ownership_val > self.OWNERSHIP_THRESHOLD_DOLLAR:
                requires_disclosure = True
                reasons.append(f"Ownership value ${ownership_val:,.2f} (> ${self.OWNERSHIP_THRESHOLD_DOLLAR:,.2f})")
            
            # Check Question C: Entitled to more than 5% distributive income
            if income_pct > self.OWNERSHIP_THRESHOLD_PERCENT:
                requires_disclosure = True
                reasons.append(f"Distributive income {income_pct}% (> {self.OWNERSHIP_THRESHOLD_PERCENT}%)")
            
            # Check Question D: Entitled to more than $142,740 distributive income
            if income_val > self.OWNERSHIP_THRESHOLD_DOLLAR:
                requires_disclosure = True
                reasons.append(f"Distributive income ${income_val:,.2f} (> ${self.OWNERSHIP_THRESHOLD_DOLLAR:,.2f})")
            
            if requires_disclosure:
                disclosure_required = True
                owner['disclosure_reasons'] = reasons
                owners_to_disclose.append(owner)
                self.add_to_report(f"✓ REQUIRES DISCLOSURE: {name}")
                for reason in reasons:
                    self.add_to_report(f"    - {reason}")
            else:
                self.add_to_report(f"  No disclosure required: {name}")
        
        self.add_to_report("")
        if disclosure_required:
            self.add_to_report(f"✗ DISCLOSURE REQUIRED for {len(owners_to_disclose)} owner(s)", "ERROR")
            self.add_to_report("  ACTION REQUIRED:")
            self.add_to_report("  1. Answer Question I.1 as 'Yes, the information is not publicly available'")
            self.add_to_report("  2. Download IPG Percentage of Ownership and Distributive Income Form")
            self.add_to_report("  3. Complete form for all disclosed owners")
            self.add_to_report("  4. Re-attach completed form to Question I.1")
            self.add_to_report("  5. Review/update Form I Questions: 5, 6, 7, 8, 11-20")
        else:
            self.add_to_report("✓ No ownership disclosure required (all owners < 5% and < $142,740)")
        
        return disclosure_required, owners_to_disclose
    
    def generate_checklist(self, is_manufacturer: bool = False) -> str:
        """Generate a comprehensive checklist for IPG application corrections"""
        self.add_to_report("=" * 80)
        self.add_to_report("GENERATING IPG APPLICATION CORRECTION CHECKLIST")
        self.add_to_report("=" * 80)
        
        checklist = f"""
IPG APPLICATION CORRECTION CHECKLIST
Company: {self.company_name}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

═══════════════════════════════════════════════════════════════════════════════

QUESTION C.1 - REQUIRED DOCUMENTATION
═══════════════════════════════════════════════════════════════════════════════

[ ] 1. Federal Income Tax Return (2024)
       - Must be CURRENT 2024 copy
       - Include page(s) showing total annual gross sales
       - Forms: 1040, 1120, 1120-S, or 1065 as applicable

[ ] 2. Illinois Income Tax Return (Most Recent)
       - Include page showing Illinois address
       - Must clearly display company address in Illinois

{"[ ] 3. Form IL-941 (Illinois Annual Withholding Income Tax Return)" if is_manufacturer else ""}
{"       - REQUIRED FOR MANUFACTURERS ONLY" if is_manufacturer else ""}
{"       - Must be latest year's form" if is_manufacturer else ""}
{"       - Must show number of Forms W-2, W-2G, and 1099-R issued" if is_manufacturer else ""}

═══════════════════════════════════════════════════════════════════════════════

QUESTION E.1 - ILLINOIS SECRETARY OF STATE GOOD STANDING
═══════════════════════════════════════════════════════════════════════════════

[ ] 1. Check Business Standing
       - Visit: http://www.cyberdriveillinois.com/departments/business_services/corp.html
       - Search for your business
       - Verify current status

[ ] 2. Resolve Standing Issues (IF NOT IN GOOD STANDING)
       - Contact IL SOS Department of Business Services
       - Address any compliance issues
       - Pay outstanding fees if applicable
       - Info: http://www.cyberdriveillinois.com/departments/business_services/howdoi.html

[ ] 3. Obtain Proof of Good Standing
       - Request Certificate of Good Standing from IL SOS
       - Attach to application if required

═══════════════════════════════════════════════════════════════════════════════

QUESTION I.1 - OWNERSHIP AND DISTRIBUTIVE INCOME DISCLOSURE
═══════════════════════════════════════════════════════════════════════════════

UNDERSTANDING THE FOUR-PART QUESTION:

[ ] Question A: Does any person/entity own MORE THAN 5% of the company?
    Note: Only answer "No" if you have 20+ owners each owning ≤5%

[ ] Question B: Does any person/entity own LESS THAN 5%, but ownership 
    value is GREATER THAN $142,740?

[ ] Question C: Is any person/entity entitled to MORE THAN 5% of the 
    company's distributive income?

[ ] Question D: Is any person/entity entitled to MORE THAN $142,740 of 
    the company's distributive income?

IF ANY ANSWER IS "YES":

[ ] 1. Answer Question I.1 as "Yes, the information is not publicly available"

[ ] 2. Download the form:
       "IPG Percentage of Ownership and Distributive Income Form"

[ ] 3. Complete the form for ALL qualifying individuals/entities

[ ] 4. Re-attach completed form to Question I.1

[ ] 5. Review and update Form I questions if needed:
       - Question 5
       - Question 6
       - Question 7
       - Question 8
       - Question 11
       - Question 12
       - Question 13
       - Question 14
       - Question 15
       - Question 16
       - Question 17
       - Question 18
       - Question 19
       - Question 20

═══════════════════════════════════════════════════════════════════════════════

FINAL STEPS BEFORE RESUBMISSION
═══════════════════════════════════════════════════════════════════════════════

[ ] 1. Review all corrected sections

[ ] 2. Verify all required documents are attached

[ ] 3. Ensure IL SOS good standing is resolved

[ ] 4. Double-check ownership disclosure completeness

[ ] 5. Save application draft

[ ] 6. Submit corrected application

═══════════════════════════════════════════════════════════════════════════════
"""
        
        checklist_path = self.output_dir / f"IPG_Correction_Checklist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(checklist_path, 'w') as f:
            f.write(checklist)
        
        self.add_to_report(f"✓ Checklist generated: {checklist_path}")
        return str(checklist_path)
    
    def save_report(self) -> str:
        """Save the processing report to a file"""
        report_path = self.output_dir / f"IPG_Fix_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_path, 'w') as f:
            f.write('\n'.join(self.report))
        print(f"\n✓ Report saved to: {report_path}")
        return str(report_path)


def main():
    """Main execution function"""
    print("=" * 80)
    print("IPG APPLICATION FIX SCRIPT")
    print("=" * 80)
    print()
    
    # Configuration
    company_name = input("Enter company name: ").strip() or "AS Peoria"
    is_manufacturer = input("Is this a manufacturing business? (y/n): ").strip().lower() == 'y'
    docs_path = input("Enter path to tax documents directory (or press Enter to skip): ").strip()
    
    # Initialize fixer
    fixer = IPGApplicationFixer(company_name)
    
    # Check documents if path provided
    if docs_path:
        fixer.check_question_c1_documents(docs_path)
    else:
        fixer.add_to_report("⚠ Document check skipped - no path provided", "WARNING")
    
    print()
    
    # Check IL SOS status
    fixer.check_illinois_sos_status()
    print()
    
    # Check ownership disclosure requirements
    print("Enter owner information (press Enter on name to finish):")
    owners = []
    while True:
        name = input("  Owner name: ").strip()
        if not name:
            break
        
        try:
            ownership_pct = float(input("    Ownership % (e.g., 25 for 25%): ") or 0)
            ownership_val = float(input("    Ownership value in $ (e.g., 50000): ") or 0)
            income_pct = float(input("    Distributive income % (e.g., 25 for 25%): ") or 0)
            income_val = float(input("    Distributive income value in $ (e.g., 75000): ") or 0)
            
            owners.append({
                'name': name,
                'ownership_percent': ownership_pct,
                'ownership_value': ownership_val,
                'distributive_income_percent': income_pct,
                'distributive_income_value': income_val
            })
        except ValueError:
            print("    Invalid input - owner skipped")
    
    if owners:
        disclosure_required, owners_to_disclose = fixer.calculate_ownership_disclosure(owners)
    else:
        fixer.add_to_report("⚠ Ownership check skipped - no owners provided", "WARNING")
    
    print()
    
    # Generate checklist
    checklist_path = fixer.generate_checklist(is_manufacturer)
    print(f"\n✓ Checklist saved to: {checklist_path}")
    
    # Save report
    report_path = fixer.save_report()
    
    print("\n" + "=" * 80)
    print("PROCESS COMPLETE")
    print("=" * 80)
    print(f"Report: {report_path}")
    print(f"Checklist: {checklist_path}")
    print("\nNext steps:")
    print("1. Review the generated checklist")
    print("2. Gather all required documents")
    print("3. Resolve IL SOS good standing issues")
    print("4. Complete ownership disclosure form if needed")
    print("5. Resubmit IPG application")


if __name__ == "__main__":
    main()
