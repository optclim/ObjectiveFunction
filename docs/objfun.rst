The Objective Function
======================

An objective function returns the misfit of the model with observations given a particular set of parameters. The :class:`OptClim2.ObjectiveFunction` object implements a generic objective function as a lookup table.

The lookup table is queried using either the :meth:`OptClim2.ObjectiveFunction.get_result` which takes a dictionary of parameter values or by calling the :meth:`ObjectiveFunction instance <OptClim2.ObjectiveFunction.__call__>` with a tuple of parameter values. A lookup can have different results depending on the state of the entry in the lookup table.

.. list-table:: Lookup Result
   :header-rows: 1

   * - call
     - old state
     - new state
     - result
   * - :meth:`get_result(A) <OptClim2.ObjectiveFunction.get_result>`
     - N/A
     - PROVISIONAL
     - raises :exc:`OptClim2.OptClimPreliminaryRun`
   * - :meth:`get_result(A) <OptClim2.ObjectiveFunction.get_result>`
     - PROVISIONAL
     - NEW
     - raises :exc:`OptClim2.OptClimNewRun`
   * - :meth:`get_result(B) <OptClim2.ObjectiveFunction.get_result>`
     - PROVISIONAL
     - N/A
     - raises :exc:`OptClim2.OptClimWaiting`, drops provisional entry
   * - :meth:`get_result(A) <OptClim2.ObjectiveFunction.get_result>`
     - NEW
     - NEW
     - random positive value
   * - :meth:`get_result(A) <OptClim2.ObjectiveFunction.get_result>`
     - ACTIVE
     - ACTIVE
     - random positive value
   * - :meth:`get_result(A) <OptClim2.ObjectiveFunction.get_result>`
     - COMPLETED
     - COMPLETED
     - get stored value
   * - :meth:`get_new() <OptClim2.ObjectiveFunction.get_new>`
     - NEW
     - ACTIVE
     - get parameter set that is in NEW state
   * - :meth:`set_result(A, val) <OptClim2.ObjectiveFunction.set_result>`
     - ACTIVE
     - COMPLETED
     - get parameter set that is in NEW state

The system can automatically determine if models can be run in parallel. When the optimiser is called entries with the NEW or ACTIVE state return a random value. The first time a parameter set, A, lookup fails it is added with the PROVISIONAL state. If when the optimiser is run again the same parameter set A the entry enters the NEW state and a :exc:`OptClim2.OptClimNewRun` exception is raised. If however a different parameter set B is requested the PROVISIONAL parameter is dropped from the lookup table and a :exc:`OptClim2.OptClimWaiting` exception is raised. A different parameter set B indicates that the parameter set depends on the not yet know values and the optimiser has to wait until they become available before trying again.
