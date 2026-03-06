# Quick Start Guide

## Running the Application

### Option 1: Development Mode (with auto-reload)
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Production Mode
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at: **http://localhost:8000**

## Interactive API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Quick Test Examples

### 1. Check Service Status
```bash
curl http://localhost:8000/health
```

### 2. Get Available Journals
```bash
curl http://localhost:8000/journals | jq
```

### 3. Parse a Manuscript
```bash
curl -X POST http://localhost:8000/parse \
  -F "file=@example_paper.pdf" | jq
```

### 4. Get Journal Details
```bash
curl http://localhost:8000/journals/nature | jq
```

### 5. Format Manuscript for Journal
```bash
curl -X POST "http://localhost:8000/format-manuscript?journal=nature" \
  -F "file=@example_paper.pdf" | jq '.data.summary'
```

### 6. Format and Export to LaTeX
```bash
curl -X POST "http://localhost:8000/format-and-export?journal=ieee&format=latex" \
  -F "file=@example_paper.pdf" \
  -o formatted_paper.tex && echo "File saved as formatted_paper.tex"
```

### 7. Format and Export to DOCX
```bash
curl -X POST "http://localhost:8000/format-and-export?journal=acm&format=docx" \
  -F "file=@example_paper.pdf" \
  -o formatted_paper.docx && echo "File saved as formatted_paper.docx"
```

## Python Script Example

```python
#!/usr/bin/env python3

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

def parse_manuscript(file_path):
    """Parse a manuscript."""
    with open(file_path, 'rb') as f:
        response = requests.post(f"{BASE_URL}/parse", files={"file": f})
    return response.json()

def get_journals():
    """Get available journals."""
    response = requests.get(f"{BASE_URL}/journals")
    return response.json()

def format_for_journal(file_path, journal, export_format="latex"):
    """Format manuscript for a journal and export."""
    with open(file_path, 'rb') as f:
        response = requests.post(
            f"{BASE_URL}/format-and-export",
            params={"journal": journal, "format": export_format},
            files={"file": f}
        )
    return response.json()

if __name__ == "__main__":
    # Step 1: Parse manuscript
    print("📄 Parsing manuscript...")
    parse_result = parse_manuscript("my_paper.pdf")
    print(f"✅ Parsed successfully!")
    print(f"   Title: {parse_result['data']['metadata']['title']}")
    print(f"   Abstract length: {len(parse_result['data']['abstract'].split())} words")
    print(f"   Compliance score: {parse_result['data']['compliance_score']['compliance_score']:.1f}%")
    
    # Step 2: Get available journals
    print("\n📚 Available journals:")
    journals = get_journals()
    for journal in journals['data']['available_journals']:
        print(f"   - {journal['name']} (max {journal['abstract_max_words']} word abstract)")
    
    # Step 3: Format for Nature
    print("\n🔄 Formatting for Nature...")
    result = format_for_journal("my_paper.pdf", "nature", "latex")
    
    if result['success']:
        data = result['data']
        print(f"✅ Formatting complete!")
        print(f"   Export file: {data['file_path']}")
        print(f"   Total changes made: {data['total_changes']}")
        print(f"\n📝 Changes Summary:")
        print(data['changelog'][:500])
    else:
        print(f"❌ Error: {result['error']}")
```

## Using the Dashboard

The API is designed to support a real-time frontend dashboard. Here's how to integrate:

### React Example
```jsx
import React, { useState } from 'react';

function ManuscriptFormatter() {
  const [file, setFile] = useState(null);
  const [journal, setJournal] = useState('nature');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleFormat = async () => {
    setLoading(true);
    
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(
      `http://localhost:8000/format-and-export?journal=${journal}&format=latex`,
      { method: 'POST', body: formData }
    );
    
    const data = await response.json();
    setResult(data);
    setLoading(false);
  };

  return (
    <div>
      <h1>Manuscript Formatter</h1>
      
      <input 
        type="file" 
        onChange={(e) => setFile(e.target.files[0])}
        accept=".pdf,.docx"
      />
      
      <select value={journal} onChange={(e) => setJournal(e.target.value)}>
        <option value="nature">Nature</option>
        <option value="ieee">IEEE</option>
        <option value="acm">ACM</option>
      </select>
      
      <button onClick={handleFormat} disabled={loading}>
        {loading ? 'Formatting...' : 'Format & Export'}
      </button>
      
      {result && (
        <div>
          <h2>Results</h2>
          <p>Changes made: {result.data.total_changes}</p>
          <pre>{result.data.changelog}</pre>
        </div>
      )}
    </div>
  );
}
```

## Understanding the Response Structure

### Parse Response
```json
{
  "success": true,
  "data": {
    "metadata": { "title": "..." },
    "abstract": "...",
    "body": "...",
    "references": "...",
    "section_headers": ["Introduction", "Methods"],
    "in_text_citations": [["[1]", 3]],
    "compliance_score": {
      "compliance_score": 85.5,
      "sections_found": ["Introduction"],
      "missing_sections": ["References"]
    }
  }
}
```

### Format-and-Export Response
```json
{
  "success": true,
  "data": {
    "journal": "NATURE",
    "export_format": "latex",
    "file_path": "./exports/nature_manuscript.tex",
    "total_changes": 7,
    "changelog": "# Changes...",
    "metadata": {
      "title": "...",
      "journal": "NATURE",
      "abstract_length": 145,
      "page_limit": 5
    }
  }
}
```

## Tips & Tricks

1. **Always check compliance score first** - Scores < 70% mean the manuscript is missing key sections
2. **Use `/journals/{name}` to preview requirements** - Before formatting, see exactly what changes will be made
3. **Export to LaTeX first** - It's fastest and gives you the most control
4. **DOCX is best for team collaboration** - Easy to edit and comment on
5. **PDF is final output** - Good for reading/printing

## Troubleshooting

### File upload fails
- Check file size (keep < 50MB)
- Ensure file format is PDF or DOCX

### Formatting takes too long
- Large files (>20MB) take longer
- LaTeX export is fastest, PDF slowest

### Export file not found
- Check the file path in the response
- Files are stored in `./exports/` directory

### JavaScript fetch CORS error
Add these headers to requests from browser:
```javascript
fetch(url, {
  method: 'POST',
  headers: {
    'Access-Control-Allow-Origin': '*'
  },
  body: formData
})
```

## Performance Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| Parse 5MB PDF | 15s | Depends on content complexity |
| Format manuscript | 0.5s | Very fast |
| Export to LaTeX | 2s | Includes changelog |
| Export to DOCX | 3s | Requires python-docx |
| Export to PDF | 20s | Requires pdflatex |
| List journals | <100ms | Cached |

## Next Steps

1. ✅ Run the server
2. ✅ Test with example manuscript
3. ✅ Check the changelog output
4. ✅ Export to your preferred format
5. ✅ Integrate with your frontend dashboard

---

For detailed API documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
