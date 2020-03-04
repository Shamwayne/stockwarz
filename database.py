"""
This is the database for storing user investments and credentials for verification and whatnot
"""
from datetime import datetime
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Boolean
from sqlalchemy import Integer
from sqlalchemy import String, Text
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declared_attr # see class Base for details
from flask_login import UserMixin


db_engine = create_engine('sqlite:///stocks.db', connect_args={'check_same_thread': False})

class Base(object):
    """
    this enables all shared database classes to have premade attributes and behaviour.
    In this case it was to auto generate the __tablename__ attribute ONLY.
    """
    @declared_attr
    def __tablename__(cls):
        """ autogenerates the __tablename__ attribute with the class name
        in lowercase.
        e.g 'class FooBar()' will have an __tablename__ == 'foobar' automatically.
        """
        return cls.__name__.lower()

Base = declarative_base(cls=Base)

class User(UserMixin, Base):
	id = Column(Integer, primary_key=True)
	username = Column(String, unique=True)
	password = Column(String)
	phone = Column(String, unique=True)
	balance = Column(Float, default=20000)


class BoughtShares(Base):
	id = Column(Integer, primary_key=True)
	userid = Column(Integer, ForeignKey('user.id'))
	date_bought = Column(DateTime, default=datetime.now)
	cost_per_share = Column(Float)
	no_of_shares = Column(Integer)
	symbol = Column(String)

class SoldShares(Base):
	id = Column(Integer, primary_key=True)
	cost_per_share = Column(Float)
	userid = Column(Integer, ForeignKey('user.id'))
	date_sold = Column(DateTime, default=datetime.now)
	no_of_shares = Column(Integer)
	symbol = Column(String)

"""
Holding off dividents here
"""

# class Dividents(Base):
# 	id = Column(Integer, primary_key=True)
# 	divident_per_share = Column(Float)
# 	shares_id = Column(Integer, ForeignKey('boughtshares.id'))
# 	date_paid = Column(DateTime, default=datetime.now)



Base.metadata.create_all(db_engine)
Session = sessionmaker(bind=db_engine)
db_session = Session()
