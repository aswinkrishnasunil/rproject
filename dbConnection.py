import pyodbc as odbc
import warnings
warnings.filterwarnings('ignore')


class SqlDbConn:
    """
        This class is connection of SQL Server
        @author: Madhubalan S
        @date: Tuesday October 20 14:11:00 2022
        @return: fetch the data's from db
    """
    def __init__(self):
        try:
            self.server_name = r"172.200.10.9"
            self.database = "SDR"
            self.username = "devuser"
            self.password = "D3vus3r!"
            self.conn = odbc.connect('DRIVER={ODBC Driver 17 for SQL Server}; \
                                        SERVER=' + self.server_name + '; \
                                        DATABASE=' + self.database + '; \
                                        UID=' + self.username + '; \
                                        PWD=' + self.password)
        except Exception as e:
            print("=========", e)

    def dbConn(self):
        return self.conn


if __name__ == "__main__":
    main = SqlDbConn()
    main.dbConn()


