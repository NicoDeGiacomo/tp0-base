#!/bin/bash

SERVER_NAME="server"
SERVER_PORT=12345
NETWORK_NAME="tp0_testing_net"
MESSAGE="ping"

usage() {
    echo "Usage: $0 [-s <name>] [-p <port>] [-n <network>] [-m <message>]"
    echo "Options:"
    echo "  -s, --server   <name>     Server container name (default: server)"
    echo "  -p, --port     <port>     Server port (default: 12345)"
    echo "  -n, --network  <network>  Docker network name (default: tp0_testing_net)"
    echo "  -m, --message  <message>  Message to send to the server (default: ping)"
    echo "  -h, --help                Show this help message and exit"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -s|--server)
            SERVER_NAME="$2"
            shift 2
            ;;
        -p|--port)
            SERVER_PORT="$2"
            shift 2
            ;;
        -n|--network)
            NETWORK_NAME="$2"
            shift 2
            ;;
        -m|--message)
            MESSAGE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            shift
            ;;
    esac
done

RESPONSE=$(docker run --rm --network="$NETWORK_NAME" busybox sh -c "echo '$MESSAGE' | nc $SERVER_NAME $SERVER_PORT")

if [ "$RESPONSE" = "$MESSAGE" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi
