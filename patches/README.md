# Patches Directory

This directory contains patches applied to fix issues found during Step 4 execution.

## Applied Patches

### netmhcpan_path_fix.patch
- **Description**: Fixes the NMHOME path configuration in the NetMHCpan wrapper script
- **File Modified**: `repo/netMHCpan-4.2/netMHCpan`
- **Issue**: The original script had hardcoded path `/tools/src/netMHCpan-4.2` which doesn't exist in our repo structure
- **Fix**: Updated NMHOME to point to the actual location of NetMHCpan in our repo directory
- **Impact**: Critical fix - without this patch, no use cases would work as the NetMHCpan binary couldn't be found
- **Backup**: Original file saved as `repo/netMHCpan-4.2/netMHCpan.bak`

## How to Apply Patches

If you need to reapply these patches:

```bash
# For netMHCpan path fix:
cd /path/to/netmhcpan_mcp
patch -p0 < patches/netmhcpan_path_fix.patch
```

## Creating New Patches

To create patches for future fixes:

```bash
# Create backup
cp original_file original_file.bak

# Make changes to original_file

# Generate patch
diff -u original_file.bak original_file > patches/fix_description.patch
```