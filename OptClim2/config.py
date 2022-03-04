__all__ = ['OptclimConfig']

import logging
from configobj import ConfigObj, flatten_errors
from validate import Validator
from pathlib import Path
from os.path import expandvars
from io import StringIO

from .objective_function_misfit import ObjectiveFunctionMisfit
from .objective_function_residual import ObjectiveFunctionResidual
from .parameter import ParameterFloat, ParameterInt


class OptclimConfig:
    """handle OptClim configuration

    :param fname: the name of the configuration file
    :type fname: Path
    """

    defaultCfgStr = """
    [setup]
      study = string() # the name of the study
      scenario = string() # the name of the scenario
      basedir = string() # the base directory
      objfun = string(default=misfit)
      db = string(default=None) # SQLAlchemy DB connection string

    [parameters]
      [[float_parameters]]
        [[[__many__]]]
          value = float() # the default value
          min = float() # the minimum value allowed
          max = float() # the maximum value allowed
          resolution = float(default=1e-6) # the resolution of the parameter
          constant = boolean(default=False) # if set to True the parameter is
                                             # not optimised for
      [[integer_parameters]]
        [[[__many__]]]
          value = integer() # the default value
          min = integer() # the minimum value allowed
          max = integer() # the maximum value allowed
          constant = boolean(default=False) # if set to True the parameter is
                                            # not optimised for


    [targets]
      __many__ = float
    """

    def __init__(self, fname: Path) -> None:
        self._log = logging.getLogger('OptClim2.config')

        if not fname.is_file():
            msg = f'no such configuration file {fname}'
            self._log.error(msg)
            raise RuntimeError(msg)

        # read config file into string
        cfgData = fname.open('r').read()
        # expand any environment variables
        cfgData = expandvars(cfgData)

        # populate the default  config object which is used as a validator
        optclimDefaults = ConfigObj(self.defaultCfgStr.split('\n'),
                                    list_values=False, _inspec=True)
        validator = Validator()

        self._cfg = ConfigObj(StringIO(cfgData), configspec=optclimDefaults)

        self._params = None
        self._optimise_params = None
        self._values = None
        self._objfun = None
        self._obsNames = None

        res = self._cfg.validate(validator, preserve_errors=True)
        errors = []
        # loop over any configuration errors
        for section, key, error in flatten_errors(self.cfg, res):
            section = '.'.join(section)
            if key is None:
                # missing section
                errors.append(f'section {section} is missing')
            else:
                if error is False:
                    errors.append(
                        f'{key} is missing in section {section}')
                else:
                    errors.append(
                        f'{key} in section {section}: {error}')
        if len(errors) > 0:
            msg = f'could not read configuration file {fname}'
            self._log.error(msg)
            for e in errors:
                self._log.error(e)
            raise RuntimeError(msg)

    def _get_params(self):
        self._params = {}
        self._values = {}

        PARAMS = {'float_parameters': ParameterFloat,
                  'integer_parameters': ParameterInt}

        for t in PARAMS:
            for p in self.cfg['parameters'][t]:
                self._values[p] = self.cfg['parameters'][t][p]['value']
                minv = self.cfg['parameters'][t][p]['min']
                maxv = self.cfg['parameters'][t][p]['max']
                extra = {}
                extra['constant'] = self.cfg['parameters'][t][p]['constant']
                if t == 'float':
                    extra['resolution'] = \
                        self.cfg['parameters'][t][p]['resolution']
                try:
                    self._params[p] = PARAMS[t](minv, maxv, **extra)
                except Exception as e:
                    msg = f'problem with parameter {p}: {e}'
                    self._log.error(msg)
                    raise RuntimeError(msg)

    @property
    def cfg(self):
        """a dictionary containing the configuration"""
        return self._cfg

    @property
    def values(self):
        """a dictionary of the parameter values"""
        if self._values is None:
            self._get_params()
        return self._values

    @property
    def parameters(self):
        """a dictionary of parameters"""
        if self._params is None:
            self._get_params()
        return self._params

    @property
    def optimise_parameters(self):
        """a dictionary of parameters that should be optimised"""
        if self._optimise_params is None:
            self._optimise_params = {}
            for p in self.parameters:
                if not self.parameters[p].constant:
                    self._optimise_params[p] = self.parameters[p]
        return self._optimise_params

    @property
    def basedir(self):
        """the base directory"""
        p = Path(self.cfg['setup']['basedir'])
        if not p.exists():
            self._log.info(f'creating base directory {p}')
            p.mkdir(parents=True)
        return p

    @property
    def study(self):
        """the name of the study"""
        return self.cfg['setup']['study']

    @property
    def scenario(self):
        """the name of the scenario"""
        return self.cfg['setup']['scenario']

    @property
    def objfunType(self):
        """the objective function type"""
        return self.cfg['setup']['objfun']

    @property
    def objectiveFunction(self):
        """intantiate a ObjectiveFunction object from config object"""
        if self._objfun is None:
            if self.objfunType == 'misfit':
                objfun = ObjectiveFunctionMisfit
            elif self.objfunType == 'residual':
                objfun = ObjectiveFunctionResidual
            else:
                msg = 'wrong type of objective function: ' + self.objfunType
                self._log.error(msg)
                raise RuntimeError(msg)
            self._objfun = objfun(self.study, self.basedir,
                                  self.optimise_parameters,
                                  scenario=self.scenario,
                                  db=self.cfg['setup']['db'])
        return self._objfun

    @property
    def observationNames(self):
        """the name of the observations"""
        if self._obsNames is None:
            self._obsNames = sorted(list(self.cfg['targets'].keys()))
        return self._obsNames

    @property
    def targets(self):
        return self.cfg['targets']


if __name__ == '__main__':
    import sys
    from pprint import pprint
    cfg = OptclimConfig(Path(sys.argv[1]))
    pprint(cfg.cfg)

    pprint(cfg.parameters)
    pprint(cfg.optimise_parameters)
    pprint(cfg.values)
