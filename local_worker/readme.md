## Worker ToDo List

- [ ] The file move workflow assumes that the file move will be susesful.  It really should be rename source file, and only delete if the move is sucsesful.  I may not get to that in this itteration.  After Edit: Validate video output probably shouldn't start until the encoded file is moved.  After after edit: That might be too heavy on the NAS bandwidth...  Need to rethink this a bit
- [ ] Add a preflight check for video exists
- [ ] Improve logging messages
- [ ] Debate if queueing with nothing in queue after so many instances should trigger a scan
- [ ] Debate if worker should loop through attempts to send results until a 200