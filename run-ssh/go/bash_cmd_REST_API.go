package main

import (
    "fmt"
    "net"
    "net/http"
    "os/exec"
    "strconv"
    "strings"

    "github.com/gorilla/mux"
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
    cmd := exec.Command("sh", "-c", command)
    output, err := cmd.CombinedOutput()
    if err != nil {
        fmt.Fprintf(w, `{"error": "%s"}`, err)
        return
    }
    fmt.Fprintf(w, `{"output": "%s"}`, strings.TrimSuffix(string(output), "\n"))
}

func main() {
    r := mux.NewRouter()
    r.HandleFunc("/get_port/{ip}/{start:[0-9]+}/{end:[0-9]+}", getAvailablePort).Methods("GET")
    r.HandleFunc("/run", runCommand).Methods("POST")
    http.ListenAndServe(":8888", r)
}