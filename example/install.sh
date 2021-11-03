#!/usr/bin/bash

usage() { echo "Usage: $0 [-p local|eddie|archer2]" 1>&2; exit 1; }

platform="local"
while getopts ":p:" o; do
    case "${o}" in
        p)
            platform=${OPTARG}
            if [ "$platform" != "local" \
		 -a "$platform" != "eddie" \
		 -a "$platform" != "archer2" ]; then
		usage
	    fi
            ;;
	*)
	    usage
	    ;;
    esac
done

for opt in nlopt dfols; do
    flow=optimise-$opt-$platform.cylc
    if [ -f $flow ]; then
        echo $flow
	target=~/cylc-src/optclim-$opt-$platform
	mkdir -p $target
	cp $flow $target/flow.cylc
	cp example-$opt.cfg $target
    fi
done

