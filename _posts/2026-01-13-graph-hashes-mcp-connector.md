---
layout: post
title: "Graph Hashes connector: File integrity for Power Automate and Copilot Studio"
date: 2026-01-13 09:00:00 -0500
categories: [Power Platform]
tags: [MCP, Custom Connectors, Microsoft Graph, File Integrity, Hash Algorithms, Copilot Studio, Power Automate]
---

Ever wondered if that file you uploaded to OneDrive arrived intact? Or need to detect when critical documents change? The Graph Hashes connector brings file hash computation and verification to Power Automate and Copilot Studio, letting you verify file integrity, detect changes, and identify duplicates using Microsoft's native hash algorithms.

## What makes this connector unique?

Microsoft Graph automatically computes hashes for files stored in OneDrive and SharePoint, but accessing and using these hashes requires custom code. This connector bridges that gap, making hash operations available as simple Power Automate actions and natural language queries in Copilot Studio.

**Key capabilities:**
- **Compute file hashes** using QuickXorHash, SHA1, or CRC32 algorithms
- **Verify file integrity** by comparing computed hashes against Graph-stored values
- **Detect file changes** by tracking hash values over time
- **Find duplicate files** by comparing hash values across multiple files
- **Ask questions naturally** like "Has the Q4 report changed since last week?"

## Hash algorithms explained

### QuickXorHash
This is Microsoft's standard hash for OneDrive and SharePoint files. It's a 160-bit hash optimized for cloud storage, and it's **guaranteed to be available** for all OneDrive for Business and personal OneDrive files. When verifying file integrity in Microsoft's cloud, QuickXorHash is your reliable choice.

Format: Base64 (e.g., `UNq5WtvvgNlOzU+QP4z/QSS/VmQ=`)

### SHA1
A standard cryptographic hash that's familiar to most developers. While Microsoft Graph may compute SHA1 for some files, it's not guaranteed to be available for all files.

Format: Hexadecimal (e.g., `50dab95b1bef80d94ecd4f903f8cff4124bf5664`)

### CRC32
A fast checksum algorithm useful for quick integrity checks. Like SHA1, availability through Graph API varies by file.

Format: Hexadecimal, 8 characters (e.g., `a1b2c3d4`)

## Power Automate scenarios

### Verify upload integrity
```
1. When a file is created → Get file content
2. Compute QuickXorHash → Input: File Content
3. Delay 5 seconds (allow OneDrive to process)
4. Get File Hashes → Input: Drive ID, Item ID
5. If computed hash equals Graph hash → Success
```

This flow confirms your uploaded file matches what OneDrive stored, catching corruption during upload.

### Detect file changes
```
1. Recurrence - Daily at 9 AM
2. Get File Hashes → Input: Critical file ID
3. Get previous hash from variable
4. Compare Hashes → Input: Current vs Previous
5. If no match → Send alert email
6. Update variable with new hash
```

Monitor critical documents like contracts, compliance files, or financial reports for unauthorized changes.

### Find duplicate files
```
1. Get files from folder
2. Apply to each file:
   - Compute QuickXorHash
   - Append hash + filename to array
3. Compare all hashes
4. If duplicate found → Move to archive
```

Clean up storage by identifying identical files, even if they have different names or locations.

## Copilot Studio integration

The connector includes four MCP tools that enable natural language file verification:

| Tool | Purpose | Example Query |
|------|---------|---------------|
| `compute_file_hash` | Calculate hash for a file | "Calculate the QuickXorHash for this file" |
| `get_graph_file_hashes` | Retrieve hashes from Graph | "What are the hashes for the Q4 report?" |
| `verify_file_integrity` | Compare computed vs stored hash | "Verify this file hasn't been corrupted" |
| `compare_hashes` | Compare two hash values | "Do these hashes match?" |

**Conversational examples:**

**User:** "Has the Q4 financial report changed since last week?"  
**Agent:** Retrieves current file hash, compares to stored value, confirms no changes detected.

