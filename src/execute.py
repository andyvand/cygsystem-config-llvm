import rhpl.executil
import locale

BASH_PATH='/bin/bash'

    
def execWithCapture(bin, args):
    command = 'LANG=C ' + bin
    if len(args) > 0:
        for arg in args[1:]:
            command = command + ' ' + arg
    return rhpl.executil.execWithCapture(BASH_PATH, [BASH_PATH, '-c', command])
    
def execWithCaptureErrorStatus(bin, args):
    command = 'LANG=C ' + bin
    if len(args) > 0:
        for arg in args[1:]:
            command = command + ' ' + arg
    return rhpl.executil.execWithCaptureErrorStatus(BASH_PATH, [BASH_PATH, '-c', command])
