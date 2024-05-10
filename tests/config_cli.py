
import subprocess

# Setup the configuration file
cfg = {}

# Define a call run mechanic
def run_call(command, stdin=None):
    '''Returns true if call succeeds, false otherwise'''
    try:
        subprocess.check_output(command, stdin=stdin)
    except subprocess.CalledProcessError as e:
        return False
    except OSError as e:
        return False
    return True
cfg['RUN_CALL'] = run_call
