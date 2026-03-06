"""
Example usage of the Manuscript Formatting Agent API.
This script demonstrates the full workflow: parse -> list journals -> format -> export.
"""

import requests
import json
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"

def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_service_health():
    """Check if the API service is running."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print("✅ Service is healthy and running")
        return True
    except requests.ConnectionError:
        print("❌ Cannot connect to service at " + BASE_URL)
        print("   Start the server with: cd backend && uvicorn main:app --reload")
        return False

def parse_manuscript(file_path):
    """Parse a manuscript file."""
    print_header("Step 1: Parse Manuscript")
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return None
    
    print(f"📄 Parsing: {file_path}")
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/parse", files=files)
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            data = result['data']
            print(f"✅ Parsing complete!\n")
            print(f"   Title: {data['metadata']['title']}")
            print(f"   Abstract: {len(data['abstract'].split())} words")
            print(f"   Body: {len(data['body'].split())} words")
            print(f"   References: {len(data['references'].split())} words")
            print(f"\n   Section Headers Found: {', '.join(data['section_headers'])}")
            print(f"\n   Compliance Score: {data['compliance_score']['compliance_score']:.1f}%")
            print(f"   Sections Found: {', '.join(data['compliance_score']['sections_found'])}")
            print(f"   Missing Sections: {', '.join(data['compliance_score']['missing_sections'])}")
            print(f"\n   In-text Citations: {json.dumps(data['in_text_citations'], indent=6)}")
            return data
        else:
            print(f"❌ Parsing failed: {result['error']}")
            return None
    else:
        print(f"❌ Request failed with status {response.status_code}")
        return None

def list_available_journals():
    """List all available journals."""
    print_header("Step 2: Available Journals")
    
    response = requests.get(f"{BASE_URL}/journals")
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            data = result['data']
            print(f"📚 Available Journals: {data['total_journals']}\n")
            
            for journal in data['available_journals']:
                print(f"   📖 {journal['name']}")
                print(f"      ID: {journal['id']}")
                print(f"      Abstract Max: {journal['abstract_max_words']} words")
                print(f"      Citation Style: {journal['citation_style']}")
                if journal['page_limit']:
                    print(f"      Page Limit: {journal['page_limit']}")
                print()
            
            return [j['id'] for j in data['available_journals']]
        else:
            print(f"❌ Failed to get journals: {result['error']}")
            return []
    else:
        print(f"❌ Request failed with status {response.status_code}")
        return []

def format_manuscript(file_path, journal_name):
    """Format a manuscript for a specific journal."""
    print_header(f"Step 3: Format for {journal_name.upper()}")
    
    print(f"🔄 Formatting manuscript for {journal_name.upper()}...")
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        params = {'journal': journal_name}
        response = requests.post(
            f"{BASE_URL}/format-manuscript",
            files=files,
            params=params
        )
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            data = result['data']
            print(f"\n✅ Formatting complete!\n")
            print(f"   Journal: {data['journal']}")
            print(f"\n📝 Summary:")
            print(data['summary'])
            return data
        else:
            print(f"❌ Formatting failed: {result['error']}")
            return None
    else:
        print(f"❌ Request failed with status {response.status_code}")
        print(f"   {response.text}")
        return None

def export_manuscript(file_path, journal_name, export_format="latex"):
    """Format and export a manuscript."""
    print_header(f"Step 4: Format & Export (Format: {export_format.upper()})")
    
    print(f"📤 Exporting to {export_format.upper()}...")
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        params = {
            'journal': journal_name,
            'format': export_format
        }
        response = requests.post(
            f"{BASE_URL}/format-and-export",
            files=files,
            params=params
        )
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            data = result['data']
            print(f"\n✅ Export complete!\n")
            print(f"   Journal: {data['journal']}")
            print(f"   Format: {data['export_format'].upper()}")
            print(f"   File: {data['file_path']}")
            print(f"   Total Changes: {data['total_changes']}")
            print(f"   Abstract Length: {data['metadata']['abstract_length']} words")
            print(f"\n📊 Changelog Summary:")
            changelog = data['changelog']
            # Print first 500 chars of changelog
            print(changelog[:800])
            if len(changelog) > 800:
                print(f"\n   ... (truncated, see file for full changelog)")
            return data
        else:
            print(f"❌ Export failed: {result['error']}")
            return None
    else:
        print(f"❌ Request failed with status {response.status_code}")
        print(f"   {response.text}")
        return None

def get_journal_details(journal_name):
    """Get detailed profile for a journal."""
    print_header(f"Step 2b: Journal Details - {journal_name.upper()}")
    
    response = requests.get(f"{BASE_URL}/journals/{journal_name}")
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            profile = result['data']
            print(f"📋 {profile['name']} Profile:\n")
            print(f"   Font: {profile['font']}")
            print(f"   Font Size: {profile['font_size']}pt")
            print(f"   Line Spacing: {profile['line_spacing']}")
            print(f"   Margins: {profile['margins']}")
            print(f"   Abstract Max: {profile['abstract_max_words']} words")
            print(f"   Citation Style: {profile['reference_style']}")
            print(f"   Keywords Required: {profile['keywords']}")
            print(f"   Structure: {', '.join(profile['structure'][:3])}...")
            print(f"   DOI Required: {profile['doi_required']}")
            print(f"   Page Limit: {profile.get('page_limit', 'Unlimited')}")
            print(f"   Supplementary Info: {profile['supplementary_info']}")
            return profile
        else:
            print(f"❌ Failed to get journal details: {result['error']}")
            return None
    else:
        print(f"❌ Request failed with status {response.status_code}")
        return None

def main():
    """Main workflow demonstration."""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   Manuscript Formatting Agent - Example Workflow            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    # Check if service is running
    if not check_service_health():
        return
    
    # Example workflow
    print("\n🎯 Running example workflow...\n")
    
    # For demonstration, we'll use a placeholder file path
    # In real usage, replace with actual manuscript file
    example_file = "example_paper.pdf"
    
    print("📝 NOTE: This example uses a placeholder file path.")
    print(f"   Replace '{example_file}' with your actual manuscript file.")
    print("   Supported formats: PDF (.pdf), Word (.docx)\n")
    
    files_to_check = ["../../example_paper.pdf", "../example_paper.pdf", "./example_paper.pdf"]
    file_found = False
    
    for potential_file in files_to_check:
        if Path(potential_file).exists():
            example_file = potential_file
            file_found = True
            break
    
    if not file_found:
        print_header("Demo Mode - Simulating API Calls")
        print("To run with actual file, provide a manuscript and update the file path.\n")
    else:
        print_header("Real Workflow Starting")
        
        # Step 1: Parse
        parsed_data = parse_manuscript(example_file)
        if not parsed_data:
            return
        
        # Step 2: List journals
        journals = list_available_journals()
        if not journals:
            return
        
        # Step 2b: Get details for first journal
        get_journal_details(journals[0])
        
        # Step 3: Format for first journal
        format_manuscript(example_file, journals[0])
        
        # Step 4: Export
        export_manuscript(example_file, journals[0], "latex")
        
        print_header("✅ Workflow Complete!")
        print("The formatted manuscript has been exported.")
        print(f"Check the 'exports/' directory for your files.\n")

if __name__ == "__main__":
    main()
