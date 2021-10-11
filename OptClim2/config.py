__all__ = ['OptclimConfig']

import logging
from configobj import ConfigObj, flatten_errors
from validate import Validator
from pathlib import Path
from os.path import expandvars
from io import StringIO

from .objective_function_misfit import ObjectiveFunctionMisfit
from .objective_function_residual import ObjectiveFunctionResidual
from .parameter import Parameter


class OptclimConfig:
    """handle OptClim configuration

    :param fname: the name of the configuration file
    :type fname: Path
    """

    defaultCfgStr = """
    [setup]
      basedir = string() # the base directory
      objfun = string(default=misfit)

    [parameters]
      [[__many__]]
        value = float() # the default value
        min = float(default=None) # the minimum value allowed
        max = float(default=None) # the maximum value allowed
        resolution = float(default=1e-6) # the resolution of the parameter
        constant = boolean(default=False) # if set to True the parameter is
                                          # not optimised for
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
        self._objfun = None

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
        self._optimise_params = {}

        for p in self.cfg['parameters']:
            self._params[p] = self.cfg['parameters'][p]['value']
            if not self.cfg['parameters'][p]['constant']:
                try:
                    self._optimise_params[p] = Parameter(
                        self.cfg['parameters'][p]['min'],
                        self.cfg['parameters'][p]['max'],
                        resolution=self.cfg['parameters'][p]['resolution'])
                except Exception as e:
                    msg = f'problem with parameter {p}: {e}'
                    self._log.error(msg)
                    raise RuntimeError(msg)

    @property
    def cfg(self):
        """a dictionary containing the configuration"""
        return self._cfg

    @property
    def parameters(self):
        """a dictionary of parameters and their values"""
        if self._params is None:
            self._get_params()
        return self._params

    @property
    def optimise_parameters(self):
        """a dictionary of parameters that should be optimised"""
        if self._optimise_params is None:
            self._get_params()
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
            self._objfun = objfun(self.basedir, self.optimise_parameters)
        return self._objfun


if __name__ == '__main__':
    import sys
    from pprint import pprint
    cfg = OptclimConfig(Path(sys.argv[1]))
    pprint(cfg.cfg)

    pprint(cfg.parameters)
    pprint(cfg.optimise_parameters)
