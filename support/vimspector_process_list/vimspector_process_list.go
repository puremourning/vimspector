// Vimspector process lister - a simple process lister
// Copyright 2023 Ben Jackson (puremourning@gmail.com)
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// 	http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package main

import (
	"fmt"
	"os"
	"os/user"
	"regexp"
	"text/tabwriter"
	"time"

	"github.com/shirou/gopsutil/v3/process"
)

const (
	DateTime = "2006-01-02 15:04:05"
)

func main() {
	pattern := ".*"
	pattern_supplied := false
	if len(os.Args) > 2 {
		fmt.Println("Usage: process_list <regex>")
		return
	} else if len(os.Args) == 2 {
		pattern = os.Args[1]
		pattern_supplied = true
	}

	processes, _ := process.Processes()
	cur_user, _ := user.Current()
	w := tabwriter.NewWriter(os.Stdout, 0, 2, 1, ' ', 0)

	if pattern_supplied {
		fmt.Fprintf(w, "%v\t%v\t%v\t%v\n", "PID", "PPID", "CWD", "START")
	} else {
		fmt.Fprintf(w, "%v\t%v\t%v\t%v\t%v\n", "PID", "PPID", "NAME", "CMDLINE", "START")
	}

	for _, p := range processes {
		name, _ := p.Name()
		match, _ := regexp.MatchString(pattern, name)
		if !match {
			continue
		}

		if len(name) > 20 {
			name = name[:20]
		}

		cwd, _ := p.Cwd()
		pid := p.Pid
		ppid, _ := p.Ppid()
		status, _ := p.Status()
		cmdline, _ := p.Cmdline()
		if len(cmdline) > 40 {
			cmdline = cmdline[:40]
		}
		is_running, _ := p.IsRunning()
		utime, _ := p.CreateTime()
		dtime := time.UnixMilli(utime).Format(DateTime)

		username, _ := p.Username()

		parent, _ := process.NewProcess(ppid)
		pname, _ := parent.Name()

		if username == cur_user.Username && is_running && status[0] != "zombie" {
			if pattern_supplied {
				fmt.Fprintf(w, "%v\t%v (%v)\t%v\t%v\n", pid, ppid, pname, cwd, dtime)
			} else {
				fmt.Fprintf(w, "%v (%v)\t%v (%v)\t%v\t%v\n", pid, name, ppid, pname, cmdline, dtime)
			}
		}
	}
	w.Flush()
}
