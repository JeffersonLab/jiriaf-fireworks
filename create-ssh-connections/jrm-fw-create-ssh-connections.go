package main

import (
    "fmt"
    "net"
    "net/http"
    "os"
    "os/exec"
    "strconv"
    "github.com/gorilla/mux"
    "context"
    "time"
    "bufio"
    "strings"
    "golang.org/x/crypto/ssh"
)

func getAvailablePort(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    ip := vars["ip"]
    start, _ := strconv.Atoi(vars["start"])
    end, _ := strconv.Atoi(vars["end"])

    for port := start; port <= end; port++ {
        address := fmt.Sprintf("%s:%d", ip, port)
        listener, err := net.Listen("tcp", address)
        if err == nil {
            listener.Close()
            fmt.Fprintf(w, `{"port": %d}`, port)
            return
        }
    }
    fmt.Fprintf(w, `{"error": "No available port found"}`)
}

var restartServer bool

func runCommand(w http.ResponseWriter, r *http.Request) {
    command := r.FormValue("command")

    // Create a new context with a timeout
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second) // adjust the timeout value as needed
    defer cancel()

    // Create the command with the context
    cmd := exec.CommandContext(ctx, "bash", "-c", command)

    // Get the stderr pipe
    stderr, err := cmd.StderrPipe()
    if err != nil {
        fmt.Fprintf(w, `{"error": "%s"}`, err)
        return
    }

    // Start the command and don't wait for it to finish
    if err := cmd.Start(); err != nil {
        fmt.Fprintf(w, `{"error": "%s"}`, err)
        return
    }

    // Create a channel to wait for the command to finish
    done := make(chan error, 1)
    go func() {
        done <- cmd.Wait()
    }()

    // Read from the stderr pipe in a separate goroutine
    go func() {
        reader := bufio.NewReader(stderr)
        for {
            line, err := reader.ReadString('\n')
            if err != nil || strings.Contains(line, "(jlabtsai@perlmutter.nersc.gov) Password + OTP: ") {
                // If the specific output is detected or an error occurs, send a SIGINT signal to the command's process
                cmd.Process.Signal(os.Interrupt)
                restartServer = true
                return
            }
            // Print the output
            fmt.Println(line)
        }
    }()

    // Use a select statement to wait for the command to finish or for the context to timeout
    select {
    case <-ctx.Done():
        if ctx.Err() == context.DeadlineExceeded {
            fmt.Fprintf(w, `{"error": "Command timed out, check your connection"}`)
        }
        if err := cmd.Process.Kill(); err != nil {
            fmt.Fprintf(w, `{"error": "Failed to kill process: %s"}`, err)
        }
    case err := <-done:
        if err != nil {
            fmt.Fprintf(w, `{"error": "%s"}`, err)
        } else {
            fmt.Fprintf(w, `{"status": "Command completed"}`)
        }
    }
}

func main() {
    // SSH client config
    config := &ssh.ClientConfig{
		User: "username",
        Auth: []ssh.AuthMethod{
            ssh.Password("password"),
        },
        HostKeyCallback: ssh.InsecureIgnoreHostKey(),
    }

    // Connect to the remote server
    client, err := ssh.Dial("tcp", "remote-server:22", config)
    if err != nil {
        panic(err)
    }

    // Create a session
    session, err := client.NewSession()
    if err != nil {
        panic(err)
    }
    defer session.Close()

    // Redirect session's stderr to a pipe
    stderr, _ := session.StderrPipe()

    // Start the command
    if err := session.Start("command"); err != nil {
        panic(err)
    }

    // Read from the stderr pipe
    reader := bufio.NewReader(stderr)
    for {
        line, err := reader.ReadString('\n')
        if err != nil || strings.Contains(line, "(jlabtsai@perlmutter.nersc.gov) Password + OTP: ") {
            // If the specific output is detected or an error occurs, send a SIGINT signal to the command's process
            session.Signal(ssh.SIGINT)
            break
        }
        // Print the output
        fmt.Println(line)
    }

    // Wait for the command to finish
    session.Wait()
}