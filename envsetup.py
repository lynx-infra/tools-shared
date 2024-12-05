import argparse
import subprocess
import sys


def RunCommand(command):
    p = subprocess.Popen(' '.join(command),
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         shell=True)
    result, error = p.communicate()
    # Compatibale with Python 3.
    # Since the return value of communicate is bytes instead of str in Python 3.
    return result.decode('utf-8'), error.decode('utf-8')

def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

if __name__ == '__main__':
    sys.exit(main())
