#!/usr/bin/env python3
"""Fill out the Empire State Development PIW form using Autho.R RPA."""

import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

from rpa import RPA

# Initialize RPA
bot = RPA()

# Source and output paths
SOURCE_DOC = "/Users/_malcolmadams/projects/author-rpa/EMPIRE STATE DEVELOPMENT_PIW.docx"
OUTPUT_DOC = "/Users/_malcolmadams/projects/author-rpa/EMPIRE STATE DEVELOPMENT_PIW_FILLED.docx"

# Company information for Avid Solutions International
COMPANY_DATA = {
    # Basic Company Info
    "project_name": "Avid Solutions Intl - NY Precision Agriculture Innovation Hub",
    "legal_name": "Avid Solutions International, Inc.",
    "address": "3675 Crestwood Parkway NW, Suite 400, Duluth, GA 30096",
    "dba_name": "Avid Solutions Intl",
    "contact_name": "Malcolm Adams, CEO",
    "contact_address": "3675 Crestwood Parkway NW, Suite 400, Duluth, GA 30096",
    "contact_phone": "(404) 555-0100",
    "contact_email": "malcolm@aspeoria.net",
    "type_of_business": "Agricultural Technology / Precision Agriculture R&D / Software Development",

    # Tax & ID Numbers
    "naics_code": "541715",
    "naics_description": "Research and Development in Physical, Engineering, and Life Sciences",
    "federal_tax_id": "88-1234567",
    "duns_number": "123456789",
    "nys_ui_number": "To be obtained upon NY establishment",

    # Financials
    "annual_sales": "2,850,000",
    "percent_sold_in_state": "15",

    # Statement of Need
    "statement_of_need": """Avid Solutions International seeks ESD assistance to establish a Precision Agriculture Innovation Hub in Upstate New York. This facility will advance sustainable farming technologies including AI-driven soil analysis, automated irrigation systems, and carbon sequestration monitoring. The project addresses critical needs in NY's agricultural sector: improving farm productivity, reducing environmental impact, and creating high-tech jobs in rural communities. Our proprietary data management platform currently serves 10+ farms and this expansion will accelerate adoption across the Northeast region.""",

    # Project Information
    "project_description": """Establishment of a 25,000 sq ft R&D and operations facility combining laboratory space, data center infrastructure, and field testing coordination. The facility will develop precision agriculture solutions including: (1) IoT sensor networks for real-time crop monitoring, (2) AI/ML models for yield optimization, (3) Drone-based field mapping systems, (4) Carbon credit verification platforms. We will partner with SUNY agricultural programs and local farms for technology validation and workforce development.""",

    "project_address": "To be determined - evaluating locations in Albany, Syracuse, and Buffalo regions",
    "project_county": "Albany (primary consideration)",

    # R&D Activity
    "rd_activity": """Development of precision agriculture AI models, IoT sensor integration, drone mapping systems, soil health analytics, and carbon sequestration measurement technologies. Collaboration with Cornell AgriTech and SUNY research programs.""",

    # Timeline
    "first_project_year": "2025",
    "project_start_date": "Q2 2025",

    # Employment Projections
    "existing_jobs_nys": "0",
    "existing_jobs_nationwide": "12",

    # Job Categories and Salaries (Year 1 -> Year 5)
    "jobs": [
        {"title": "Software Engineers", "salary": "95,000", "y1": "3", "y2": "5", "y3": "7", "y4": "8", "y5": "10"},
        {"title": "Data Scientists", "salary": "105,000", "y1": "2", "y2": "3", "y3": "4", "y4": "5", "y5": "6"},
        {"title": "Agricultural Scientists", "salary": "75,000", "y1": "2", "y2": "3", "y3": "4", "y4": "5", "y5": "6"},
        {"title": "Field Technicians", "salary": "55,000", "y1": "3", "y2": "5", "y3": "8", "y4": "10", "y5": "12"},
        {"title": "Operations/Admin Staff", "salary": "50,000", "y1": "2", "y2": "3", "y3": "4", "y4": "5", "y5": "6"},
        {"title": "Sales/Business Development", "salary": "70,000", "y1": "1", "y2": "2", "y3": "3", "y4": "4", "y5": "5"},
    ],

    # Investment Budget
    "property_acquisition": "500,000",
    "construction_renovation": "1,200,000",
    "machinery_equipment": "850,000",
    "furniture_fixtures": "150,000",
    "training": "200,000",
    "design_planning": "100,000",
    "other_investment": "250,000",
    "other_description": "IT infrastructure, cloud computing setup, drone fleet",
    "total_investment": "3,250,000",

    # R&D Expenditures by Year
    "rd_y1": "400,000",
    "rd_y2": "600,000",
    "rd_y3": "800,000",
    "rd_y4": "950,000",
    "rd_y5": "1,100,000",

    # Real Property
    "own_property": "Lease with option to purchase",
    "current_property_tax": "N/A - New facility",
    "future_property_tax": "Estimated $45,000 annually after improvements",

    # Additional Info
    "benefits_percentage": "85",
    "nys_resident_percentage": "90",
    "veteran_percentage": "10",

    # Completion Info
    "official_name": "Malcolm Adams",
    "official_title": "Chief Executive Officer",
    "completion_date": "December 14, 2025",
}

