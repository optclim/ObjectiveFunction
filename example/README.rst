Example Optimisation Run
========================
This directory holds an example setup. The script `model <bin/model>`_ is used to either generate synthetic data to be fitted or compute the misfit for a given set of parameters. In this case the model is a quadratic surface:

.. math::

   f(x,y) = ax^2+by^2+cxy+dx+ey+f

The optimisation is configured in the `example.cfg <example.cfg>`_ configuration file. You can either run it using the `example.sh <example.sh>`_ shell script or a cylc work flow.
