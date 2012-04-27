import transaction
import datetime as date

from sqlalchemy import orm, Table, Column, Numeric, Integer, String, ForeignKey, Sequence, Unicode, select, func, desc, asc, distinct, not_

from sqlalchemy.types import DateTime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relation, backref
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from zope.sqlalchemy import ZopeTransactionExtension
from useradmin.helpers import *

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


## User Admin Tables ##
""" Authentication Tables """
userGroup = Table('USER_GROUP', Base.metadata,
                    Column('USER_ID', Integer, ForeignKey('SZ_USER.USER_ID')),
                    Column('GROUP_ID', Integer, ForeignKey('SZ_GROUP.GROUP_ID'))
            )
"""
    DROP TABLE USER_GROUP;
    CREATE TABLE USER_GROUP (
        USER_ID  NUMBER(38) NOT NULL,
        GROUP_ID NUMBER(38) NOT NULL,
        CONSTRAINT PK_USER_GROUP PRIMARY KEY (USER_ID, GROUP_ID),
        CONSTRAINT FK_UG_SG_GROUP_ID FOREIGN KEY (GROUP_ID) REFERENCES SZ_GROUP (GROUP_ID),
        CONSTRAINT FK_UG_SU_USER_ID FOREIGN KEY (USER_ID) REFERENCES SZ_USER (USER_ID)
    );
    SELECT * FROM USER_GROUP;
"""

applicationGroup = Table('APPLICATION_GROUP', Base.metadata,
                    Column('APPLICATION_ID', Integer, ForeignKey('APPLICATION.APPLICATION_ID')),
                    Column('GROUP_ID', Integer, ForeignKey('SZ_GROUP.GROUP_ID'))
            )
"""
    DROP TABLE APPLICATION_GROUP;
    CREATE TABLE APPLICATION_GROUP (
        APPLICATION_ID NUMBER(38) NOT NULL,
        GROUP_ID       NUMBER(38) NOT NULL,
        CONSTRAINT PK_APPLICATION_GROUP PRIMARY KEY (APPLICATION_ID, GROUP_ID),
        CONSTRAINT FK_A_APPL_ID FOREIGN KEY (APPLICATION_ID) REFERENCES APPLICATION (APPLICATION_ID),
        CONSTRAINT FK_SG_CHNG_TYP FOREIGN KEY (GROUP_ID) REFERENCES SZ_GROUP (GROUP_ID)
    );
    SELECT * FROM APPLICATION_GROUP;
"""

groupPermission = Table('GROUP_PERMISSION', Base.metadata,
                    Column('GROUP_ID', Integer, ForeignKey('SZ_GROUP.GROUP_ID')),
                    Column('PERMISSION_ID', Integer, ForeignKey('PERMISSION.PERMISSION_ID'))
            )
"""
    DROP TABLE GROUP_PERMISSION;
    CREATE TABLE GROUP_PERMISSION (
        GROUP_ID      NUMBER(38) NOT NULL,
        PERMISSION_ID NUMBER(38) NOT NULL,
        CONSTRAINT PK_GROUP_PERMISSION PRIMARY KEY (GROUP_ID, PERMISSION_ID),
        CONSTRAINT FK_GP_SG_GROUP_ID FOREIGN KEY (GROUP_ID) REFERENCES SZ_GROUP (GROUP_ID),
        CONSTRAINT FK_GP_P_PERM_ID FOREIGN KEY (PERMISSION_ID) REFERENCES PERMISSION (PERMISSION_ID)
    );
    SELECT * FROM GROUP_PERMISSION;
"""

