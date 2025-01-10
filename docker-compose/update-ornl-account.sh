#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 <new_account_name>"
    echo "Example: $0 newuser"
    exit 1
fi

NEW_ACCOUNT=$1

# Update the account name in the build-ssh-ornl.sh file inside the container
docker exec jrm-fw-lpad bash -c "
    # First, check if the pattern exists
    if ! grep -q 'ORNL_ACCOUNT=' /root/build-ssh-ornl.sh; then
        # Add the variable definition at the start of the file (after shebang)
        sed -i '2i\\n# ORNL account configuration\nORNL_ACCOUNT=jlabtsai' /root/build-ssh-ornl.sh
        # Replace hardcoded usernames with the variable
        sed -i 's/jlabtsai@flux/\$ORNL_ACCOUNT@flux/g' /root/build-ssh-ornl.sh
        sed -i 's/jlabtsai@128/\$ORNL_ACCOUNT@128/g' /root/build-ssh-ornl.sh
    fi
    
    # Update the account variable
    sed -i \"s/ORNL_ACCOUNT=.*/ORNL_ACCOUNT=${NEW_ACCOUNT}/\" /root/build-ssh-ornl.sh
    
    echo 'Updated ORNL account to: ${NEW_ACCOUNT}'
    echo 'Changes made to: /root/build-ssh-ornl.sh'
" 