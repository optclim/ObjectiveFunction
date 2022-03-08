OPTIMISER=dfols
if [ -n "$1" ]; then
    if [ "$1" != 'dfols' -a "$1" != 'nlopt' -a "$1" != 'simobs' ]; then
	echo "argument should be one of dfols, nlopt or simobs" >&2
	exit 1
    fi
    OPTIMISER=$1
fi

echo "using optimiser $OPTIMISER"
optscript=optclim2-dfols
optcfg=example-dfols.cfg
if [ $OPTIMISER = 'nlopt' ]; then
    optscript=optclim2-nlopt
    optcfg=example-nlopt.cfg
elif [ $OPTIMISER = 'simobs' ]; then
    optcfg=example-simobs.cfg
fi
export CYLC_WORKFLOW_WORK_DIR=/tmp/test-$OPTIMISER
rm -rf $CYLC_WORKFLOW_WORK_DIR

if [ $OPTIMISER != 'simobs' ]; then
    # generate synthetic data
    optclim2-example-model $optcfg -g
fi

while /bin/true
do
    $optscript $optcfg
    res=$?
    if [ $res -eq 0 ]; then
        # the optimiser has finised
        break
    fi
    while [ $res -eq 1 ]
    do
	# generate new forward parameters to be tested
	$optscript $optcfg
	res=$?
    done
    while optclim2-example-model $optcfg
    do
	echo 'fwd'
    done
done

echo "parameters used"
if [ $OPTIMISER = 'simobs' ]; then
    echo 4 3 2
else
    cat $CYLC_WORKFLOW_WORK_DIR/parameters.data
fi
