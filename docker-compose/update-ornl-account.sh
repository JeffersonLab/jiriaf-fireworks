#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 <new_account_name>"
    echo "Example: $0 newuser"
    exit 1
fi

NEW_ACCOUNT=$1

# Update the ORNL account in the container
docker exec jrm-fw-lpad bash -c "
    # Create or update the account file
    echo '${NEW_ACCOUNT}' > /root/.ornl_account
    
    echo 'Updated ORNL account to: ${NEW_ACCOUNT}'
    echo 'Account stored in: /root/.ornl_account'
" 