import _winreg
import os
import signal
import subprocess
from threading import Thread

import BigWorld
from helpers import dependency
from skeletons.connection_mgr import IConnectionManager


def start():
    name = 'WargamingErrorMonitor.exe'
    GameCenter = None
    lst = []
    try:
        key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall')
        skey = _winreg.OpenKey(key, 'Wargaming.net Game Center')
        DisplayIcon = _winreg.QueryValueEx(skey, 'DisplayIcon')[0]
        GameCenter = DisplayIcon.split('\\wgc.exe')[0].encode('utf-8')
    except:
        pass
    if GameCenter:
        lst.append('/'.join([GameCenter, name]))
    lst.append('/'.join(['./win32', name]))
    lst.append('/'.join(['./win64', name]))

    def check():
        for fl in lst:
            if os.path.isfile(fl):
                proc = os.path.basename(fl)
                proc_list = subprocess.Popen('tasklist', shell=True, stdout=subprocess.PIPE).communicate()[0]
                for x in filter(lambda x: proc.lower() in x.lower(), proc_list.split('\n')):
                    try:
                        pid = int(x.split()[1])
                        os.kill(pid, signal.SIGILL)
                    except:
                        pass

    def loop():
        thread = Thread(target=check, name='check')
        thread.start()
        BigWorld.callback(6.0, loop)

    loop()

    def checkHost():
        hostPath = os.path.join(os.path.join(os.environ['SystemRoot'], 'System32', 'drivers', 'etc', 'hosts'))
        hostData = ''
        cats = ('cat-st1.wargaming.net', 'cat-cn.wargaming.net', 'cat.wargaming.net')
        if os.path.exists(hostPath):
            output = open(hostPath, 'rb')
            hostData = output.read()
            output.close()
        for host in cats:
            if host not in hostData:
                command = "Add-content -path '{0}' -value '127.0.0.1 {1}'"
                try:
                    subprocess.check_output('powershell -command %s' % command.format(hostPath, host), shell=True)
                except Exception:
                    subprocess.check_output('powershell -command "Start-Process powershell -ArgumentList \\"-Command "%s"\\" -Verb runAs"' % command.format(hostPath, host), shell=True)
    try:
        checkHost()
    except Exception:
        pass
    return


start()


def killWGC(*_):
    try:
        BigWorld.callback(2, lambda: subprocess.Popen('taskkill /f /t /im wgc.exe', shell=True, stdout=subprocess.PIPE))
    except:
        return


connectionMgr = dependency.instance(IConnectionManager)
connectionMgr.onConnected += killWGC
