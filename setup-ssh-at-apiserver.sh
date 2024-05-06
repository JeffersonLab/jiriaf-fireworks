#!/bin/bash
# run this on login04

# export APISERVER_PORT="35679"

# ssh -NfL $APISERVER_PORT:localhost:$APISERVER_PORT jiriaf2301


# run this on jiriaf2301 to login04 at nersc
export APISERVER_PORT="35679"
ssh -i ~/.ssh/nersc -J perlmutter -NfR $APISERVER_PORT:localhost:$APISERVER_PORT jlabtsai@128.55.64.13

# setup mongodb
ssh -i ~/.ssh/nersc -J perlmutter -NfR 27017:localhost:27017 jlabtsai@128.55.64.13


for i in $(seq 1 30)
do
    i_padded=$(printf "%02d" $i)
    echo "100""$i_padded"
    ssh -i ~/.ssh/nersc -J perlmutter -NfL *:100$i_padded:localhost:100$i_padded jlabtsai@128.55.64.13
    echo "200""$i_padded"
    ssh -i ~/.ssh/nersc -J perlmutter -NfL 200$i_padded:localhost:200$i_padded jlabtsai@128.55.64.13
    echo "300""$i_padded"
    ssh -i ~/.ssh/nersc -J perlmutter -NfL 300$i_padded:localhost:300$i_padded jlabtsai@128.55.64.13
    echo "400""$i_padded"
    ssh -i ~/.ssh/nersc -J perlmutter -NfL 400$i_padded:localhost:400$i_padded jlabtsai@128.55.64.13
done

wait