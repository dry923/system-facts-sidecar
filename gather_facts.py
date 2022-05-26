#!/usr/bin/env python3

import socket
import sys
import argparse
import redis
import logging
import time
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

    waitForInput(args)

def waitForInput(args):
    # Connect to redis and wait for the "get" value to appear in the system-facts-sidecar key
    # Once it appears, execute the gatherFacts function and then set the value in our system-facts-sidecar key to done
    # NOTE: We ignore all other values other than "get" in the system-facts-sidecar key
    r = redis.Redis(host=args.redis_ip, port=args.redis_port)
    log.info("Starting waiting for input loop")
    while True:
        redisOut = None
        try:
            redisOut = r.get('system-facts-sidecar')
            # If we get a key that doesn't exist or  unknown key value, ignore it
            if redisOut == None or redisOut.decode() != "get":
                time.sleep(2)
                continue
            log.info("Recieved get command. Starting to gather facts.")
            gatherFacts(args,r)
            log.info("Setting system-facts-sidecar redis key to done")
            r.set('system-facts-sidecar','done')
        except Exception:
            continue
        time.sleep(2)

def gatherFacts(args, r):
    # Read our input file in key:command format and write data to redis
    # NOTE: we do not exit with a failure when trying to write to redis
    log.info("Attempting to read from input file %s", args.input_file)
    try:
        inputFile = open(args.input_file, 'r')
    except IOError:
        log.error("ERROR: Failed to read input file %s. Exiting", args.input_file)
        exit(1)


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
