#!/usr/bin/env python3
"""
Upload Phase 2B Test CSV to Content Processor API
"""
import urllib.request
import urllib.parse
import os
import json

def create_multipart_form_data(files, fields=None):
    """Create multipart form data"""
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    data = []
    
    if fields:
        for key, value in fields.items():
            data.append(f'--{boundary}'.encode())
            data.append(f'Content-Disposition: form-data; name="{key}"'.encode())
            data.append(b'')
            data.append(str(value).encode())
    
    for key, filepath in files.items():
        filename = os.path.basename(filepath)
        data.append(f'--{boundary}'.encode())
        data.append(f'Content-Disposition: form-data; name="{key}"; filename="{filename}"'.encode())
        data.append(f'Content-Type: text/csv'.encode())
        data.append(b'')
        
        with open(filepath, 'rb') as f:
            data.append(f.read())
    
    data.append(f'--{boundary}--'.encode())
    
    body = b'\r\n'.join(data)
    content_type = f'multipart/form-data; boundary={boundary}'
    
    return body, content_type

def upload_csv():
    csv_file = 'phase2b_test_questions.csv'
    url = 'http://localhost:8002/content/import/csv'
    
    if not os.path.exists(csv_file):
        print(f'❌ File not found: {csv_file}')
        return
    
    print(f'📁 Uploading: {csv_file}')
    
    try:
        # Create multipart form data
        body, content_type = create_multipart_form_data({'file': csv_file})
        
        # Create request
        req = urllib.request.Request(url, data=body)
        req.add_header('Content-Type', content_type)
        
        # Upload
        with urllib.request.urlopen(req, timeout=30) as response:
            result = response.read().decode()
            print(f'✅ Upload successful!')
            print(f'📤 Status: {response.status}')
            
            # Parse JSON response
            try:
                data = json.loads(result)
                print(f'📋 Operation ID: {data.get("operation_id")}')
                print(f'📄 Sheet ID: {data.get("sheet_id")}')
                print(f'🔢 Total Rows: {data.get("total_rows")}')
                return data.get("operation_id")
            except:
                print(f'📋 Response: {result}')
                
    except Exception as e:
        print(f'❌ Upload failed: {str(e)}')

if __name__ == '__main__':
    operation_id = upload_csv()
    if operation_id:
        print(f'\n🎯 Next: Check import status with: http://localhost:8002/content/import/status/{operation_id}')