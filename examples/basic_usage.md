Basic Usage Examples
Normal Workflow
bash

cd ~/frappe-bench
python stop.py
bench start

When Ports Are Stuck
bash

# First try normal stop
python stop.py

# If ports still stuck, use advanced
python stop_all.py

# For emergency situations
python emergency_stop.py

With Supervisor
bash

# Use stop_all.py when supervisor manages your bench
python stop_all.py

