The Objective Function
======================

An objective function compares a model with observations given a particular set of parameters. ObjectiveFunction provides two generic objective functions that use a lookup table:
 * The :class:`ObjectiveFunction.ObjectiveFunctionMisfit` class uses a single value which is stored directly in the lookup table; and
 * the :class:`ObjectiveFunction.ObjectiveFunctionResidual` class uses an array containing the residuals. This array is stored in an auxiliary file.

The lookup table is queried using either the :meth:`ObjectiveFunction.ObjectiveFunction.get_result` which takes a dictionary of parameter values or by calling the :meth:`ObjectiveFunction instance <ObjectiveFunction.ObjectiveFunction.__call__>` with a numpy array containing parameter values. A lookup can have different results depending on the state of the entry in the lookup table. The methods :meth:`<ObjectiveFunction.ObjectiveFunction.values2params>` and :meth:`<ObjectiveFunction.ObjectiveFunction.params2values>` can be used to map between an array and a dictionary of parameter values and vice versa.

.. list-table:: Lookup Result
   :header-rows: 1

   * - call
     - old state
     - new state
     - result
   * - :meth:`get_result(A) <ObjectiveFunction.ObjectiveFunction.get_result>`
     - N/A
     - PROVISIONAL
     - raises :exc:`ObjectiveFunction.PreliminaryRun`
   * - :meth:`get_result(A) <ObjectiveFunction.ObjectiveFunction.get_result>`
     - PROVISIONAL
     - NEW
     - raises :exc:`ObjectiveFunction.NewRun`
   * - :meth:`get_result(B) <ObjectiveFunction.ObjectiveFunction.get_result>`
     - PROVISIONAL
     - N/A
     - raises :exc:`ObjectiveFunction.Waiting`, drops provisional entry
   * - :meth:`get_result(A) <ObjectiveFunction.ObjectiveFunction.get_result>`
     - NEW
     - NEW
     - random positive value
   * - :meth:`get_result(A) <ObjectiveFunction.ObjectiveFunction.get_result>`
     - ACTIVE
     - ACTIVE
     - random positive value
   * - :meth:`get_result(A) <ObjectiveFunction.ObjectiveFunction.get_result>`
     - COMPLETED
     - COMPLETED
     - get stored value
   * - :meth:`get_new() <ObjectiveFunction.ObjectiveFunction.get_new>`
     - NEW
     - ACTIVE
     - get parameter set that is in NEW state
   * - :meth:`set_result(A, val) <ObjectiveFunction.ObjectiveFunction.set_result>`
     - ACTIVE
     - COMPLETED
     - get parameter set that is in NEW state

The system can automatically determine if models can be run in parallel. When the optimiser is called entries with the NEW or ACTIVE state return a random value. The first time a parameter set, A, lookup fails it is added with the PROVISIONAL state. If when the optimiser is run again the same parameter set A is requested the entry enters the NEW state and a :exc:`ObjectiveFunction.NewRun` exception is raised. If however a different parameter set B is requested the PROVISIONAL parameter is dropped from the lookup table and a :exc:`ObjectiveFunction.Waiting` exception is raised. A different parameter set B indicates that the parameter set depends on the not yet know values and the optimiser has to wait until they become available before trying again.

The :meth:`<ObjectiveFunction.ObjectiveFunction.get_new>` method is used to get a parameter set that is in the NEW state. The entry is moved into the ACTIVE state. A :exc:`RuntimeError` exception is raised if there is no parameter set in the NEW state. 

Finally, the result of the objective function for a particular parameter set is set using the :meth:`<ObjectiveFunction.ObjectiveFunction.set_result>`. A :exc:`LookupError` is raised if there is no entry with that parameter set. A :exc:`RuntimeError` exception is raised if the entry is not in the ACTIVE state. On success the entry moves to the COMPLETED state.

