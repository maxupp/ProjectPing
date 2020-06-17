call activate.bat project_ping
pushd %~dp0
python main.py
popd
PAUSE