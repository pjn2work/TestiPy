@ECHO OFF

REM Clean previous setups
rmdir /s /q dist
rmdir /s /q build
rmdir /s /q TestiPy.egg-info


REM Create new setup
pip install wheel
python setup.py bdist_wheel


REM Install locally
for %%i in (.\dist\TestiPy-*-py3-none-any.whl) do pip install %%i


REM Clean current setup
rmdir /s /q dist
rmdir /s /q build
rmdir /s /q TestiPy.egg-info
