export CYLC_WORKFLOW_WORK_DIR=/tmp/test-dfols
rm -rf $CYLC_WORKFLOW_WORK_DIR
./example/bin/model example/example-dfols.cfg -g

while /bin/true
do
    res=$(optclim2-dfols example/example-dfols.cfg | egrep '^(new|done|waiting)$')
    if [ $res = "done" ]; then
	break
    fi
    while [ $res = "new" ]
    do
	res=$(optclim2-dfols example/example-dfols.cfg | egrep '^(new|done|waiting)$')
    done
    while ./example/bin/model example/example-dfols.cfg
    do
	echo 'fwd'
    done
done