class User(Base):
    """
    DROP TABLE SZ_USER;
    CREATE TABLE SZ_USER (
        USER_ID             NUMBER(38) NOT NULL,
        USER_NAME           VARCHAR2(255) NOT NULL,
        FIRST_NAME          VARCHAR2(30) NULL,
        LAST_NAME           VARCHAR2(30) NULL,
        EMAIL               VARCHAR2(40) NULL,
        DTE_CREATE          DATE DEFAULT SYSDATE NOT NULL,
        DTE_UPDATE          DATE DEFAULT SYSDATE NOT NULL,
        LAST_UPD_BY         VARCHAR2(300) DEFAULT 'USER ' NOT NULL,
        DTE_EFFECTIVE_START DATE DEFAULT SYSDATE NOT NULL,
        DTE_EFFECTIVE_END   DATE DEFAULT SYSDATE NOT NULL,
        ACTION_TYPE         VARCHAR2(6) NULL,
        CONSTRAINT PK_SZ_USER PRIMARY KEY (USER_ID)
    );
    SELECT * FROM SZ_USER;
    """

    __tablename__  = 'SZ_USER'
    
    id             = Column('USER_ID', Integer, primary_key=True)
    userName       = Column('USER_NAME', String(255))
    firstName      = Column('FIRST_NAME', String(30))
    lastName       = Column('LAST_NAME', String(30))
    emailAddress   = Column('EMAIL', String(40))
    createdDate    = Column('DTE_CREATE', DateTime, nullable=False)
    updatedDate    = Column('DTE_UPDATE', DateTime, nullable=False)
    updatedBy      = Column('LAST_UPD_BY', String(300))
    effectiveStart = Column('DTE_EFFECTIVE_START', DateTime, nullable=False)
    effectiveEnd   = Column('DTE_EFFECTIVE_END', DateTime, nullable=False)
    actionType     = Column('ACTION_TYPE', String(6))
    groups         = relation('Group', secondary=userGroup, backref='users', lazy=False)

    def getMaxId(self):
        max = DBSession().query(self.__class__).from_statement(
            select(
                [self.__mapper__._with_polymorphic_selectable],
                select([func.max(self.__mapper__.c.id)]).label('id')==self.__mapper__.c.id)
        ).first()
        if max:
            self.id = max.id + 1
        else:
            self.id = 1

    def getAll(self, filter=None):
        query = DBSession().query(self.__class__)
        if filter:
            for word in filter.split():
                query = query.filter(getattr(User, "firstName").ilike("%%%s%%" % word))
        return query.order_by(self.__class__.id).all()

    def getAllDealLoader(self):
        return DBSession().query(self.__class__).join(['groups', 'applications']).filter_by(applicationName='dealloader').order_by(self.__class__.id).all()

    def getById(self, id=None):
        if not id: return
        return DBSession().query(self.__class__).filter_by(id=id).one()

    def getSet(self, limit=10, offset=0):
        return DBSession().query(self.__class__).order_by(self.__class__.id).limit(limit).offset(offset).all()

    def getTotal(self):
        return DBSession().query(self.__class__).count()

    def setParams(self, data=None, username='149924'):
        if not data: return self
        self.userName       = data.get('userName')
        self.firstName      = data.get('firstName')
        self.lastName       = data.get('lastName')
        self.emailAddress   = data.get('emailAddress')
        self.updatedBy      = username
        self.updatedDate    = date.datetime.today()
        self.effectiveStart = date.datetime.strptime(data.get('effectiveStartDate'), getSettings('date.short'))
        self.effectiveEnd   = date.datetime.strptime(data.get('effectiveEndDate'), getSettings('date.short'))
        self.setGroupData(data)
        if not self.createdDate:
            self.createdDate = date.datetime.today()
        return self

    def setGroupData(self, data=None):
        if not data: return self
        self.groups = [ ]
        for id in data.getall('user_group'):
            self.groups.append(Group().getById(id))
        return self.groups

    def create(self, params):
        self.getMaxId()
        self.setParams(params)
        session = DBSession()
        session.add(self)
        return

    def update(self, params):
        self.setParams(params)
        session = DBSession()
        return

    def delete(self):
        session = DBSession()
        session.delete(self)
        return

    def jsonify(self):
        """ dump to json string """
        groups = [ ]
        for g in self.groups:
            group  = { }
            group['id']    = g.id
            group['label'] = g.groupName
            groups.append(group)
        result = {
              'id':             self.id,
              'userName':       self.userName,
              'firstName':      self.firstName,
              'lastName':       self.lastName,
              'emailAddress':   self.emailAddress,
              'createdDate':    self.createdDate.strftime(getSettings('date.short')),
              'updatedDate':    self.updatedDate.strftime(getSettings('date.short')),
              'updatedBy':      self.updatedBy,
              'effectiveStart': self.effectiveStart.strftime(getSettings('date.short')),
              'effectiveEnd':   self.effectiveEnd.strftime(getSettings('date.short')),
              'actionType':     self.actionType or 0,
              'group':          groups,
              'label':          '%d-%s'%(self.id, self.userName)
        }
        return result


