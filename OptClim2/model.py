from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Float, Enum
from sqlalchemy import ForeignKey, UniqueConstraint

from .parameter import ParameterInt, ParameterFloat
from .common import LookupState

Base = declarative_base()


class DBRun(Base):
    __tablename__ = 'runs'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    parameters = relationship("DBParameter", order_by="DBParameter.name",
                              back_populates="run")
    lookup = relationship("DBLookup", back_populates="run")

    def __repr__(self):
        return f"<DBRun(name={self.name})>"


class DBParameter(Base):
    __tablename__ = 'parameters'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    run_id = Column(Integer, ForeignKey('runs.id'))
    type = Column(String)

    run = relationship("DBRun", back_populates="parameters")

    __table_args__ = (
        UniqueConstraint('name', 'run_id', name='_unique_params'), )

    __mapper_args__ = {
        'polymorphic_identity': 'parameter',
        'polymorphic_on': type}

    def __repr__(self):
        return f"<DBParameter(name='{self.name}')>"


class DBParameterInt(DBParameter):
    __tablename__ = 'parameters_int'

    id = Column(Integer, ForeignKey('parameters.id'), primary_key=True)
    minv = Column(Integer)
    maxv = Column(Integer)

    __mapper_args__ = {
        'polymorphic_identity': 'parameterint'}

    def __repr__(self):
        return f"<DBParameterInt(name='{self.name}', minv={self.minv}, " \
            f"maxv={self.maxv})>"

    @property
    def param(self):
        return ParameterInt(minv=self.minv, maxv=self.maxv)

    @classmethod
    def from_param(cls, run, name, parameter):
        return cls(name=name, minv=parameter.minv, maxv=parameter.maxv,
                   run=run)


class DBParameterFloat(DBParameter):
    __tablename__ = 'parameters_float'

    id = Column(Integer, ForeignKey('parameters.id'), primary_key=True)
    minv = Column(Float)
    maxv = Column(Float)
    resolution = Column(Float)

    __mapper_args__ = {
        'polymorphic_identity': 'parameterfloat'}

    def __repr__(self):
        return f"<DBParameterFloat(name='{self.name}', minv={self.minv}, " \
            f"maxv={self.maxv}, resolution={self.resolution})>"

    @property
    def param(self):
        return ParameterFloat(minv=self.minv, maxv=self.maxv,
                              resolution=self.resolution)

    @classmethod
    def from_param(cls, run, name, parameter):
        return cls(name=name, minv=parameter.minv, maxv=parameter.maxv,
                   resolution=parameter.resolution, run=run)


def getDBParameter(run, name, parameter):
    if isinstance(parameter, ParameterInt):
        return DBParameterInt.from_param(run, name, parameter)
    elif isinstance(parameter, ParameterFloat):
        return DBParameterFloat.from_param(run, name, parameter)
    else:
        raise TypeError('wrong type for argument parameter')


class DBLookup(Base):
    __tablename__ = 'lookup'

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey('runs.id'))
    state = Column(Enum(LookupState))
    type = Column(String)

    _vlist = relationship("DBLookupParameters", back_populates="_lookup")
    run = relationship("DBRun", back_populates="lookup")

    __mapper_args__ = {
        'polymorphic_identity': 'lookup',
        'polymorphic_on': type}

    def __init__(self, run, parameters):
        self.run = run
        for db_param in self.run.parameters:
            DBLookupParameters(
                _lookup=self, parameter=db_param,
                value=db_param.param.transform(parameters[db_param.name]))

    @property
    def values(self):
        values = {}
        for v in self._vlist:
            p = v.parameter
            values[p.name] = p.param.inv_transform(v.value)
        return values


class DBLookupMisfit(DBLookup):
    __tablename__ = 'lookup_misfit'

    id = Column(Integer, ForeignKey('lookup.id'), primary_key=True)
    misfit = Column(Float)

    __mapper_args__ = {
        'polymorphic_identity': 'residual'}


class DBLookupPath(DBLookup):
    __tablename__ = 'lookup_path'

    id = Column(Integer, ForeignKey('lookup.id'), primary_key=True)
    path = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'path'}


class DBLookupParameters(Base):
    __tablename__ = 'lookup_parameters'

    id = Column(Integer, primary_key=True)
    lid = Column(Integer, ForeignKey('lookup.id'))
    pid = Column(Integer, ForeignKey('parameters.id'))
    value = Column(Integer)

    _lookup = relationship(DBLookup, back_populates="_vlist")
    parameter = relationship("DBParameter")

    @property
    def name(self):
        return self.parameter.name


if __name__ == '__main__':
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine('sqlite:////tmp/test.sqlite')

    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)

    session = Session()

    run = DBRun(name='test')
    session.add(run)

    paramC = getDBParameter(run, 'C', ParameterInt(-20, -10))
    paramA = DBParameterFloat(name="A", minv=0., maxv=10.,
                              resolution=1e-6, run=run)
    paramB = DBParameterInt(name="B", minv=-10, maxv=20, run=run)
    session.add(paramA)
    session.add(paramB)
    session.add(paramC)

    values = {'A': 5,
              'B': 10,
              'C': -10}

    lookup = DBLookup(run, values)
    print(lookup.values)

    session.commit()

    print(run.parameters)
