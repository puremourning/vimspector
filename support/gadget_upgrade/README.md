# Auto download and checksum

This is useful for binary gadgets with lots of packages (like cpptools)

1. Update ../../python3/vimspector/gadgets.py with the new version/url, but 
   remove the checksums  (set to `''`)
2. run ./download_and_checksum_gadget.py gadget_name to download the packages
   for each platform/version and print the checksums
3. update ../../python3/vimspector/gadgets.py with the checksums
2. run ./download_and_checksum_gadget.py gadget_name again to verify (should
   all match and not re-download)

# Manually downloading and updating shipped gadgets

Download the gadget files manually from their official source into this dir.
Run `./checksum.py <list of files>` to get the checksums.

Update ../../python3/vimspector/gadgets.py with the new version and the
checksums.