class Group(Base):
    """
    DROP TABLE SZ_GROUP;
    CREATE TABLE SZ_GROUP (
        GROUP_ID   NUMBER(38) NOT NULL,
        GROUP_NAME VARCHAR2(100) NOT NULL,
        CONSTRAINT PK_SZ_GROUP PRIMARY KEY (GROUP_ID)
    );
    SELECT * FROM SZ_GROUP;
    """

    __tablename__ = 'SZ_GROUP'

    id            = Column('GROUP_ID', Integer, primary_key=True)
    groupName     = Column('GROUP_NAME', String(100))
    applications  = relation('Application', secondary=applicationGroup, backref='groups', lazy=False)
    permissions   = relation('Permission', secondary=groupPermission, backref='groups', lazy=False)

    def getMaxId(self):
        max = DBSession().query(self.__class__).from_statement(
            select(
                [self.__mapper__._with_polymorphic_selectable],
                select([func.max(self.__mapper__.c.id)]).label('id')==self.__mapper__.c.id)
        ).first()
        if max:
            self.id = max.id + 1
        else:
            self.id = 1

    def getAll(self):
        return DBSession().query(self.__class__).order_by(self.__class__.id).all()

    def getById(self, id=None):
        if not id: return
        return DBSession().query(self.__class__).filter_by(id=id).one()

    def setParams(self, data=None):
        if not data: return self
        self.groupName = data.get('objectName')
        self.setApplicationData(data)
        self.setPermissionData(data)

    def setApplicationData(self, data=None):
        if not data: return self
        self.applications = [ ]
        for id in data.getall('application_group'):
            self.applications.append(Application().getById(id))
        return self.applications

    def setPermissionData(self, data=None):
        if not data: return self
        self.permissions = [ ]
        for id in data.getall('permission_group'):
            self.permissions.append(Permission().getById(id))
        return self.permissions

    def create(self, params):
        self.getMaxId()
        self.setParams(params)
        session = DBSession()
        session.add(self)
        return

    def update(self, params):
        self.setParams(params)
        session = DBSession()
        return

    def delete(self):
        session = DBSession()
        session.delete(self)
        return

    def jsonify(self):
        """ dump to json string """
        applications = [ ]
        permissions  = [ ]
        for app in self.applications:
            applications.append(app.jsonify())
        for perm in self.permissions:
            permissions.append(perm.jsonify())
        result = {
              'id':           self.id,
              'groupName':    self.groupName,
              'applications': applications,
              'permissions':  permissions,
              'label':        '%d-%s'%(self.id, self.groupName),
        }
        return result


class Permission(Base):
    """
    DROP TABLE PERMISSION;
    CREATE TABLE PERMISSION (
        PERMISSION_ID   NUMBER(38) NOT NULL,
        PERMISSION_NAME VARCHAR2(100) NOT NULL,
        CONSTRAINT PK_PERMISSION PRIMARY KEY (PERMISSION_ID)
    );
    INSERT INTO PERMISSION (PERMISSION_ID, PERMISSION_NAME) VALUES(1, 'index');
    INSERT INTO PERMISSION (PERMISSION_ID, PERMISSION_NAME) VALUES(2, 'search');
    INSERT INTO PERMISSION (PERMISSION_ID, PERMISSION_NAME) VALUES(3, 'edit');
    INSERT INTO PERMISSION (PERMISSION_ID, PERMISSION_NAME) VALUES(4, 'pending');
    INSERT INTO PERMISSION (PERMISSION_ID, PERMISSION_NAME) VALUES(5, 'history');
    INSERT INTO PERMISSION (PERMISSION_ID, PERMISSION_NAME) VALUES(6, 'versions');
    INSERT INTO PERMISSION (PERMISSION_ID, PERMISSION_NAME) VALUES(7, 'update');
    INSERT INTO PERMISSION (PERMISSION_ID, PERMISSION_NAME) VALUES(8, 'delete');
    INSERT INTO PERMISSION (PERMISSION_ID, PERMISSION_NAME) VALUES(9, 'rollback');
    INSERT INTO PERMISSION (PERMISSION_ID, PERMISSION_NAME) VALUES(10, 'approve');
    INSERT INTO PERMISSION (PERMISSION_ID, PERMISSION_NAME) VALUES(11, 'administer');
    SELECT * FROM PERMISSION;
    """

    __tablename__  = 'PERMISSION'

    id             = Column('PERMISSION_ID', Integer, primary_key=True)
    permissionName = Column('PERMISSION_NAME', String(100))

    def getMaxId(self):
        max = DBSession().query(self.__class__).from_statement(
            select(
                [self.__mapper__._with_polymorphic_selectable],
                select([func.max(self.__mapper__.c.id)]).label('id')==self.__mapper__.c.id)
        ).first()
        if max:
            self.id = max.id + 1
        else:
            self.id = 1

    def getAll(self):
        return DBSession().query(self.__class__).order_by(self.__class__.id).all()

    def getById(self, id=None):
        if not id: return
        return DBSession().query(self.__class__).filter_by(id=id).one()

    def getPermissions(self, userId=None):
        currentTime = date.datetime.today()
        query = DBSession().query(self.__class__).join(['groups', 'applications']).filter_by(applicationName='dealloader').join(['groups', 'users']).filter_by(userName=userId)
        return query.filter(User.effectiveStart<=currentTime).filter(User.effectiveEnd>currentTime).all()

    def setParams(self, data=None):
        if not data: return self
        self.permissionName = data.get('objectName')

    def create(self, params):
        self.getMaxId()
        self.setParams(params)
        session = DBSession()
        session.add(self)
        return

    def update(self, params):
        self.setParams(params)
        session = DBSession()
        return

    def delete(self):
        session = DBSession()
        session.delete(self)
        return

    def jsonify(self):
        """ dump to json string """
        result = {
              'id':             self.id,
              'permissionName': self.permissionName,
              'label':          '%d-%s'%(self.id, self.permissionName),
        }
        return result


