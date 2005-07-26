
from execute import execWithCapture, execWithCaptureErrorStatus, execWithCaptureStatus


def follow_links_to_target(path, paths=[]):
    o, s = execWithCaptureStatus('/bin/ls', ['/bin/ls', '-l', path])
    if s == 0:
        words = o.strip().split()
        if words[0][0] == 'l':
            target = words[len(words) - 1]
            paths.append(target)
            return follow_links_to_target(target, paths)
        else:
            return path
    else:
        return None
