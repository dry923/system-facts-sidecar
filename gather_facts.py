#!/usr/bin/env python3

import socket
import sys
import argparse
import redis
import logging
from subprocess import PIPE, Popen

# Create basic logger
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
log = logging.getLogger("my-log")

def main(argv):
    parser = argparse.ArgumentParser(description="Obtain Facts and write them to Redis")
    parser.add_argument("-c", "--ip", default="127.0.0.1", help="Communication IP")
    parser.add_argument("-p", "--port", default=7777, type=int, help="Communication Port")
    parser.add_argument("-x", "--redis-port", default=6379, help="Redis Port")
    parser.add_argument("-r", "--redis-ip", required=True, help="Redis IP")
    parser.add_argument("-i", "--input-file", required=True, help="Input File")
    parser.add_argument("-v", "--log-level", default="INFO", help="Log Level")
    args = parser.parse_args()

    log.setLevel(args.log_level)

    log.info("Waiting for input")
    waitForInput(args)

def waitForInput(args):
    # Bind to IP and port and wait for the "get" command
    log.debug("Attempting to connect to port %d", args.port)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((args.ip, args.port))
    except:
        log.error("ERROR: Unable to bind to port %d. Exiting", args.port)
        exit(1)
    s.listen()
    conn, addr = s.accept()
    while True:
        data = conn.recv(1024)
        if data.decode().strip() == "get":
            log.info("Recieved get command")
            gatherFacts(args)

def gatherFacts(args):
    # Read our input file in key:command format and write data to redis
    # NOTE: we do not exit with a failure when trying to write to redis
    log.info("Attempting to read from input file %s", args.input_file)
    try:
        inputFile = open(args.input_file, 'r')
    except IOError:
        log.error("ERROR: Failed to read input file %s. Exiting", args.input_file)
        exit(1)

    r = redis.Redis(host=args.redis_ip, port=args.redis_port)

    for line in inputFile.readlines():
        chunks = line.strip().split(':')
        log.debug("Attempting %s: %s", chunks[0], ' '.join(str(x) for x in chunks[1:]))
        
        p = Popen(chunks[1:], stdout=PIPE, stderr=PIPE, shell=True)
        output, errors = p.communicate()
        try:
            assert p.returncode == 0
            gotValue = True
        except Exception:
            log.error("Failed to gather data from command \'%s\'", ' '.join(str(x) for x in chunks[1:]))
            log.error("%s",errors.decode())
            gotValue = False

        # Only attempt to write to redis if our command returned 0
        if gotValue is True:
            value = output.decode().strip()
            log.info("%s: %s", chunks[0], value)

            log.debug("Logging to Redis")
            try:
                r.set(chunks[0],value)
            except Exception as e:
                log.error("ERROR: Failed to write to Redis server %s on port %s", args.redis_ip, args.redis_port)
                log.error(e)

    inputFile.close()

if __name__ == '__main__':
    main(sys.argv[1:])
