import rhpl.executil
import locale
import time
import gtk
import os, sys
import select


ERROR_MESSAGE =_("An error has occurred while running a system command. Please check logs for details.") 

BASH_PATH='/bin/bash'

def execWithCapture(bin, args):
    return execWithCaptureErrorStatus(bin, args)[0]

def execWithCaptureStatus(bin, args):
    res = execWithCaptureErrorStatus(bin, args)
    return res[0], res[2]

def execWithCaptureErrorStatus(bin, args):
    command = 'LANG=C ' + bin
    if len(args) > 0:
        for arg in args[1:]:
            command = command + ' ' + arg
    return rhpl.executil.execWithCaptureErrorStatus(BASH_PATH, [BASH_PATH, '-c', command])


def execWithCaptureProgress(bin, args, message):
    forked = ForkedCommand(bin, args, message)
    return forked.run()[0]

def execWithCaptureStatusProgress(bin, args, message):
    forked = ForkedCommand(bin, args, message)
    res = forked.run()
    return res[0], res[2]

def execWithCaptureErrorStatusProgress(bin, args, message):
    forked = ForkedCommand(bin, args, message)
    return forked.run()



class ForkedCommand:
    def __init__(self, bin, args, message):
        self.child_pid = None
        self.pbar_timer = 0
        self.be_patient_dialog = None
        self.system_command_retval = None
        
        self.bin = bin
        self.args = args
        
        self.message = message
        
        # This pipe is for the parent process to receive
        # the result of the system call in the child process.
        self.fd_read_out, self.fd_write_out = os.pipe()
        self.fd_read_err, self.fd_write_err = os.pipe()
        
    def run(self):
        try:
            self.child_pid = os.fork()
        except OSError:
            sys.exit("Unable to fork!!!")
            
        if (self.child_pid != 0):
            # parent process
            os.close(self.fd_write_out)
            os.close(self.fd_write_err)
            
            return self.showDialog(self.message)
        else:
            # child process

            os.close(self.fd_read_out)
            os.close(self.fd_read_err)
            
            out, err, res = execWithCaptureErrorStatus(self.bin, self.args)
            # let parent process know result of system call through IPC
            os.write(self.fd_write_out, out)
            os.write(self.fd_write_err, err)
            os.close(self.fd_write_out)
            os.close(self.fd_write_err)
            
            os._exit(res)
        
    def showDialog(self,message):
        self.be_patient_dialog = gtk.Dialog()
        self.be_patient_dialog.set_has_separator(False)
        
        label = gtk.Label(message)
        self.be_patient_dialog.vbox.pack_start(label, True, True, 0)
        self.be_patient_dialog.set_modal(True)
        
        #Create an alignment object that will center the pbar
        align = gtk.Alignment(0.5, 0.5, 0, 0)
        self.be_patient_dialog.vbox.pack_start(align, False, False, 5)
        align.show()
        
        self.pbar = gtk.ProgressBar()
        align.add(self.pbar)
        self.pbar.show()
        
        #Start bouncing progress bar
        self.pbar_timer = gtk.timeout_add(100, self.progress_bar_timeout)
        
        self.be_patient_dialog.show_all()
        while self.be_patient_dialog.run() == gtk.RESPONSE_DELETE_EVENT:
            pass
        self.be_patient_dialog.destroy()
        
        # child has finished, collect data
        out = ''
        err = ''
        in_list = [self.fd_read_out, self.fd_read_err]
        while len(in_list) != 0:
            i,o,e = select.select(in_list, [], [])
            for fd in i:
                if fd == self.fd_read_out:
                    s = os.read(self.fd_read_out, 1000)
                    if s == '':
                        in_list.remove(self.fd_read_out)
                    out = out + s
                if fd == self.fd_read_err:
                    s = os.read(self.fd_read_err, 1000)
                    if s == '':
                        in_list.remove(self.fd_read_err)
                    err = err + s
        os.close(self.fd_read_out)
        os.close(self.fd_read_err)
        
        return out, err, self.system_command_retval
    
    def progress_bar_timeout(self):
        (reaped, status) = os.waitpid(self.child_pid, os.WNOHANG)
        
        if reaped == self.child_pid:
            # child exited
            if os.WIFEXITED(status):
                ret_status = os.WEXITSTATUS(status)
                self.system_command_retval = ret_status
            else:
                self.system_command_retval = 255
            self.be_patient_dialog.response(gtk.RESPONSE_OK)
            return False
        else:
            # child still alive
            self.pbar.pulse()
            return True
