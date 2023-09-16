# import sqlite3


# class Database:

#     def __init__(self, db_file):
#         self.connection = sqlite3.connect(db_file)
#         self.cursor = self.connection.cursor()

#     def user_logining(self, login_user):
#         with self.connection:
#             user_data = self.cursor.execute(
#                 "SELECT * FROM 'users' WHERE 'login_user' = ?", (login_user,)).fetchall()
#                 # "SELECT 'login_user' FROM 'users'", (login_user,)).fetchall()
#             return user_data


# db = Database('users_bot.db')
# print(db.user_logining('Pavel'))


import csv


class Database:

    def __init__(self, db_file):
        self.db_file = db_file

    def user_logining(self, login_user, password_user):
        result = {}
        with open(self.db_file, 'r', encoding='UTF-8', newline='') as file:
            reader = csv.reader(file, delimiter=';')
            next(reader)
            for line in reader:
                lgn_user = line[1]
                pswd_user = line[2]
                result.update({lgn_user: pswd_user})
        if password_user == result.get(login_user):
            return True
        else:
            return False
    
    def user_task(self, login_user):
        with open(self.db_file, 'r', encoding='UTF-8', newline='') as file:
            reader = csv.reader(file, delimiter=';')
            next(reader)
            for line in reader:
                if login_user == line[1]:
                    result = f'id: {line[0]}, login: {line[1]}, password: {line[2]}'
                    # result = ' '.join(map(str, line))
                    return result
        # return result


# db = Database('users_db.csv')
# lgn = input('enter login: ')
# pswd = input('enter password: ')
# print(db.user_task('Pavel'))
