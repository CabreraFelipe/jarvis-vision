"""Explicit Windows desktop shortcut creation, targeting the existing managed installation."""
import os
import subprocess
import sys
from pathlib import Path

SCRIPT=r"""
$ErrorActionPreference = 'Stop'
$shell = New-Object -ComObject WScript.Shell
$desktop = $shell.SpecialFolders.Item('Desktop')
if ([string]::IsNullOrWhiteSpace($desktop)) { throw 'Desktop not available' }
$link = $shell.CreateShortcut((Join-Path $desktop 'JARVIS.lnk'))
$link.TargetPath = $env:JARVIS_SHORTCUT_PYTHONW
$link.Arguments = '"' + $env:JARVIS_SHORTCUT_MANAGER + '"'
$link.WorkingDirectory = $env:JARVIS_SHORTCUT_ROOT
$link.Description = 'JARVIS Vision - actualizaciones autenticadas'
$link.Save()
"""

def shortcut_paths(root,executable):
    root=Path(root).resolve()
    manager=root/'.jarvis'/'manager.py'
    pythonw=Path(executable).resolve().with_name('pythonw.exe')
    if not manager.is_file() or not pythonw.is_file():
        raise ValueError('No se encontró el gestor o pythonw.exe.')
    return root,manager,pythonw

def create_shortcut(root):
    if os.name!='nt': raise RuntimeError('Disponible solo en Windows.')
    root,manager,pythonw=shortcut_paths(root,sys.executable)
    powershell=Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32'/'WindowsPowerShell'/'v1.0'/'powershell.exe'
    if not powershell.is_file(): raise RuntimeError('No se encontró Windows PowerShell.')
    env=os.environ.copy()
    env.update(JARVIS_SHORTCUT_ROOT=str(root),JARVIS_SHORTCUT_MANAGER=str(manager),JARVIS_SHORTCUT_PYTHONW=str(pythonw))
    result=subprocess.run([str(powershell),'-NoProfile','-NonInteractive','-Command',SCRIPT],
                          env=env,capture_output=True,timeout=20,
                          creationflags=subprocess.CREATE_NO_WINDOW,check=False)
    if result.returncode!=0: raise RuntimeError('Windows no pudo crear el acceso directo.')
