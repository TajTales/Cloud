from lingualive_api.persistence.settings import PersistenceSettings
from lingualive_api.persistence.s3 import S3ObjectStore

s = PersistenceSettings.from_environment()
store = S3ObjectStore(s.bucket, s.region)
key = "frames/tmp/smoke/test"
ref = store.put(key, b"hello", "image/png", max_bytes=1024)
print("put:", ref)
print("stat:", store.stat(key) == ref, "read:", store.read(key))
print("presigned:", store.presign_put(key, "image/png")[:80], "...")
store.delete(key)
print("deleted")