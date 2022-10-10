class DbClient:

    def __init__(self, client, db, environment):
        self.__mongo = client[db]
        self.environment = environment
    
    # tagging
    def get_table(self, table):
        return table + '_' + self.environment

    # element
    def insert(self, table, document):
        return self.__mongo[self.get_table(table)].insert_one(document)

    def get(self, table, query):
        return [doc for doc in self.__mongo[self.get_table(table)].find(query)]

    def find(self, table, query):
        return self.__mongo[self.get_table(table)].find(query)

    def get_all(self, table):
        return [doc for doc in self.__mongo[self.get_table(table)].find()]

    def update(self, table, match, query, upsert=False):
        return self.__mongo[self.get_table(table)].update_one(match, {"$set":  query}, upsert=upsert)

    def update_many(self, table, match, query, upsert=False):
        return self.__mongo[self.get_table(table)].update_many(match, {"$set":  query}, upsert=upsert)

    def delete(self, table, match):
        return self.__mongo[self.get_table(table)].delete_one(match)

    def increase(self, table, match, query):
        return self.__mongo[self.get_table(table)].update_one(match, {"$inc":  query})

    # applied
    def get_author(self, user_name):
        return [doc for doc in self.__mongo[self.get_table("Author")].find({"user_name": user_name})][0]

    def update_author(self, user_name, query, upsert=False):
        return self.__mongo[self.get_table("Author")].update_one({"user_name": user_name}, {"$set":  query}, upsert=upsert)

    def increase_author(self, user_name, query):
        return self.__mongo[self.get_table("Author")].update_one({"user_name": user_name}, {"$inc":  query})
    
    def user_key_existence(self, user_name, key):
        return len(list(self.__mongo[self.get_table("Author")].find({"user_name": f'{user_name}', f"{key}": {"$exists": True}})))

    def key_existence(self, table, key=None):
        return len(list(self.__mongo[self.get_table(table)].find({f"{key}": {"$exists": True}})))


    def reset_user(self, user_name):
        user_id = self.get_author(user_name)["user_id"]
        self.delete("Author", {"user_name": user_name})
        self.insert("Author", {"user_name": user_name, "user_id": user_id})