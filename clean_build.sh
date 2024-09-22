#!/bin/bash
# if dist exists, remove it, rebuild & clean up crap
[ -d "dist" ] && rm -rf dist && python setup.py bdist_wheel && rm -rf build && rm -rf *egg-info
