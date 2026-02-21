## Worker ToDo List

- [x] The file move workflow assumes that the file move will be susesful.  It really should be rename source file, and only delete if the move is sucsesful.  I may not get to that in this itteration.  After Edit: Validate video output probably shouldn't start until the encoded file is moved.  After after edit: That might be too heavy on the NAS bandwidth...  Need to rethink this a bit
- [x] Add a preflight check for video exists
- [x] Add a postflight check for video exists
- [x] Improve logging messages.  Including posting messages when steps start, not just end.  New line breaks.
- [x] Debate if queueing with nothing in queue after so many instances should trigger a scan
- [x] Debate if worker should loop through attempts to send results until a 200
- [x] Add additional messaging on hash mismatch
- [x] Refactor both pipelines so that /boilemdia/ isn't used in the directory path... I.E. Appear more like the actual URL
- [x] Refactor logging so that line breaks more intuiity break up the lines in the logs
- [x] Figure out why in isloated cases, the original file does not get replaced
- [x] Rework the pre/post check list to include determining if the file exists, add appropraite messaging
- [x] Refactor how media file integrity is done 
- [x] Video validation, need to revisit how validation is done to let in some videos that would otherwise be fixed with encoding
- [ ] Do a little cleanup and formatting of local_worker_functions
- [x] On status messaging between phases, mention the directory path
- [x] Resolve an issue where a postflight validation check leaves an ophaned file
- [x] Add a random delay to the next task piece
- [x] Eyeball how we could do the wait for next task differently
- [x] Add a retry on files failing to write







