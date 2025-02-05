import threading
import pathlib
import sqlite3

class DatabaseHandler():

    def __init__(self,dbPath:str):
        self._semaphore = threading.BoundedSemaphore()
        dataPath = pathlib.Path(pathlib.Path.home(),'.local','share','icable')
        dataPath.mkdir(parents=True,exist_ok=True)
        self._database = sqlite3.connect(pathlib.Path(dataPath,dbPath),check_same_thread=False,detect_types=sqlite3.PARSE_DECLTYPES)
        #self._database.row_factory = Row
        self._cursor = self._database.cursor()
        self._cursor.executescript("""
        BEGIN;
        CREATE TABLE IF NOT EXISTS "users" (
	        login TEXT PRIMARY KEY CHECK(typeof("login") = 'text'),
	        password BLOB NOT NULL CHECK(typeof("password") = 'blob'),
	        subnetid INTEGER NOT NULL CHECK(typeof("subnetid") = 'integer'),
	        subnetperm INTEGER NOT NULL DEFAULT 0 CHECK(typeof("subnetperm") = 'integer')
        );
        CREATE TABLE IF NOT EXISTS sessions (
            sid INTEGER PRIMARY KEY CHECK(typeof(sid) = 'integer'),
            login TEXT NOT NULL REFERENCES users(login) ON DELETE CASCADE ON UPDATE CASCADE CHECK(typeof(login) = 'text')
        );
        CREATE TABLE IF NOT EXISTS networks (
            id INTEGER PRIMARY KEY AUTOINCREMENT CHECK(typeof(id) = 'integer'),
            subnetid INTEGER NOT NULL CHECK(typeof(subnetid) = 'integer'),
            network INTEGER NOT NULL CHECK(typeof(network) = 'integer'),
            nmask INTEGER NOT NULL CHECK(typeof(nmask) = 'integer'),
            UNIQUE (subnetid,network,nmask)
        );
        CREATE TABLE IF NOT EXISTS networkUsers (
            networkid INTEGER NOT NULL REFERENCES networks(id) ON DELETE CASCADE ON UPDATE CASCADE CHECK(typeof(networkid) = 'integer'),
            userid TEXT NOT NULL REFERENCES users(login) ON DELETE CASCADE ON UPDATE CASCADE CHECK(typeof(userid) = 'text'),
            permissions INTEGER DEFAULT 0 CHECK(typeof(permissions) = 'integer'),
            PRIMARY KEY (networkid,userid)
        );
        CREATE TABLE IF NOT EXISTS firewall (
            subnetid INTEGER PRIMARY KEY CHECK(typeof(subnetid) = 'integer'),
            pickle FIREWALL NOT NULL CHECK(typeof(pickle) = 'blob')
        );
        CREATE TRIGGER IF NOT EXISTS cleanSubnetwork AFTER DELETE ON users WHEN NOT EXISTS (SELECT * FROM users WHERE subnetid = OLD.subnetid)
        BEGIN
	        DELETE FROM networks WHERE subnetid = OLD.subnetid;
        END;
        COMMIT;
        PRAGMA foreign_keys=ON;""")

    def execute(self,*args,**kwargs):
        return self._cursor.execute(*args,**kwargs)
    def fetchone(self,*args,**kwargs):
        return self._cursor.fetchone(*args,**kwargs)
    def fetchall(self,*args,**kwargs):
        return self._cursor.fetchall(*args,**kwargs)
    def fetchmany(self,*args,**kwargs):
        return self._cursor.fetchmany(*args,**kwargs)
    def commit(self,*args,**kwargs):
        return self.database.commit()
    
    @property
    def semaphore(self)->threading.BoundedSemaphore:
        return self._semaphore
    
    @property
    def database(self):
        return self._database
    
    def __del__(self):
        self._cursor.execute("PRAGMA optimize;")
        self.database.commit()
        self._cursor.close()
        self.database.close()
