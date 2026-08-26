import boto3
from botocore.config import Config

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'

s3 = boto3.client('s3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY_ID,
    aws_secret_access_key=R2_SECRET,
    config=Config(signature_version='s3v4')
)

dramas = [
    ('kakakku-bos-mafia', '20921'),
    ('enam-pewaris-untuk-presdir-bo', '20188'),
    ('gladiator-api-darah-dan-dendam', '21861'),
    ('dari-rival-jadi-kekasih', '21734'),
    ('runtuhnya-mahkota', '21045'),
    ('berkat-sistem-putri-jadi-milikku', '18698'),
    ('sang-penagih-utang-takdir', '18630'),
    ('mantan-istriku-ternyata-ceo', '20849'),
    ('putri-disakiti-ayah-ternyata-jenderal', '21614'),
    ('pelindungku-cinta-terlarangku', '20742'),
    ('cinta-takkan-berbalik', '20100'),
    ('ratu-hati-sang-pembalap', '20526'),
    ('aku-cerai-bos-mafia-gila', '20119'),
]

for slug, vid_id in dramas:
    prefix = f'dramas/netshort/{slug}/'
    resp = s3.list_objects_v2(Bucket=R2_BUCKET, Prefix=prefix, MaxKeys=1)
    count = resp.get('KeyCount', 0)
    status = f'[ADA] ({count} file+)' if count > 0 else '[BELUM]'
    print(f'{status:25s} | {slug}--{vid_id}')
