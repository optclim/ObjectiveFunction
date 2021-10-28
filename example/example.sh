export CYLC_WORKFLOW_WORK_DIR=/tmp/test
rm -rf $CYLC_WORKFLOW_WORK_DIR
# generate synthetic data
optclim2-example-model example/example.cfg -g

while /bin/true
do
    res=$(optclim2 example/example.cfg)
    if [ $res = "done" ]; then
	break
    fi
    while [ $res = "new" ]
    do
	res=$(optclim2 example/example.cfg)
    done
    while optclim2-example-model example/example.cfg
    do
	echo 'fwd'
    done
done
