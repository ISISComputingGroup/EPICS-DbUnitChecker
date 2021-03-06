DB Unit Checker
===============

The DBUnitChecker Python script is a helper file that checks a number of things are true about the PVs used within the project.

Current error checks are:

1. PVs that are labelled as interesting and have type longin, longout, ai or ao must contain a unit field
2. Description fields must contain less than 41 characters
3. All units must conform to unit standards (see below)
4. PVs that are labelled as interesting must have description fields
5. The names of PVs that are labelled as interesting must be capitialised and contain only A-Z 0-9 _ :
6. There should be no duplicate fields on PVs

Current warning are:

1. PVs that are labelled as interesting and have type longin, longout, ai or ao may not have blank fields
2. PVs are duplicated in a db

The checker is run at the end of a build on Jenkins and unit tests are failed if any of the error checks fail. Failed warnings will be noted and displayed in the test report but will not result in an unstable build.

Unit Standards
--------------

If the unit has a standard alphanumeric unit symbol that has been used. In the case where the usual symbol is not alphanumeric e.g. degree (°), angstrom (Å), the unit is written in full, lower case and singular.

Standard prefixes, [T|G|M|k|m|u|n|p|f], are accepted before all units.

Units can be constructed from a number of 'base' units using a space, forwardslash and caret for multiplication, division and powers respectively. For example a unit for work done could be "m s", a unit for velocity could be "m/s" and a unit for area "m!^2". This is the same standard as used in [http://linux.die.net/man/3/udunits udunits].

For PVs where the units are contestable, for example NUMSPECTRA, a blank units field is acceptable. This will give a warning, but not a failure, when a test is run and so can be discussed at a later date.

The units within the support/optics/ path are not checked as they contained a number of ambiguities and are rarely used.

Supported Units
---------------

The project currently contains the following base units:

* A
* angstrom
* bar
* bit
* byte
* C
* cm
* count
* degree
* eV
* hour
* Hz
* inch
* interrupt
* K
* L
* m
* minute
* ohm
* Oersted
* %
* photon
* pixel
* radian
* s
* torr
* step
* V
* T
* N

Ignoring Certain Paths
----------------------

Add directory name to ignore_paths.py