**User:** "Verify the uploaded contract matches the original"  
**Agent:** Computes hash, compares to expected value, confirms integrity.

**User:** "Are these two invoices identical?"  
**Agent:** Computes hashes for both files, confirms they're duplicates.

## Available operations

The connector provides seven operations for different verification scenarios:

**Hash Computation:**
- Compute QuickXorHash
- Compute SHA1 Hash
- Compute CRC32 Hash

**Verification:**
- Compare Hashes (two hash values)
- Verify File Integrity (computed vs Graph stored)

**Graph Integration:**
- Get File Hashes (retrieve stored hashes)
- Download File Content (for hash computation)

Each operation returns detailed results including the hash value, file size, and verification status.

## Technical implementation

The connector implements Microsoft's official QuickXorHash algorithm as documented in their developer resources. It's a circular-shifting XOR operation with file length that produces a 160-bit hash optimized for large files.

**File size considerations:**
- Power Platform limit: 50 MB (connector execution timeout)
- Graph API downloads: Up to 250 MB
- Recommendation: For files over 10 MB, use direct Graph download within the connector

**Authentication:**
- OAuth 2.0 with Microsoft Entra ID
- Required scopes: `Files.Read` or `Files.Read.All`
- Uses global consent redirect URL

**Optional telemetry:**
The connector can send events to Application Insights for monitoring hash operations, verification results, and performance metrics. Update the connection string in the script to enable.

## Best practices

1. **Use QuickXorHash for OneDrive/SharePoint** - It's guaranteed to be available for all files
2. **Cache hash values** - Store in variables to avoid repeated computation
3. **Add delays after upload** - Give Graph API time to process files and compute hashes
4. **Handle missing hashes gracefully** - SHA1 and CRC32 aren't available for all files
5. **Batch operations** - Use parallel branches when checking multiple files

## Error handling

Common scenarios and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| Invalid base64 | File content not properly encoded | Ensure file is base64-encoded |
| Graph API error: 404 | File not found | Verify driveId and itemId |
| Graph API error: 401 | Insufficient permissions | Grant Files.Read.All scope |
| Hash not available | Graph hasn't computed hash yet | Retry after delay |

## Limitations

- **Read-only**: Cannot write hashes to Graph (service computes them automatically)
- **No streaming**: Files load entirely into memory
- **Timeout constraints**: Very large files may hit execution limits
- **Hash availability**: SHA1 and CRC32 not guaranteed for all files

## Use cases at a glance

**File integrity monitoring**: Verify critical files haven't been corrupted or tampered with  
**Upload verification**: Confirm files uploaded correctly to cloud storage  
**Change detection**: Track when documents are modified  
**Deduplication**: Identify identical files across folders or sites  
**Conversational verification**: Ask natural language questions about file status

## Get started

The Graph Hashes connector is available in the [SharingIsCaring repository](https://github.com/troystaylor/SharingIsCaring/tree/main/Graph%20Hashes) with complete source code, setup instructions, and example flows.

**What you'll need:**
- Microsoft Graph permissions (Files.Read or Files.Read.All)
- Power Automate or Copilot Studio license
- Files stored in OneDrive or SharePoint

Whether you're building automated integrity checks, file monitoring systems, or conversational file management agents, the Graph Hashes connector makes hash operations accessible without writing custom code.

## Resources

- [Microsoft Graph Hashes Resource](https://learn.microsoft.com/graph/api/resources/hashes)
- [QuickXorHash Algorithm Documentation](https://learn.microsoft.com/onedrive/developer/code-snippets/quickxorhash)
- [Graph Hashes Connector Source](https://github.com/troystaylor/SharingIsCaring/tree/main/Graph%20Hashes)

✅ Verify file integrity  
🔍 Detect unauthorized changes  
🚀 Automate file verification  

#PowerPlatform #MCP #FileIntegrity #Microsoft Graph #CustomConnectors #CopilotStudio #PowerAutomate
