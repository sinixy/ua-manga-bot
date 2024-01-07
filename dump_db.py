from pymongo import MongoClient
from bson import json_util


def dump(fp: str, uri: str, db_names: list):
    client = MongoClient(uri)
    data = {}

    for db_name in db_names:
        data[db_name] = {}
        col_names = client[db_name].list_collection_names()
        for col_name in col_names:
            data[db_name][col_name] = list(client[db_name][col_name].find({}))

    with open(fp, 'w') as file:
        file.write(json_util.dumps(data, indent=2))


if __name__ == '__main__':
    dump('data.json', 'mongodb://localhost:27018', ['apscheduler', 'bot'])