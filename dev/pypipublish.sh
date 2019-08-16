#!/usr/bin/env bash

pushd $1

rm -rf dist build

python3 setup.py sdist bdist_wheel

python3 -m twine upload dist/* --verbose

popd
