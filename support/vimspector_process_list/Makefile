vimspector_process_list: vimspector_process_list.go go.mod
	go build

.PHONY: clean
clean:
	rm -f vimspector_process_list

.PHONY: install
install: vimspector_process_list
	go install
