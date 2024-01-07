from pymongo import MongoClient, errors
from bson import json_util


def populate(src_fp: str, uri: str):
    client = MongoClient(uri)
    with open(src_fp) as file:
        data = json_util.loads(file.read())

    for db_name, collections in data.items():
        for col_name, entries in collections.items():
            for e in entries:
                try:
                    client[db_name][col_name].insert_one(e)
                except errors.DuplicateKeyError:
                    continue


if __name__ == '__main__':
    populate('data.json', 'mongodb://localhost:27018')