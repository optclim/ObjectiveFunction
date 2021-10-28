OPTIMISER=dfols
if [ -n "$1" ]; then
    if [ "$1" != 'dfols' -a "$1" != 'nlopt' ]; then
	echo "argument should be either dfols or nlopt" >&2
	exit 1
    fi
    OPTIMISER=$1
fi

echo "using optimiser $OPTIMISER"
optscript=optclim2-dfols
optcfg=example-dfols.cfg
if [ $OPTIMISER = 'nlopt' ]; then
    optscript=optclim2
    optcfg=example.cfg
fi
export CYLC_WORKFLOW_WORK_DIR=/tmp/test-$OPTIMISER
rm -rf $CYLC_WORKFLOW_WORK_DIR
# generate synthetic data
optclim2-example-model $optcfg -g

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
cat $CYLC_WORKFLOW_WORK_DIR/parameters.data
