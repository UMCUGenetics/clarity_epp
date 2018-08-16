import sys
import getopt
import os
import tempfile


def log(msg):
    f = open("/opt/gls/clarity/customextensions/logs/runLater.log", "a")
    f.write(msg + "\n")
    f.close()


def main():
    global args

    args = {}

    opts, extraparams = getopt.getopt(sys.argv[1:], "c:")

    for o, p in opts:
        if o == '-c':
            args["command"] = p

    if len(args["command"]) > 0:
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as tmp:
            cmd = 'bash -l -c "' + args["command"] + '"'
            log(cmd)
            tmp.write(cmd)

        cmd = "cd /tmp && /usr/bin/at -f " + path + " now"
        log(cmd)
        os.system(cmd)
        print("This step will be finished for you. Press the 'Lab View' button on the main Clarity Tool Bar")


if __name__ == "__main__":
    main()