# ============================================================
# TABLE 0: Company Information (26 rows x 9 cols)
# ============================================================
table0_mappings = [
    # Project Name (row 0, col 2+)
    {"table": 0, "row": 0, "col": 2, "value": COMPANY_DATA["project_name"]},

    # 1. Legal Name of Applicant (row 2, col 2+)
    {"table": 0, "row": 2, "col": 2, "value": COMPANY_DATA["legal_name"]},

    # 2. Applicant Address (row 3, col 2+)
    {"table": 0, "row": 3, "col": 2, "value": COMPANY_DATA["address"]},

    # 3. DBA Name (row 4, col 2+)
    {"table": 0, "row": 4, "col": 2, "value": COMPANY_DATA["dba_name"]},

    # 4. Applicant Contact Name (row 5, col 2+)
    {"table": 0, "row": 5, "col": 2, "value": COMPANY_DATA["contact_name"]},

    # 5. Applicant Contact Address (row 6, col 2+)
    {"table": 0, "row": 6, "col": 2, "value": COMPANY_DATA["contact_address"]},

    # 6. Contact Phone Number (row 7, col 2)
    {"table": 0, "row": 7, "col": 2, "value": COMPANY_DATA["contact_phone"]},

    # 6. Contact Email Address (row 7, col 7+)
    {"table": 0, "row": 7, "col": 7, "value": COMPANY_DATA["contact_email"]},

    # 7. Type of Business (row 8, col 2+)
    {"table": 0, "row": 8, "col": 2, "value": COMPANY_DATA["type_of_business"]},

    # 8. Publicly Traded - NO (row 9, col 4 for NO)
    {"table": 0, "row": 9, "col": 4, "value": "X"},

    # 9. Privately Held - YES (row 10, col 2 for YES)
    {"table": 0, "row": 10, "col": 2, "value": "X"},

    # 10. Start-up company - NO (row 12, col 8 for NO)
    {"table": 0, "row": 12, "col": 8, "value": "X"},

    # 12. Primary NAICS Code (row 15, col 8)
    {"table": 0, "row": 15, "col": 8, "value": COMPANY_DATA["naics_code"]},

    # 13. NAICS Description (row 16, col 8)
    {"table": 0, "row": 16, "col": 8, "value": COMPANY_DATA["naics_description"]},

    # 14. Federal Tax ID (row 19, col 8)
    {"table": 0, "row": 19, "col": 8, "value": COMPANY_DATA["federal_tax_id"]},

    # 14. DUNS Number (row 19, col 3)
    {"table": 0, "row": 19, "col": 3, "value": COMPANY_DATA["duns_number"]},

    # 14. NYS Unemployment Insurance Tax Number (row 20, col 3)
    {"table": 0, "row": 20, "col": 3, "value": COMPANY_DATA["nys_ui_number"]},

    # 15. Company's Annual Sales (row 21, col 4)
    {"table": 0, "row": 21, "col": 4, "value": COMPANY_DATA["annual_sales"]},

    # 16. Percent sold within state (row 22, col 7)
    {"table": 0, "row": 22, "col": 7, "value": COMPANY_DATA["percent_sold_in_state"]},

    # 17. Statement of Need (row 25, col 1)
    {"table": 0, "row": 25, "col": 1, "value": COMPANY_DATA["statement_of_need"]},
]

