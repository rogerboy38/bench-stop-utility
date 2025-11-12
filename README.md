# 🛑 Bench Stop Utility

**Zero-freeze, reliable process killer for Frappe/ERPNext benches**

[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![No Freeze Guarantee](https://img.shields.io/badge/Zero%20Freeze-Guaranteed-green.svg)](https://github.com/rogerboy38/bench-stop-utility)

Tired of `bench start` failing with "Address already in use"? Frustrated with frozen terminals when trying to stop services? This utility solves both problems!

## 🚀 Quick Start

```bash
cd ~/frappe-bench
wget https://raw.githubusercontent.com/rogerboy38/bench-stop-utility/master/stop.py
python stop.py
bench start
