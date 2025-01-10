#!/usr/bin/expect -f

# ORNL account configuration
ORNL_ACCOUNT=jlabtsai

# Check if port, is_reversed flag, and encoded password were provided
if {[llength $argv] < 3} {
    puts "Usage: $argv0 <port> <is_reversed> <base64_encoded_password>"
    exit 1
}

# Set the port, is_reversed, and base64_encoded_password from the command-line arguments
set port [lindex $argv 0]
set is_reversed [lindex $argv 1]
set base64_encoded_password [lindex $argv 2]

# Decode the base64 encoded password
set password [exec echo $base64_encoded_password | base64 --decode]

# Set timeout
set timeout -1

# Determine the SSH command arguments based on the is_reversed variable
if {$is_reversed eq "false"} {
    set first_hop_cmd "ssh -o StrictHostKeyChecking=no -L *:$port:localhost:$port $ORNL_ACCOUNT@flux.op.ccs.ornl.gov"
    set second_hop_cmd "ssh -o StrictHostKeyChecking=no -L *:$port:localhost:$port $ORNL_ACCOUNT@128.219.141.17"
} else {
    set first_hop_cmd "ssh -o StrictHostKeyChecking=no -R $port:localhost:$port $ORNL_ACCOUNT@flux.op.ccs.ornl.gov"
    set second_hop_cmd "ssh -o StrictHostKeyChecking=no -R $port:localhost:$port $ORNL_ACCOUNT@128.219.141.17"
}

# First hop to ornl-login with port forwarding
spawn bash -c "$first_hop_cmd"
expect {
    "assword:" {
        send "$password\r"
    }
    timeout {
        puts "Connection to ornl-login timed out"
        exit 1
    }
    eof {
        puts "Connection to ornl-login failed"
        exit 1
    }
}

# Wait for the prompt after login
expect {
    -re "(%|#|\\$) $" {
        # Short delay to ensure the system is ready
        sleep 1
    }
    timeout {
        puts "Did not get shell prompt on ornl-login"
        exit 1
    }
}

# Second hop to ornl-worker with port forwarding
send "$second_hop_cmd\r"
expect {
    "assword:" {
        send "$password\r"
    }
    timeout {
        puts "Connection to ornl-worker timed out"
        exit 1
    }
    eof {
        puts "Connection to ornl-worker failed"
        exit 1
    }
}

# Wait for the prompt after the second login
expect {
    -re "(%|#|\\$) $" {
        # Tunnel is established, keep the connection alive
        puts "Tunnel established successfully"
        send "echo 'Keeping connection alive...'\r"
        expect {
            "Keeping connection alive..." {
                # Enter an infinite loop to keep the script running
                while {1} {
                    # Send a harmless command every 60 seconds to keep the connection active
                    sleep 60
                    send "echo 'Still alive'\r"
                    expect {
                        "Still alive" {}
                        timeout {
                            puts "Connection lost"
                            exit 1
                        }
                    }
                }
            }
        }
    }
    timeout {
        puts "Did not get shell prompt on ornl-worker"
        exit 1
    }
}