# ============================================================
# TABLE 1: Project Information (28 rows x 20 cols)
# ============================================================
table1_mappings = [
    # 18. Project Description (row 2, col 1)
    {"table": 1, "row": 2, "col": 1, "value": COMPANY_DATA["project_description"]},

    # 19. Project Address (row 3, col 3)
    {"table": 1, "row": 3, "col": 3, "value": COMPANY_DATA["project_address"]},

    # 20. Distressed Location - TBD (row 4)
    {"table": 1, "row": 4, "col": 3, "value": "TBD"},

    # 21. Project County (row 5, col 3)
    {"table": 1, "row": 5, "col": 3, "value": COMPANY_DATA["project_county"]},

    # 24. Primary Activity - Check Agriculture and Software Development
    {"table": 1, "row": 10, "col": 4, "value": "X"},  # Agriculture
    {"table": 1, "row": 13, "col": 4, "value": "X"},  # Software Development & New Media

    # 25. First project year (row 14, col 3)
    {"table": 1, "row": 14, "col": 3, "value": COMPANY_DATA["first_project_year"]},

    # 26. Estimated Project Start Date (row 15, col 3)
    {"table": 1, "row": 15, "col": 3, "value": COMPANY_DATA["project_start_date"]},

    # 27. Seeking incentives from other states - NO (row 16)
    {"table": 1, "row": 16, "col": 10, "value": "X"},  # NO

    # 28. R&D Activity (row 20, col 1)
    {"table": 1, "row": 20, "col": 1, "value": COMPANY_DATA["rd_activity"]},

    # 29. R&D Expenditures by Year (row 23)
    {"table": 1, "row": 23, "col": 4, "value": COMPANY_DATA["rd_y1"]},
    {"table": 1, "row": 23, "col": 6, "value": COMPANY_DATA["rd_y2"]},
    {"table": 1, "row": 23, "col": 8, "value": COMPANY_DATA["rd_y3"]},
    {"table": 1, "row": 23, "col": 10, "value": COMPANY_DATA["rd_y4"]},
    {"table": 1, "row": 23, "col": 12, "value": COMPANY_DATA["rd_y5"]},

    # 30. Own property - Lease (row 25)
    {"table": 1, "row": 25, "col": 10, "value": COMPANY_DATA["own_property"]},

    # 31. Current property tax (row 26)
    {"table": 1, "row": 26, "col": 10, "value": COMPANY_DATA["current_property_tax"]},

    # 32. Future property tax (row 27)
    {"table": 1, "row": 27, "col": 10, "value": COMPANY_DATA["future_property_tax"]},
]

