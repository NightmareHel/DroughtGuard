"""
Upload DroughtGuard model artifacts to DigitalOcean Spaces.
"""

import os
import json
import glob
from datetime import datetime
from typing import List, Tuple, Dict, Any
import boto3
from botocore.exceptions import ClientError


def load_credentials() -> Tuple[str, str, str, str, str]:
    """Load DigitalOcean Spaces credentials from environment variables."""
    access_key = os.getenv('SPACES_ACCESS_KEY')
    secret_key = os.getenv('SPACES_SECRET_KEY')
    region = os.getenv('SPACES_REGION', 'nyc3')
    bucket = os.getenv('SPACES_BUCKET')
    endpoint_url = os.getenv('SPACES_ENDPOINT_URL')
    
    if not all([access_key, secret_key, bucket]):
        print("ERROR: Missing required environment variables!")
        print("   Required:")
        print("     - SPACES_ACCESS_KEY")
        print("     - SPACES_SECRET_KEY")
        print("     - SPACES_BUCKET")
        print("   Optional:")
        print("     - SPACES_REGION (default: nyc3)")
        print("     - SPACES_ENDPOINT_URL (auto-generated if not provided)")
        return None
    
    # Generate endpoint URL if not provided
    if not endpoint_url:
        endpoint_url = f"https://{region}.digitaloceanspaces.com"
    
    return access_key, secret_key, region, bucket, endpoint_url


def create_spaces_client(access_key: str, secret_key: str, endpoint_url: str) -> Any:
    """Create and return a DigitalOcean Spaces client."""
    session = boto3.session.Session()
    client = session.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )
    return client


def find_model_files() -> List[Tuple[str, str]]:
    """Find all model files to upload."""
    model_files = []
    
    # Look for model files with patterns
    patterns = [
        'model_h1*.pkl',
        'model_h2*.pkl', 
        'model_h3*.pkl',
        'metrics*.json'
    ]
    
    for pattern in patterns:
        matches = glob.glob(pattern)
        for match in matches:
            # Determine remote path
            if match.startswith('model_h'):
                horizon = match.split('_')[1].split('.')[0]  # Extract h1, h2, h3
                remote_path = f"models/{match}"
            elif match.startswith('metrics'):
                remote_path = f"models/{match}"
            else:
                remote_path = f"models/{match}"
            
            model_files.append((match, remote_path))
    
    return model_files


def upload_file(s3_client: Any, bucket: str, local_path: str, remote_path: str, 
                endpoint_url: str) -> Tuple[bool, str]:
    """Upload a file to Spaces."""
    try:
        s3_client.upload_file(local_path, bucket, remote_path)
        public_url = f"{endpoint_url}/{bucket}/{remote_path}"
        print(f"   [OK] {local_path} -> {remote_path}")
        print(f"        {public_url}")
        return True, public_url
    except ClientError as e:
        print(f"   [FAILED] {local_path}: {e}")
        return False, ""


def upload_forecasts(s3_client: Any, bucket: str, endpoint_url: str) -> Tuple[bool, str]:
    """Upload forecasts CSV file."""
    forecasts_path = "../data/forecasts.csv"
    if os.path.exists(forecasts_path):
        return upload_file(s3_client, bucket, forecasts_path, "data/forecasts.csv", endpoint_url)
    else:
        print(f"   [SKIP] {forecasts_path} (not found)")
        return False, ""


def create_upload_manifest(uploaded_files: List[Dict[str, str]]) -> None:
    """Create a manifest file with upload details."""
    manifest = {
        "timestamp": datetime.now().isoformat(),
        "uploaded_files": uploaded_files,
        "total_files": len(uploaded_files)
    }
    
    manifest_path = "upload_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"   [INFO] Created upload manifest: {manifest_path}")


def main():
    """Main upload function."""
    print("=" * 60)
    print("DroughtGuard Artifact Upload to DigitalOcean Spaces")
    print("=" * 60)
    
    # Load credentials
    creds = load_credentials()
    if not creds:
        return
    
    access_key, secret_key, region, bucket, endpoint_url = creds
    print(f"\nConnecting to bucket: {bucket}")
    print(f"Endpoint: {endpoint_url}")
    
    # Create client
    try:
        s3_client = create_spaces_client(access_key, secret_key, endpoint_url)
        print("   [OK] Connected to DigitalOcean Spaces")
    except Exception as e:
        print(f"   [FAILED] Connection failed: {e}")
        return
    
    # Find files to upload
    model_files = find_model_files()
    print(f"\nFound {len(model_files)} model files to upload")
    
    # Upload files
    print("\nUploading files...")
    uploaded_files = []
    success_count = 0
    
    # Upload model files
    for local_path, remote_path in model_files:
        if os.path.exists(local_path):
            success, url = upload_file(s3_client, bucket, local_path, remote_path, endpoint_url)
            if success:
                success_count += 1
                uploaded_files.append({
                    "local_path": local_path,
                    "remote_path": remote_path,
                    "url": url
                })
        else:
            print(f"   [SKIP] {local_path} (not found)")
    
    # Upload forecasts
    success, url = upload_forecasts(s3_client, bucket, endpoint_url)
    if success:
        success_count += 1
        uploaded_files.append({
            "local_path": "data/forecasts.csv",
            "remote_path": "data/forecasts.csv", 
            "url": url
        })
    
    # Create manifest
    create_upload_manifest(uploaded_files)
    
    print("\n" + "=" * 60)
    print(f"Upload complete! ({success_count} files uploaded)")
    print("=" * 60)
    
    # Print summary
    print("\nUploaded files:")
    for file_info in uploaded_files:
        print(f"   [OK] {file_info['local_path']}")
        print(f"     URL: {file_info['url']}")
    
    print(f"\nVerification:")
    print(f"   Visit: https://cloud.digitalocean.com/spaces")
    print(f"   Bucket: {bucket}")
    
    print(f"\nPublic URLs:")
    base_url = f"{endpoint_url}/{bucket}"
    print(f"   Models: {base_url}/models/")
    print(f"   Forecasts: {base_url}/data/forecasts.csv")
    print(f"   Manifest: {base_url}/model/upload_manifest.json")


if __name__ == '__main__':
    main()
