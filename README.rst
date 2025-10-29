=================================
Komfovent C6 integration for SIMO.io
=================================

Local‑first control and telemetry for Komfovent units with the C6 web
interface. This app adds a ``Komfovent`` gateway and a Recuperator
controller, with automatic sensors for supply‑air temperature and filter
contamination. Switch operating modes from the SIMO.io app; the gateway
polls the unit and updates state in near real time.

What you get (at a glance)
--------------------------

* Gateway type: ``Komfovent`` (auto‑created with defaults after restart).
* Component types:
  - ``State select`` (controller: "Recuperator") — selects operating mode.
  - ``Numeric sensor`` (auto‑created): "Recuperator supply temperature" (°C).
  - ``Numeric sensor`` (auto‑created): "Recuperator filter contamination" (%).
* Operating modes provided out of the box: Away, Normal, Intensive, Boost,
  Kitchen, Fireplace, Override, Holidays. Names update to match the device
  UI when available.
* Polling roughly every 30 s for state and telemetry; mode changes are
  sent directly to the unit.

Requirements
------------

* SIMO.io core ``>= 2.5.32`` (installed on your hub).
* Python ``>= 3.8``.
* Network reachability Hub → Komfovent controller over HTTP ``80/tcp``.
* A reserved/static IP for the Komfovent unit on your LAN.
* Valid Komfovent web UI credentials (username/password) for the unit.

Install on a SIMO.io hub
------------------------

1. SSH to your hub and activate the hub’s Python environment
   (for example ``workon simo-hub``).

   .. code-block:: bash

      workon simo-hub

2. Install the package.

   .. code-block:: bash

      pip install simo-komfovent

3. Enable the app in Django settings (``/etc/SIMO/settings.py``).

   .. code-block:: python

      # /etc/SIMO/settings.py
      from simo.settings import *  # keep platform defaults

      INSTALLED_APPS += [
          'simo_komfovent',
      ]

4. Apply migrations from this app.

   .. code-block:: bash

      cd /etc/SIMO/hub
      python manage.py migrate

5. Restart SIMO services so the new app and gateway type load.

   .. code-block:: bash

      supervisorctl restart all

After restart: discovery and logs
---------------------------------

The integration runs a background watcher. After installation and restart,
give it a short time; then open the ``Komfovent`` gateway in Django Admin
to see live logs of requests and state updates.

Add a Komfovent recuperator component
-------------------------------------

1. In the SIMO.io app: Components → Add New → Component.
2. Select Gateway: ``Komfovent``.
3. Select Component type: ``State select``.
4. Complete the form:
   - ``IP address`` — the Komfovent controller’s LAN IP (reserve it on the router).
   - ``Username`` and ``Password`` — Komfovent web UI credentials.
   - Usual component fields (name, room, category, icon).
5. Save. Two extra components are created automatically in the same zone:
   - "Recuperator supply temperature" (numeric sensor, °C).
   - "Recuperator filter contamination" (numeric sensor, %).

Using it in the SIMO.io app
---------------------------

Recuperator component (State select):

* Pick a mode from the list (Away, Normal, Intensive, Boost, Kitchen,
  Fireplace, Override, Holidays). The gateway sends the change to the unit
  and updates the state.

Auto‑created sensors:

* Supply temperature: shows current supply‑air temperature (°C).
* Filter contamination: shows filter clogging level (%). Useful for
  maintenance reminders.
* Sensors default to the “Basic Sensor” widget; you can switch to the
  “Graph” widget in the component form and adjust graph limits.

Django Admin
------------

* The ``Komfovent`` gateway appears automatically after restart — open it
  to view live logs of background polling and mode changes.
* Components show current value, alive state, and any error messages if the
  hub cannot reach the unit or parse telemetry.

Troubleshooting
---------------

* Cannot connect / component not alive:
  - Verify the IP address and that the unit is reachable from the hub over
    HTTP ``80/tcp``.
  - Confirm username/password are correct for the Komfovent web UI.
  - Reserve a static IP on your router to avoid IP changes.
* Modes list doesn’t match the device UI: Names are refreshed from the
  device. Wait for the next polling cycle.
* Sensors missing: They are created on first save of the Recuperator
  component. Delete and re‑create the Recuperator if needed.

Upgrade
-------

.. code-block:: bash

   workon simo-hub
   pip install --upgrade simo-komfovent
   python manage.py migrate
   supervisorctl restart all


License
-------

© Copyright by SIMO LT, UAB. Lithuania.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see `<https://www.gnu.org/licenses/>`_.