# ============================================================
# TABLE 2: Employment & Budget (44 rows x 19 cols)
# ============================================================
table2_mappings = [
    # 33. Existing Jobs in NYS (row 4, col 4)
    {"table": 2, "row": 4, "col": 4, "value": COMPANY_DATA["existing_jobs_nys"]},

    # 34. Existing Jobs Nationwide (row 7, col 4)
    {"table": 2, "row": 7, "col": 4, "value": COMPANY_DATA["existing_jobs_nationwide"]},

    # 35. New Jobs by Category (rows 13-18)
    # Job 1: Software Engineers
    {"table": 2, "row": 13, "col": 1, "value": COMPANY_DATA["jobs"][0]["title"]},
    {"table": 2, "row": 13, "col": 3, "value": COMPANY_DATA["jobs"][0]["salary"]},
    {"table": 2, "row": 13, "col": 5, "value": COMPANY_DATA["jobs"][0]["y1"]},
    {"table": 2, "row": 13, "col": 7, "value": COMPANY_DATA["jobs"][0]["y2"]},
    {"table": 2, "row": 13, "col": 9, "value": COMPANY_DATA["jobs"][0]["y3"]},
    {"table": 2, "row": 13, "col": 11, "value": COMPANY_DATA["jobs"][0]["y4"]},
    {"table": 2, "row": 13, "col": 13, "value": COMPANY_DATA["jobs"][0]["y5"]},

    # Job 2: Data Scientists
    {"table": 2, "row": 14, "col": 1, "value": COMPANY_DATA["jobs"][1]["title"]},
    {"table": 2, "row": 14, "col": 3, "value": COMPANY_DATA["jobs"][1]["salary"]},
    {"table": 2, "row": 14, "col": 5, "value": COMPANY_DATA["jobs"][1]["y1"]},
    {"table": 2, "row": 14, "col": 7, "value": COMPANY_DATA["jobs"][1]["y2"]},
    {"table": 2, "row": 14, "col": 9, "value": COMPANY_DATA["jobs"][1]["y3"]},
    {"table": 2, "row": 14, "col": 11, "value": COMPANY_DATA["jobs"][1]["y4"]},
    {"table": 2, "row": 14, "col": 13, "value": COMPANY_DATA["jobs"][1]["y5"]},

    # Job 3: Agricultural Scientists
    {"table": 2, "row": 15, "col": 1, "value": COMPANY_DATA["jobs"][2]["title"]},
    {"table": 2, "row": 15, "col": 3, "value": COMPANY_DATA["jobs"][2]["salary"]},
    {"table": 2, "row": 15, "col": 5, "value": COMPANY_DATA["jobs"][2]["y1"]},
    {"table": 2, "row": 15, "col": 7, "value": COMPANY_DATA["jobs"][2]["y2"]},
    {"table": 2, "row": 15, "col": 9, "value": COMPANY_DATA["jobs"][2]["y3"]},
    {"table": 2, "row": 15, "col": 11, "value": COMPANY_DATA["jobs"][2]["y4"]},
    {"table": 2, "row": 15, "col": 13, "value": COMPANY_DATA["jobs"][2]["y5"]},

    # Job 4: Field Technicians
    {"table": 2, "row": 16, "col": 1, "value": COMPANY_DATA["jobs"][3]["title"]},
    {"table": 2, "row": 16, "col": 3, "value": COMPANY_DATA["jobs"][3]["salary"]},
    {"table": 2, "row": 16, "col": 5, "value": COMPANY_DATA["jobs"][3]["y1"]},
    {"table": 2, "row": 16, "col": 7, "value": COMPANY_DATA["jobs"][3]["y2"]},
    {"table": 2, "row": 16, "col": 9, "value": COMPANY_DATA["jobs"][3]["y3"]},
    {"table": 2, "row": 16, "col": 11, "value": COMPANY_DATA["jobs"][3]["y4"]},
    {"table": 2, "row": 16, "col": 13, "value": COMPANY_DATA["jobs"][3]["y5"]},

    # Job 5: Operations/Admin
    {"table": 2, "row": 17, "col": 1, "value": COMPANY_DATA["jobs"][4]["title"]},
    {"table": 2, "row": 17, "col": 3, "value": COMPANY_DATA["jobs"][4]["salary"]},
    {"table": 2, "row": 17, "col": 5, "value": COMPANY_DATA["jobs"][4]["y1"]},
    {"table": 2, "row": 17, "col": 7, "value": COMPANY_DATA["jobs"][4]["y2"]},
    {"table": 2, "row": 17, "col": 9, "value": COMPANY_DATA["jobs"][4]["y3"]},
    {"table": 2, "row": 17, "col": 11, "value": COMPANY_DATA["jobs"][4]["y4"]},
    {"table": 2, "row": 17, "col": 13, "value": COMPANY_DATA["jobs"][4]["y5"]},

    # Job 6: Sales/Business Development
    {"table": 2, "row": 18, "col": 1, "value": COMPANY_DATA["jobs"][5]["title"]},
    {"table": 2, "row": 18, "col": 3, "value": COMPANY_DATA["jobs"][5]["salary"]},
    {"table": 2, "row": 18, "col": 5, "value": COMPANY_DATA["jobs"][5]["y1"]},
    {"table": 2, "row": 18, "col": 7, "value": COMPANY_DATA["jobs"][5]["y2"]},
    {"table": 2, "row": 18, "col": 9, "value": COMPANY_DATA["jobs"][5]["y3"]},
    {"table": 2, "row": 18, "col": 11, "value": COMPANY_DATA["jobs"][5]["y4"]},
    {"table": 2, "row": 18, "col": 13, "value": COMPANY_DATA["jobs"][5]["y5"]},

    # Total Jobs (row 19) - Y5 total = 45
    {"table": 2, "row": 19, "col": 13, "value": "45"},

    # 36. Benefits percentage (row 20)
    {"table": 2, "row": 20, "col": 10, "value": COMPANY_DATA["benefits_percentage"]},

    # 37. NYS resident percentage (row 21)
    {"table": 2, "row": 21, "col": 10, "value": COMPANY_DATA["nys_resident_percentage"]},

    # 38. Veteran percentage (row 22)
    {"table": 2, "row": 22, "col": 10, "value": COMPANY_DATA["veteran_percentage"]},

    # 39. Project Budget
    # Property Acquisition (row 26)
    {"table": 2, "row": 26, "col": 5, "value": COMPANY_DATA["property_acquisition"]},

    # Construction/Renovation (row 27)
    {"table": 2, "row": 27, "col": 5, "value": COMPANY_DATA["construction_renovation"]},

    # Machinery & Equipment (row 28)
    {"table": 2, "row": 28, "col": 5, "value": COMPANY_DATA["machinery_equipment"]},

    # Furniture, Fixtures & Equipment (row 29)
    {"table": 2, "row": 29, "col": 5, "value": COMPANY_DATA["furniture_fixtures"]},

    # Training (row 30)
    {"table": 2, "row": 30, "col": 5, "value": COMPANY_DATA["training"]},

    # Design & Planning (row 31)
    {"table": 2, "row": 31, "col": 5, "value": COMPANY_DATA["design_planning"]},

    # Other (row 32)
    {"table": 2, "row": 32, "col": 3, "value": COMPANY_DATA["other_description"]},
    {"table": 2, "row": 32, "col": 5, "value": COMPANY_DATA["other_investment"]},

    # Total Investment (row 33)
    {"table": 2, "row": 33, "col": 5, "value": COMPANY_DATA["total_investment"]},

    # 40. Learn more about incentives - YES (row 36)
    {"table": 2, "row": 36, "col": 10, "value": "X"},

    # 41. R&D Tax Credit - YES (row 38)
    {"table": 2, "row": 38, "col": 10, "value": "X"},

    # 42. Health insurance - YES (row 39)
    {"table": 2, "row": 39, "col": 10, "value": "X"},

    # 43. Learn about exporting - YES (row 40)
    {"table": 2, "row": 40, "col": 10, "value": "X"},

    # Worksheet Completion (row 42)
    {"table": 2, "row": 42, "col": 3, "value": COMPANY_DATA["official_name"]},
    {"table": 2, "row": 42, "col": 8, "value": COMPANY_DATA["official_title"]},
    {"table": 2, "row": 42, "col": 13, "value": COMPANY_DATA["completion_date"]},
]

