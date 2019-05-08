# Simple-P2P-File-Sharing-System

This is a simple P2P file sharing application that synchronizes files among peers.

1. Only consider the files within the same folder where the peer or synchronizer runs (no subfolders).
2. Changes after peers start are not considered, such as file deletion, modification, and addition. In other words, the (initial) message that contains local file information is sent only once.
3. If multiple files from different peers have the same file name, the one with the latest modified timestamp will be kept by the tracker.
4. Only one TCP connection is needed between a peer and a tracker.
