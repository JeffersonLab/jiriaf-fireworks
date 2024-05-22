package main

import (
    "fmt"
    "net"
    "net/http"
    "os"
    "os/signal"
    "strconv"
    "syscall"
    "github.com/gorilla/mux"
    "time"
    "github.com/google/goexpect"
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

func runCommand(w http.ResponseWriter, r *http.Request) {
    command := r.FormValue("command")

    // Create a new Expect subprocess
    e, _, err := goexpect.Spawn(command, -1)
    if err != nil {
        fmt.Fprintf(w, `{"error": "%s"}`, err)
        return
    }

    // Wait for the "Password + OTP" prompt
    _, _, err = e.Expect("Password + OTP", 5*time.Second) // adjust the timeout value as needed
    if err != nil {
        // If the prompt is not detected within the timeout, the command completed successfully
        fmt.Fprintf(w, `{"status": "Command completed"}`)
    } else {
        // If the prompt is detected, terminate the process
        if err := e.Close(); err != nil {
            fmt.Fprintf(w, `{"error": "Failed to kill process: %s"}`, err)
        } else {
            fmt.Fprintf(w, `{"error": "Command asked for a password, check your connection"}`)
        }
    }
}

func main() {
    r := mux.NewRouter()
    r.HandleFunc("/get_port/{ip}/{start:[0-9]+}/{end:[0-9]+}", getAvailablePort).Methods("GET")
    r.HandleFunc("/run", runCommand).Methods("POST")

    // Create a channel to receive OS signals
    c := make(chan os.Signal, 1)
    // Notify the channel for SIGINT signals
    signal.Notify(c, os.Interrupt, syscall.SIGTERM)

    // Run a goroutine that waits for the SIGINT signal
    go func() {
        <-c
        fmt.Println("\nReceived an interrupt, stopping services...")
        os.Exit(0)
    }()

    http.ListenAndServe(":8888", r)
}