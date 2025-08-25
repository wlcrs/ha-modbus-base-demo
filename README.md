# Home Assistant `modbus_base` demonstration

This repository contains some code that explores the creation of a `modbus_base` integration
which acts as an abstraction layer between the integration `modbus_demo` and the underlying
Modbus communication library.

## `modbus_base`

The `modbus_base` integration is responsible for:

- opening, closing and keeping the connection alive
- making sure that only one action is performed on the the connection at any one time
- keeping track of which registers must be periodically read and provide them to the registered
  sensors via a `DataUpdateCoordinator`.

## `modbus_demo`

The `modbus_demo` integration is reponsible for:

- provide a config_flow which does the necessary things like gathering connection details, checking for uniqueness between config entries, etc.
- defining entities where the `EntityDescription` contains the fields defined in [`SimpleModbusEntityDescription`](modbus_base/entity.py#L34)


## TODO's

[ ] Create an example of a complex entity which queries multiple non-consecutive registers
