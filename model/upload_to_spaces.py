"""
Upload DroughtGuard model artifacts to DigitalOcean Spaces
"""
import os
import boto3
from botocore.exceptions import ClientError


def load_credentials():
    """Load DigitalOcean Spaces credentials from environment variables."""
    access_key = os.getenv('SPACES_ACCESS_KEY')
    secret_key = os.getenv('SPACES_SECRET_KEY')
    region = os.getenv('SPACES_REGION', 'nyc3')
    bucket = os.getenv('SPACES_BUCKET')
    
    if not all([access_key, secret_key, bucket]):
        print("ERROR: Missing required environment variables!")
        print("   Required:")
        print("     - SPACES_ACCESS_KEY")
        print("     - SPACES_SECRET_KEY")
        print("     - SPACES_BUCKET")
        print("   Optional:")
        print("     - SPACES_REGION (default: nyc3)")
        return None
    
    return access_key, secret_key, region, bucket


def create_spaces_client(access_key, secret_key, region):
    """Create and return a DigitalOcean Spaces client."""
    session = boto3.session.Session()
    client = session.client(
        's3',
        region_name=region,
        endpoint_url=f'https://{region}.digitaloceanspaces.com',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )
    return client


def upload_file(s3_client, bucket, local_path, remote_path, region):
    """Upload a file to Spaces."""
    try:
        s3_client.upload_file(local_path, bucket, remote_path)
        endpoint_url = f"https://{region}.digitaloceanspaces.com"
        public_url = f"{endpoint_url}/{bucket}/{remote_path}"
        print(f"   [OK] {local_path} -> {remote_path}")
        print(f"        {public_url}")
        return True
    except ClientError as e:
        print(f"   [FAILED] {local_path}: {e}")
        return False


def main():
    """Main upload function."""
    print("=" * 60)
    print("DroughtGuard Artifact Upload to DigitalOcean Spaces")
    print("=" * 60)
    
    # Load credentials
    creds = load_credentials()
    if not creds:
        return
    
    access_key, secret_key, region, bucket = creds
    print(f"\nConnecting to bucket: {bucket} (region: {region})")
    
    # Create client
    try:
        s3_client = create_spaces_client(access_key, secret_key, region)
        print("   [OK] Connected to DigitalOcean Spaces")
    except Exception as e:
        print(f"   [FAILED] Connection failed: {e}")
        return
    
    # Files to upload
    files_to_upload = [
        ('model_h1.pkl', 'models/model_h1.pkl'),
        ('model_h2.pkl', 'models/model_h2.pkl'),
        ('model_h3.pkl', 'models/model_h3.pkl'),
        ('../data/forecasts.csv', 'data/forecasts.csv'),
        ('metrics.json', 'models/metrics.json'),
    ]
    
    print("\nUploading files...")
    success_count = 0
    for local_path, remote_path in files_to_upload:
        if os.path.exists(local_path):
            if upload_file(s3_client, bucket, local_path, remote_path, region):
                success_count += 1
        else:
            print(f"   [SKIP] {local_path} (not found)")
    
    print("\n" + "=" * 60)
    print(f"Upload complete! ({success_count}/{len(files_to_upload)} files)")
    print("=" * 60)
    print("\nVerification:")
    print(f"   Visit: https://cloud.digitalocean.com/spaces")
    print(f"   Bucket: {bucket}")
    print("\nPublic URLs:")
    base_url = f"https://{region}.digitaloceanspaces.com/{bucket}"
    print(f"   Models: {base_url}/models/")
    print(f"   Forecasts: {base_url}/data/forecasts.csv")


if __name__ == '__main__':
    main()
