import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv
import os

load_dotenv()

S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY= os.getenv("S3_SECRET_KEY")

def upload_to_s3(file_name, bucket, object_name=None):

    s3 = boto3.client('s3', aws_access_key_id=S3_ACCESS_KEY,
                      aws_secret_access_key=S3_SECRET_KEY)

    if object_name is None:
        object_name = file_name

    try:
        s3.upload_file(file_name, bucket, object_name)
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False
    

def list_files(bucket_name):
    
    s3 = boto3.client('s3', aws_access_key_id=S3_ACCESS_KEY,
                      aws_secret_access_key=S3_SECRET_KEY)
    contents = []
    try:
        for item in s3.list_objects(Bucket=bucket_name)['Contents']:
            contents.append(item['Key'])
    except Exception as e:
        print(e)
        pass

    return contents

def create_presigned_url(bucket_name, object_name, expiration=3600):
    
    s3_client = boto3.client('s3', region_name='eu-central-1',
                              aws_access_key_id=S3_ACCESS_KEY,
                              aws_secret_access_key=S3_SECRET_KEY)
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        print(e)
        return None

    return response


def download_from_s3(bucket_name, s3_key, local_path):
    s3 = boto3.client('s3', aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY)
    s3.download_file(bucket_name, s3_key, local_path)
