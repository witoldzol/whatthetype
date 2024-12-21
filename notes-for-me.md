# Notes to myself
## Build
`python setup.py bdist_wheel && rm -rf build && rm -rf *egg-info`
## Publish
`twine dist/*`
token is defined in `$HOME/.pypirc`
