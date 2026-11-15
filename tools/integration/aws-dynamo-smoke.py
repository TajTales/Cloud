from lingualive_api.persistence.settings import PersistenceSettings
from lingualive_api.persistence.dynamo_aws import AwsDynamoStore

settings = PersistenceSettings.from_environment()
store = AwsDynamoStore(settings)
store.ensure_table()          # kiểm tra schema + ghi SYSTEM#MODEL/META
print("health:", store.health())
store.close()