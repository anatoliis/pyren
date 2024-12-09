#!/bin/sh
#pip freeze > requirements.in
pip-compile requirements.in --generate-hashes
