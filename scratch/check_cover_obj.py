import boto3

s3 = boto3.client(
    's3',
    endpoint_url='https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com',
    aws_access_key_id='07c99c897986ea52703c1285308d5e2c',
    aws_secret_access_key='44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44',
    region_name='auto'
)

res = s3.head_object(
    Bucket='shortlovers',
    Key='dramas/covers/auto_qtfjcm5h28bqklafpgndqxz3.jpg'
)

print("LastModified:", res.get('LastModified'))
print("ContentLength:", res.get('ContentLength'))
print("ContentType:", res.get('ContentType'))
