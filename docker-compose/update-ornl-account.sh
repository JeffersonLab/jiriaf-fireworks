#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 <new_account_name>"
    echo "Example: $0 newuser"
    exit 1
fi

NEW_ACCOUNT=$1

# Update the account name in the build-ssh-ornl.sh file inside the container
docker exec jrm-fw-lpad bash -c "
    sed -i 's/jlabtsai@flux/${NEW_ACCOUNT}@flux/g' /root/build-ssh-ornl.sh
    sed -i 's/jlabtsai@128/${NEW_ACCOUNT}@128/g' /root/build-ssh-ornl.sh
    echo 'Updated ORNL account to: ${NEW_ACCOUNT}'
    echo 'Changes made to: /root/build-ssh-ornl.sh'
" 