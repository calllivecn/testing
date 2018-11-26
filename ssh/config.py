


import getpass

__all__ = ["USERNAME","PASSWORD"]

USERNAME = input("username: ")
PASSWORD = getpass.getpass()

if __name__ == "__main__":
    print(USERNAME,PASSWORD,sep='\n')