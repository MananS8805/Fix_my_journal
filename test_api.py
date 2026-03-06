#!/usr/bin/env python3
"""
Test script for Manuscript Formatting Agent API
"""

import requests
import json
import time
import sys
from pathlib import Path

BASE_URL = "http://localhost:8001"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_journals():
    """Test journals endpoint"""
    print("📚 Testing journals endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/journals", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                journals = data['data']['available_journals']
                print(f"✅ Found {len(journals)} journals:")
                for journal in journals:
                    print(f"   - {journal['name']} ({journal['id']})")
                return True
            else:
                print(f"❌ Journals request failed: {data['error']}")
                return False
        else:
            print(f"❌ Journals request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Journals test failed: {e}")
        return False

def test_journal_details(journal_id):
    """Test journal details endpoint"""
    print(f"📋 Testing journal details for {journal_id}...")
    try:
        response = requests.get(f"{BASE_URL}/journals/{journal_id}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                profile = data['data']
                print(f"✅ {profile['name']} profile:")
                print(f"   - Abstract max: {profile['abstract_max_words']} words")
                print(f"   - Citation style: {profile['reference_style']}")
                print(f"   - Page limit: {profile.get('page_limit', 'Unlimited')}")
                return True
            else:
                print(f"❌ Journal details failed: {data['error']}")
                return False
        else:
            print(f"❌ Journal details failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Journal details test failed: {e}")
        return False

def create_sample_manuscript():
    """Create a sample manuscript for testing"""
    print("📝 Using existing sample PDF manuscript...")

    pdf_path = "exports/sample_manuscript.pdf"
    if Path(pdf_path).exists():
        print(f"✅ Using existing PDF: {pdf_path}")
        return pdf_path
    else:
        print("❌ Sample PDF not found. Run create_sample_pdf.py first.")
        return None

def test_parse_manuscript(file_path):
    """Test parse endpoint"""
    print("📄 Testing parse endpoint...")

    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return False

    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{BASE_URL}/parse", files=files, timeout=30)

        if response.status_code == 200:
            data = response.json()
            if data['success']:
                result = data['data']
                print("✅ Parse successful:")
                print(f"   - Title: {result['metadata']['title']}")
                print(f"   - Abstract: {len(result['abstract'].split())} words")
                print(f"   - Body: {len(result['body'].split())} words")
                print(f"   - References: {len(result['references'].split())} words")
                print(f"   - Section headers: {', '.join(result['section_headers'])}")
                print(f"   - Compliance score: {result['compliance_score']['compliance_score']:.1f}%")
                return True
            else:
                print(f"❌ Parse failed: {data['error']}")
                return False
        else:
            print(f"❌ Parse request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Parse test failed: {e}")
        return False

def test_format_manuscript(file_path, journal_id):
    """Test format-manuscript endpoint"""
    print(f"🔄 Testing format-manuscript for {journal_id}...")

    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return False

    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            params = {'journal': journal_id}
            response = requests.post(
                f"{BASE_URL}/format-manuscript",
                files=files,
                params=params,
                timeout=30
            )

        if response.status_code == 200:
            data = response.json()
            if data['success']:
                result = data['data']
                print("✅ Format successful:")
                print(f"   - Journal: {result['journal']}")
                print(f"   - Changes: {len(result['formatted']['changelog'])}")
                print("   - Summary preview:")
                summary = result['summary'][:200] + "..."
                print(f"     {summary}")
                return True
            else:
                print(f"❌ Format failed: {data['error']}")
                return False
        else:
            print(f"❌ Format request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Format test failed: {e}")
        return False

def test_format_and_export(file_path, journal_id, export_format="latex"):
    """Test format-and-export endpoint"""
    print(f"📤 Testing format-and-export for {journal_id} ({export_format})...")

    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return False

    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            params = {'journal': journal_id, 'format': export_format}
            response = requests.post(
                f"{BASE_URL}/format-and-export",
                files=files,
                params=params,
                timeout=60
            )

        if response.status_code == 200:
            data = response.json()
            if data['success']:
                result = data['data']
                print("✅ Format & Export successful:")
                print(f"   - Journal: {result['journal']}")
                print(f"   - Format: {result['export_format']}")
                print(f"   - File: {result['file_path']}")
                print(f"   - Total changes: {result['total_changes']}")
                print(f"   - Abstract length: {result['metadata']['abstract_length']} words")
                print(f"   - Changelog items: {len(result['changelog'])}")
                # preview markdown if available
                if 'changelog_markdown' in result:
                    preview = result['changelog_markdown'][:300] + "..."
                    print("   - Changelog preview:")
                    print(f"     {preview}")
                return True
            else:
                print(f"❌ Format & Export failed: {data['error']}")
                return False
        else:
            print(f"❌ Format & Export request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Format & Export test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Manuscript Formatting Agent - API Tests")
    print("=" * 50)

    # Test 1: Health check
    if not test_health():
        print("❌ Server not responding. Please start the server first:")
        print("   python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001")
        return

    # Test 2: Journals list
    if not test_journals():
        return

    # Test 3: Journal details
    if not test_journal_details("nature"):
        return

    # Test 4: Create sample manuscript
    sample_file = create_sample_manuscript()

    # Test 5: Parse manuscript
    if not test_parse_manuscript(sample_file):
        return

    # Test 6: Format manuscript
    if not test_format_manuscript(sample_file, "nature"):
        return

    # Test 7: Format and export
    if not test_format_and_export(sample_file, "ieee", "latex"):
        return

    print("\n" + "=" * 50)
    print("🎉 All tests passed! API is working correctly.")
    print("\n📁 Check the 'exports/' directory for generated files.")
    print("🌐 Visit http://localhost:8001/docs for interactive API docs.")

if __name__ == "__main__":
    main()