class Application(Base):
    """
    DROP TABLE APPLICATION;
    CREATE TABLE APPLICATION (
        APPLICATION_ID        NUMBER(38) NOT NULL,
        APPLICATION_NAME      VARCHAR2(100) NOT NULL,
        APPLICATION_DESC      VARCHAR2(255),
        APPLICATION_STATUS_CD INTEGER,
        APPLICATION_URL       VARCHAR2(255),
        MAINTENANCE_URL       VARCHAR2(255),
        CONSTRAINT PK_APPLICATION PRIMARY KEY (APPLICATION_ID)
    );
    INSERT INTO APPLICATION (APPLICATION_ID, APPLICATION_NAME, APPLICATION_DESC) VALUES(1, 'dealloader', 'Deal Loader Tool');
    SELECT * FROM APPLICATION;
    """

    __tablename__   = 'APPLICATION'

    id              = Column('APPLICATION_ID', Integer, primary_key=True)
    applicationName = Column('APPLICATION_NAME', String(100))
    description     = Column('APPLICATION_DESC', String(255))
    status          = Column('APPLICATION_STATUS_CD', Integer)
    applicationUrl  = Column('APPLICATION_URL', String(255))
    maintenanceUrl  = Column('MAINTENANCE_URL', String(255))
#    group           = relation('Group', secondary=applicationGroup, backref='applications', lazy=False)

    def getMaxId(self):
        max = DBSession().query(self.__class__).from_statement(
            select(
                [self.__mapper__._with_polymorphic_selectable],
                select([func.max(self.__mapper__.c.id)]).label('id')==self.__mapper__.c.id)
        ).first()
        if max:
            self.id = max.id + 1
        else:
            self.id = 1

    def getAll(self):
        return DBSession().query(self.__class__).order_by(self.__class__.id).all()

    def getById(self, id=None):
        if not id: return
        return DBSession().query(self.__class__).filter_by(id=id).one()

    def setParams(self, data=None):
        if not data: return self
        self.applicationName = data.get('objectName')

    def setGroupData(self, data=None):
        if not data: return self
        self.groups = [ ]
        for id in data.getall('group'):
            self.groups.append(Group().getById(id))
        return self.groups

    def create(self, params):
        self.getMaxId()
        self.setParams(params)
        session = DBSession()
        session.add(self)
        return

    def update(self, params):
        self.setParams(params)
        session = DBSession()
        return

    def delete(self):
        session = DBSession()
        session.delete(self)
        return

    def jsonify(self):
        """ dump to json string """
        result = {
              'id':              self.id,
              'applicationName': self.applicationName,
              'description':     self.description,
              'status':          self.status,
              'applicationUrl':  self.applicationUrl,
              'maintenanceUrl':  self.maintenanceUrl,
              'label':           '%d-%s'%(self.id, self.applicationName),
        }
        return result


## For Testing Framework ##
class MyModel(Base):
    __tablename__ = 'models'
    id    = Column(Integer, primary_key=True)
    name  = Column(Unicode(255), unique=True)
    value = Column(Integer)

    def __init__(self, name, value):
        self.name  = name
        self.value = value

def initialize_sql(engine):
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
#    Base.metadata.create_all(engine)