# Combine all mappings
all_mappings = table0_mappings + table1_mappings + table2_mappings


def main():
    """Fill out the ESD form."""
    print("=" * 70)
    print("Autho.R RPA - Empire State Development PIW Form Filler")
    print("=" * 70)

    print(f"\nSource document: {SOURCE_DOC}")
    print(f"Output document: {OUTPUT_DOC}")
    print(f"Total fields to fill: {len(all_mappings)}")

    # Check if source exists
    if not Path(SOURCE_DOC).exists():
        print(f"\nERROR: Source document not found: {SOURCE_DOC}")
        return 1

    # Fill the form
    print("\nFilling form fields...")
    try:
        result = bot.docs.fill_form(
            doc_path=SOURCE_DOC,
            output_path=OUTPUT_DOC,
            field_mappings=all_mappings
        )
        print(f"\nSUCCESS: Form filled and saved to:\n{result}")

        # Summary
        print("\n" + "=" * 70)
        print("FORM SUMMARY")
        print("=" * 70)

        print("\n[COMPANY INFORMATION]")
        print(f"  Project: {COMPANY_DATA['project_name']}")
        print(f"  Company: {COMPANY_DATA['legal_name']}")
        print(f"  Contact: {COMPANY_DATA['contact_name']}")
        print(f"  Email:   {COMPANY_DATA['contact_email']}")
        print(f"  Phone:   {COMPANY_DATA['contact_phone']}")

        print("\n[FINANCIALS]")
        print(f"  Annual Sales:      ${COMPANY_DATA['annual_sales']}")
        print(f"  Total Investment:  ${COMPANY_DATA['total_investment']}")
        print(f"  NAICS Code:        {COMPANY_DATA['naics_code']}")

        print("\n[EMPLOYMENT PROJECTIONS (5-Year)]")
        total_y5 = sum(int(j["y5"]) for j in COMPANY_DATA["jobs"])
        print(f"  Existing Jobs (Nationwide): {COMPANY_DATA['existing_jobs_nationwide']}")
        print(f"  New Jobs by Year 5:         {total_y5}")
        for job in COMPANY_DATA["jobs"]:
            print(f"    - {job['title']}: {job['y5']} positions @ ${job['salary']}/yr")

        print("\n[R&D EXPENDITURES]")
        print(f"  Year 1: ${COMPANY_DATA['rd_y1']}")
        print(f"  Year 2: ${COMPANY_DATA['rd_y2']}")
        print(f"  Year 3: ${COMPANY_DATA['rd_y3']}")
        print(f"  Year 4: ${COMPANY_DATA['rd_y4']}")
        print(f"  Year 5: ${COMPANY_DATA['rd_y5']}")

        print("\n[PROJECT BUDGET]")
        print(f"  Property Acquisition:    ${COMPANY_DATA['property_acquisition']}")
        print(f"  Construction/Renovation: ${COMPANY_DATA['construction_renovation']}")
        print(f"  Machinery & Equipment:   ${COMPANY_DATA['machinery_equipment']}")
        print(f"  Training:                ${COMPANY_DATA['training']}")
        print(f"  Other (IT/Cloud/Drones): ${COMPANY_DATA['other_investment']}")
        print(f"  TOTAL:                   ${COMPANY_DATA['total_investment']}")

        print("\n" + "=" * 70)
        print("Form completed successfully!")
        print("=" * 70)

        return 0

    except Exception as e:
        print(f"\nERROR: Failed to fill form: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
