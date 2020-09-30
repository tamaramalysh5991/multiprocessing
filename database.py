from sqlalchemy import (Boolean, Column, Integer, Sequence, String,
                        create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

Base = declarative_base()


class Url(Base):
    """Table for keep Url object"""
    __tablename__ = 'urls'
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True,
                autoincrement=True)
    url = Column(String(50))
    title = Column(String(70))
    flag = Column(Boolean)

    def __repr__(self):
        return "<Url(url='%s', title='%s', flag='%s')>" % (
            self.url, self.title, self.flag)


engine = create_engine('sqlite:///orm_in_detail.sqlite', poolclass=NullPool)
session = sessionmaker()
session.configure(bind=engine)
Base.metadata.create_all(engine)
s = session()


def add_db(url, title, status=True, ):
    """Added url in database and save it.
    Args:
        url(str): Main domain.
        status(bool): Status of pattern.
    """
    try:
        link = s.query(Url).filter(Url.url == url).first()
        if link is None:
            url_db = Url(
                url=url,
                title=title,
                flag=status
            )
            s.add(url_db)
            s.commit()
            return 'Added in db'
        else:
            return 'In db'
    except Exception as e:
        return str(e)


def commit_db():
    """Commit database"""
    s.commit()


def return_db():
    """Return current database"""
    return s.query(Url).all()


def delete_database():
    """Method for deleting database"""
    print('Database removed')
    Url.__table__.drop(engine)
