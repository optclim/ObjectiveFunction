Example Optimisation Run
========================
This directory holds an example setup. The script `model </example/bin/model>`_ is used to either generate synthetic data to be fitted or compute the misfit or residuals for a given set of parameters. In this case the model is a quadratic surface:

.. math::

   f(x,y) = ax^2+by^2+cxy+dx+ey+f

When the script is used to generate a synthetic data set it generates a random parameter set (uniformly distributed between minimum and maximum parameter value) that is stored in another file. Noise is added to the synthetic data before storing it in a file.
   
There are two options for running the optimisation:
 1. [nlopt](https://nlopt.readthedocs.io/en/latest/) which expects an objective function that returns a single value. The optimisation is configured in the `example.cfg </example/example.cfg>`_ configuration file. You can either run it using the `example.sh </example/example.sh>`_ shell script or a cylc work flow.
 2. [dfols](https://github.com/numericalalgorithmsgroup/dfols) which expects an objective function that returns a vector containing residuals. It is configured in the `example-dfols.cfg </example/example-dfols.cfg>`_ configuration file and run with the `example-dfols.sh </example/example-dfols.sh`_ shell script.

In both case you need to run the example from the top directory, ie
```bash ./example/example.sh```


