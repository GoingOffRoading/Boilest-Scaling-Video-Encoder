## Manager ToDo List

- [ ] Interactive UI
- [x] Add a status field to the queue DB
- [ ] Update flask_post_queue to check for the status flag, instead of checking for datetime columns
- [ ] Maybe add another queue for largest impact.  I.E. Largest file, x264, etc.  Maybe a field like 'encode priorit' or something.  
- [ ] Update flast_get_largest_queue to use the same datetime logic as queed/completed for datetime stamp
- [x] Logs were being printed for files being added to queue that were correctly being skipped
- [ ] Fix the queue logic to not use the datetime stamps