ObjectiveFunction Configuration
===============================

Simulations run within the ObjectiveFunction framework are stored in a hierarchy:
 * A **study** defines a group of simulations run with the same set of parameters. Each parameter has a name and is defined by type (integer of float) and an upper and lower bound. 
 * Each study consists of a number of **scenarios**. Scenarios are distinguished from each other by some other configuration. For example, in the case of a climate model this might be different CO2 forcing.
 * Each scenario holds a number of actual model **runs** where the parameters are varied within their bounds.
