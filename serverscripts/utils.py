import subprocess


def get_output(command, cwd='.', fail_on_exit_code=True):
    """Run command and return output.

    ``command`` is just a string like "cat something".

    ``cwd`` is the directory where to execute the command.

    """
    process = subprocess.Popen(
        command,
        cwd=cwd,
        shell=True,
        universal_newlines=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    i, o, e = (process.stdin, process.stdout, process.stderr)
    i.close()
    output = o.read()
    error_output = e.read()
    o.close()
    e.close()
    exit_code = process.wait()
    if exit_code and fail_on_exit_code:
        print(output + error_output)
        raise RuntimeError("Running %s failed: %s" % (command, error_output))
    return (output, error_output)
